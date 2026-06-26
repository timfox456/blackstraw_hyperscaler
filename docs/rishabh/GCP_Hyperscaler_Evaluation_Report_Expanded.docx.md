## **Streaming Visible in Trace**

**Exercise**

Deployed an ADK weather agent to Vertex AI Reasoning Engine with enable\_tracing enabled and executed weather queries through the Python SDK stream\_query interface.

**Pass Result and Condition**

Partial Pass. Invocation, invoke\_agent, call\_llm, generate\_content, and execute\_tool spans were captured along with model metadata and token statistics. Per chunk streaming events and TTFT metrics were unavailable.

**Trace ID**

c726b93cbb1ef459a762a2ab27cb6774

**Additional Notes**

Tracing required explicit enablement and custom tools required additional instrumentation to appear as spans. Reasoning token counts and model identifiers were emitted automatically.

**Pros on GCP**

* Native GenAI semantic spans generated automatically  
* Model metadata and token accounting visible  
* Hierarchical agent execution flow easy to follow

**Cons on GCP**

* No chunk level streaming visibility  
* No TTFT metrics  
* Tracing is not enabled by default

## **Persona Switching Visible in Trace**

**Exercise**

Executed a three turn session consisting of a baseline weather query followed by TV weatherman and scientific personas.

**Pass Result and Condition**

Pass. Persona transitions appeared as execute\_tool set\_persona spans and generated independent reasoning steps.

**Trace ID**

e4fe9b4b3196cf7739ca0437e2e5fa5f

**Additional Notes**

Conversation identifiers persisted across turns and token accumulation increased as session context grew. Each persona change triggered its own execution path.

**Pros on GCP**

* Persona transitions are independently observable  
* Cross turn context growth is visible  
* Reasoning steps are decomposed into individual spans

**Cons on GCP**

* No chunk level streaming events  
* Persona semantics require application implementation

## **Each Orchestration Step Visible in Trace**

**Exercise**

Executed a prompt requiring weather retrieval for Chicago and Miami followed by persona switching and response aggregation.

**Pass Result and Condition**

Pass. Parallel execution, aggregation, persona switching, and response generation appeared as distinct spans.

**Trace ID**

08b300d58ad7d89907a98551abbf9f55

**Additional Notes**

The workflow generated fifteen spans and demonstrated that orchestration decisions could be reconstructed directly from Cloud Trace.

**Pros on GCP**

* Complete workflow represented as a span tree  
* Parallel execution visible without custom instrumentation  
* Reasoning steps map directly to trace spans

**Cons on GCP**

* Trace complexity increases quickly for larger workflows  
* Manual inspection becomes difficult as span counts grow

## **Short Term Memory Operates Inside Pilot**

**Exercise**

Introduced user information in one turn, issued an unrelated weather request, and then requested recall of the original information.

**Pass Result and Condition**

Pass. The agent recalled earlier information and token growth confirmed context accumulation.

**Trace ID**

7da2763e804cc3b46736f1a6bc476abd, 62d27e017ea7f6cad91e60f3f9b2c7d8, fb96c03d0e35a8fe3304b0c5433cc81e

**Additional Notes**

Session identifiers enabled grouping of related interactions, but each turn emitted as an independent trace and required application level correlation.

**Pros on GCP**

* Session context accumulation works natively  
* Token growth provides evidence of memory retention  
* Session IDs allow logical grouping

**Cons on GCP**

* Cross turn relationships require custom correlation  
* No native cross trace conversation visualization

## **Dreaming Visible as Discrete Trace Event**

**Exercise**

Executed a three turn conversation ending with a consolidation request that triggered dream\_consolidate.

**Pass Result and Condition**

Pass with custom implementation. Dreaming appeared as a dedicated execute\_tool span with custom semantic attributes.

**Trace ID**

d84a15017ccd4ea3c3a25f2c88825e42

**Additional Notes**

Custom attributes included consolidation type, turn count, summary length, prompt identifier, and prompt version.

**Pros on GCP**

* Custom semantic attributes can be queried  
* Custom workflows become first class trace events  
* Prompt metadata can be attached manually

**Cons on GCP**

* Dreaming is not a native ADK capability  
* Requires custom engineering and instrumentation

## **Costs Attributable at Project Level**

**Exercise**

Executed a three turn weather conversation and inspected generate\_content spans and billing metadata.

**Pass Result and Condition**

Pass. Every span contained project identifiers, model information, and token usage statistics.

**Trace ID**

Invocation IDs e-bc5c6e03-c721-4013-8b0f-72b256473c69, e-c2f633cc-256c-4dd1-9cfa-45614e22596e, e-e2decf5d-0841-47d3-a271-cb2f05c5d518

**Additional Notes**

Input, output, and reasoning tokens were independently visible and conversation identifiers enabled multi turn cost correlation.

**Pros on GCP**

* Project attribution available natively  
* Reasoning token visibility available  
* Conversation level cost analysis possible

**Cons on GCP**

* Reasoning costs not surfaced in default dashboards  
* Custom metrics may be required for complete reporting

## **Blocked or Not Fully Validated Criteria**

* Attachments Visible in Trace. Fail. stream\_query does not support multimodal Content objects and Cloud Trace intentionally avoids storing binary payloads. GCS staging and custom metadata correlation would be required.  
* MCP App Visible in Trace. Fail. Reasoning Engine containers lacked Node.js and public SSE infrastructure required by MCP deployment approaches.  
* Supervisor Routing Visible in Trace. Partial Pass. Routing decisions were visible but downstream execution failed because roles slash aiplatform.user permissions were unavailable.  
* Prompt Version Identifiable. Partial Pass. Prompt identifiers could be manually instrumented but no native Prompt Management to Cloud Trace linkage exists.  
* Retrieval Uses Resolved Entity. Blocked by aiplatform.ragCorpora.query permissions and unavailable RAG infrastructure.  
* Policy Applied Visible. Fail. Model Armor and Agent Gateway were not configured during the pilot.  
* Long Term Memory Operates Inside Pilot. Not exercised because no persistent memory store was configured.  
* Compaction Visible as Discrete Trace Event. Not exercised. Dreaming was implemented but compaction was not independently implemented.  
* Ontology Mappings Visible. Not exercised because no ontology service or knowledge graph layer was configured.  
* Identity Propagation Criteria. Not validated because MCP and private connectivity infrastructure were unavailable.