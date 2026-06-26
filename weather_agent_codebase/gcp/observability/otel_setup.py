"""OpenTelemetry setup for the A2A weather + host agents.

Implements PDF Section 6 (Observability & Logging API Dashboards).

The Gemini Enterprise Agent Platform observability tab (Overview / Evaluation /
Models / Tools / Usage / Logs) is populated by spans + metrics that follow the
OpenTelemetry GenAI Semantic Conventions:

    https://opentelemetry.io/docs/specs/semconv/gen-ai/

This module:

  1. Installs an OTLP / Cloud Trace exporter for spans (-> Cloud Trace).
  2. Installs an OTLP / Cloud Monitoring exporter for metrics (-> Cloud Metrics).
  3. Sets the canonical Resource attributes Gemini Enterprise expects so the
     topology map can render agent + tool dependencies.
  4. Returns a tracer + meter the agent code can use to emit
     `gen_ai.*` spans / metrics manually for tool calls and LLM invocations.

Call `configure_otel(...)` once at process start (deploy_agent_engine.py does
this) before the ADK Runner is built.
"""

from __future__ import annotations

import os
from typing import Optional

# Public handles (set by configure_otel)
_tracer = None
_meter = None
_configured = False


def configure_otel(
    *,
    service_name: str,
    service_version: str = "1.0.0",
    project_id: Optional[str] = None,
    deployment_environment: str = "production",
):
    """Wire up OTel exporters so signals reach Cloud Trace + Cloud Monitoring.

    Safe to call multiple times - subsequent calls become no-ops.
    """
    global _tracer, _meter, _configured
    if _configured:
        return _tracer, _meter

    project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set or project_id passed in.")

    # Imports kept inside the function so the rest of the codebase still runs
    # if the OTel deps haven't been installed yet.
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

    # GenAI semantic conventions live under semconv-ai; resource attrs are
    # standard OTel resource attributes that GCP observability looks for.
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "service.namespace": "gemini-enterprise-agents",
            "deployment.environment": deployment_environment,
            "cloud.provider": "gcp",
            "cloud.platform": "vertex_ai_reasoning_engine",
            "cloud.account.id": project_id,
            # Marker that lets Gemini Enterprise Observability cluster signals
            # under the right agent in the multi-agent topology map.
            "gen_ai.agent.name": service_name,
        }
    )

    # ----- Trace pipeline (-> Cloud Trace) -----------------------------------
    try:
        from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

        span_exporter = CloudTraceSpanExporter(project_id=project_id)
    except Exception:
        # Fallback to OTLP gRPC if cloud-trace exporter is missing.
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        span_exporter = OTLPSpanExporter()

    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # ----- Metric pipeline (-> Cloud Monitoring) -----------------------------
    try:
        from opentelemetry.exporter.cloud_monitoring import (
            CloudMonitoringMetricsExporter,
        )

        metric_exporter = CloudMonitoringMetricsExporter(project_id=project_id)
    except Exception:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )

        metric_exporter = OTLPMetricExporter()

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(metric_exporter)],
    )
    metrics.set_meter_provider(meter_provider)

    # ----- Auto-instrument requests so A2A HTTP fan-out is traced -----------
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        RequestsInstrumentor().instrument()
    except Exception:
        pass

    _tracer = trace.get_tracer(service_name, service_version)
    _meter = metrics.get_meter(service_name, service_version)
    _configured = True
    return _tracer, _meter


def get_tracer():
    from opentelemetry import trace
    return trace.get_tracer('weather-agent')


def get_meter():
    if not _configured:
        raise RuntimeError("configure_otel() must be called before get_meter().")
    return _meter


# ---------------------------------------------------------------------------
# Convenience: standard GenAI semconv span helpers.
# ---------------------------------------------------------------------------

def start_llm_span(model: str, system: str = "vertex_ai"):
    """Context manager for an LLM invocation span using GenAI semantic conv."""
    tracer = get_tracer()
    span = tracer.start_as_current_span(f"chat {model}")
    return _LLMSpan(span, model=model, system=system)


def start_tool_span(tool_name: str):
    """Context manager for a tool invocation span using GenAI semantic conv."""
    tracer = get_tracer()
    span = tracer.start_as_current_span(f"execute_tool {tool_name}")
    return _ToolSpan(span, tool_name=tool_name)


class _LLMSpan:
    def __init__(self, cm, model: str, system: str):
        self._cm = cm
        self.model = model
        self.system = system

    def __enter__(self):
        self._span = self._cm.__enter__()
        self._span.set_attribute("gen_ai.system", self.system)
        self._span.set_attribute("gen_ai.request.model", self.model)
        self._span.set_attribute("gen_ai.operation.name", "chat")
        return self._span

    def __exit__(self, *args):
        return self._cm.__exit__(*args)


class _ToolSpan:
    def __init__(self, cm, tool_name: str):
        self._cm = cm
        self.tool_name = tool_name

    def __enter__(self):
        self._span = self._cm.__enter__()
        self._span.set_attribute("gen_ai.operation.name", "execute_tool")
        self._span.set_attribute("gen_ai.tool.name", self.tool_name)
        return self._span

    def __exit__(self, *args):
        return self._cm.__exit__(*args)


