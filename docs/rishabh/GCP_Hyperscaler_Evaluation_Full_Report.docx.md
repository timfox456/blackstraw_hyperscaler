# **GCP Hyperscaler Evaluation Report**

This report mirrors the Hyperscaler Evaluation Pilot spreadsheet structure. Every sub-criterion is represented as Pass, Partial Pass, Blocked by Permissions or Infrastructure, Not Exercised, or Platform Limitation.

## **01.a MCP App Render Visible in Trace**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

MCP infrastructure unavailable. Node.js and public SSE endpoint not available.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **01.b Streaming Visible in Trace**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

GenAI span hierarchy and token metrics visible. No chunk-level streaming or TTFT metrics.

**Trace ID**

c726b93cbb1ef459a762a2ab27cb6774

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **01.c Attachments Visible in Trace**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

stream\_query lacks multimodal support and Cloud Trace avoids binary payload storage.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **01.d Persona Switching Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Persona changes appeared as execute\_tool set\_persona spans with cross-turn context growth.

**Trace ID**

e4fe9b4b3196cf7739ca0437e2e5fa5f

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **02.a Multi-step Prompt Chain Runs End-to-End Against MCPs**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

End-to-end MCP chain validation was not possible due to MCP infrastructure dependencies.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **02.b Each Orchestration Step Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Parallel execution, aggregation, and response generation appeared as distinct spans.

**Trace ID**

08b300d58ad7d89907a98551abbf9f55

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **02.c Each Step Traceable to a Specific Prompt Version**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Custom prompt identifiers were possible but no native prompt-to-trace linkage exists.

**Trace ID**

Custom instrumentation only

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **03.a Supervisor Routing Visible in Trace**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Routing decisions visible but downstream execution failed due to missing IAM permissions.

**Trace ID**

Permission failure traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **03.b Parallel Worker Delegation Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Parallel execute\_tool spans and aggregation events were fully observable.

**Trace ID**

08b300d58ad7d89907a98551abbf9f55

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **03.c Coordination State Visible in Trace**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Session state observable but cross-trace relationships required custom correlation.

**Trace ID**

Session traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **03.d MCP and A2A Interop Visible in Trace**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

MCP infrastructure unavailable for end-to-end validation.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **04.a Short-term Memory Operates Inside Pilot**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Agent recalled earlier information and token growth confirmed context accumulation.

**Trace ID**

7da2763e804cc3b46736f1a6bc476abd and related traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **04.b Long-term Memory Operates Inside Pilot**

**Status**

Not Exercised

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

No persistent memory store was configured.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **04.c Compaction Visible as Discrete Trace Event**

**Status**

Not Exercised

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Compaction workflows were not implemented independently.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **04.d Dreaming Visible as Discrete Trace Event**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

dream\_consolidate appeared as a distinct execute\_tool span with custom metadata.

**Trace ID**

d84a15017ccd4ea3c3a25f2c88825e42

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **04.e Semantic Layer Integrates with Retrieval**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

RAG permissions unavailable and retrieval integration could not be validated.

**Trace ID**

Permission failure traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **05.a MCP Called Inside Ciorana Network Over Private Connectivity**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Private connectivity and MCP infrastructure unavailable.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **05.b Setup Documented**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Deployment and setup procedures were documented but not fully validated end to end.

**Trace ID**

Documentation review

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **05.c No Bespoke Vendor Engineering Required**

**Status**

Fail

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Additional infrastructure and networking engineering were required.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **06.a End-user Identity Reaches MCP Tool Call**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Dependent on MCP and private connectivity infrastructure.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **06.b Identity Propagation Visible in Trace**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Dependent on MCP and identity infrastructure.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **06.c Works in Both Deployment Patterns**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Could not be validated without MCP infrastructure.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C01.a Agent Events Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Invocation, invoke\_agent, call\_llm, and execute\_tool spans were visible.

**Trace ID**

Streaming and orchestration traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C01.b MCP Tool Events Visible in Trace**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

MCP tool execution could not be validated.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C01.c Skill Events Visible in Trace**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Custom workflows appeared as execute\_tool spans but no first-class skill abstraction existed.

**Trace ID**

d84a15017ccd4ea3c3a25f2c88825e42

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C01.d Inputs and Outputs Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Model metadata and execution details were visible in spans.

**Trace ID**

Multiple traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C01.e Errors Visible in Trace**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Permission denied and failed tool invocations surfaced in traces and logs.

**Trace ID**

Permission failure traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C02.a Costs Attributable at Project Level**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Project identifiers and token metrics visible on spans.

**Trace ID**

Invocation IDs from cost evaluation

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C02.b Resources Isolated at Project Level**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Cloud Asset Inventory confirmed project-level isolation.

**Trace ID**

Infrastructure assessment

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C02.c Quotas Visible at Project Level**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Quotas and utilization metrics visible at project level.

**Trace ID**

Infrastructure assessment

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C02.d Usage Reporting Available at Project Level**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Usage metrics and billing configuration visible.

**Trace ID**

Infrastructure assessment

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C03.a Entity IDs and Names Resolved Consistently**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Entity resolution persisted across turns.

**Trace ID**

94782e61831fa9b956e3c6e21d10d65b

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C03.b Disambiguation Decisions Visible**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Clarification decisions visible through tool arguments and context.

**Trace ID**

94782e61831fa9b956e3c6e21d10d65b

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C03.c Ontology Mappings Visible**

**Status**

Not Exercised

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

No ontology layer was configured.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C03.d Retrieval Uses Resolved Entity**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Blocked by RAG permissions.

**Trace ID**

Permission failure traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C04.a Agent Version Identifiable**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Reasoning Engine deployment identifiers were traceable.

**Trace ID**

Representative RE IDs

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C04.b Tool Version Identifiable**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Tool metadata visible but no native tool version attribute exists.

**Trace ID**

Tool execution traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C04.c Prompt Version Identifiable**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Prompt metadata could be manually instrumented only.

**Trace ID**

Custom instrumentation

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C04.d Skill Identifier Visible**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Workflow identifiers visible but no native skill abstraction exists.

**Trace ID**

Workflow traces

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C04.e Policy Applied Visible**

**Status**

Blocked

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Model Armor and Agent Gateway were not configured.

**Trace ID**

No trace generated

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C05.a Promotion Path Exists from Non-PROD to PROD**

**Status**

Partial Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Promotion possible through repeatable deployments and registration updates.

**Trace ID**

Deployment assessments

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C05.b Configuration Is Repeatable**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Deployments were deterministic and reusable.

**Trace ID**

Representative RE IDs

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C05.c Environment Differences Are Controlled**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Environment targeting achieved through configuration and environment variables.

**Trace ID**

Infrastructure assessment

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.

## **C05.d Rollback Path Exists**

**Status**

Pass

**Exercise**

See corresponding pilot exercise and deployment workflow from the evaluation notes.

**Pass Result and Condition**

Previous deployments remained available and could be re-registered.

**Trace ID**

Representative RE IDs

**RE ID**

Included where applicable in deployment-related evaluations.

**Session ID**

Included where applicable in memory-related evaluations.

**Additional Notes**

Validated, blocked, or not exercised based on available permissions, infrastructure, and pilot scope.

**Missing Permissions or Services**

Populate with specific IAM role or service requirement if blocked.

**Pros on GCP**

* Native observability and cloud primitives where applicable.  
* Extensible through custom instrumentation and managed services.

**Cons on GCP**

* Some capabilities require additional infrastructure and engineering.  
* Several advanced capabilities require custom instrumentation or permissions.