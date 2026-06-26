---
name: a2a-multi-agent-orchestration
description: Guides the construction of supervisor-specialist multi-agent execution graphs under Gemini Enterprise Agent Engine.
---
# A2A Multi-Agent Graph Orchestration Skill

This skill documents design patterns for constructing multi-agent networks where a central Coordinator (Supervisor) delegates tasks to specialized leaf agents (Sub-Agents) using structured message routing.

## Topologies & Graph Control
1. **Hub-and-Spoke Pattern**:
   * **Root Coordinator**: Coordinates execution flow, manages user context, and formats output widgets.
   * **Leaf Nodes**: Remote specialist engines deployed to Gemini Enterprise Agent Engine with scoped system prompts and tool access.
2. **State Machine Transitions**:
   * Program state machine checks directly in the Supervisor's prompt template.
   * Restrict access of sub-agents to specific domain tools (e.g. `pricing_opportunities_tool` belongs only to the pricing specialist).
3. **Structured Parameter Passing (A2A)**:
   * Avoid unstructured instruction drift. Pass parameters (e.g. target product cohort) to sub-agents via structured JSON slots.
   * Implement a dynamic `send_message_tool` instead of static registry bindings. This allows:
     * Local mocking (redirecting to mock localhost ports).
     * Injecting runtime headers.

## Best Practices
* **No Amnesia**: Migrate from `InMemoryMemoryService` to `FirestoreMemoryService` in multi-worker cloud deployments to ensure session retention.
* **Lock Step Transitions**: Instruct the Supervisor to yield execution and wait for user actions after outputting A2UI schemas.
