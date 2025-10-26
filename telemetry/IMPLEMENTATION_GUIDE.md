# OpenTelemetry Semantic Conventions Implementation Guide for Llama Stack

This guide explains how to implement the OpenTelemetry semantic conventions for GenAI operations in Llama Stack, as defined in `Semantic_conventions_otel.md`.

## Overview

The semantic conventions provide standardized attribute names and span naming patterns for GenAI operations, making telemetry data consistent and interoperable across different observability platforms.

## Current State vs. Target State

### Current Implementation
- ✅ Uses OpenTelemetry SDK (OTLPSpanExporter, OTLPMetricExporter)
- ✅ Creates spans with custom attributes
- ✅ Supports W3C Trace Context propagation
- ❌ Does NOT follow GenAI semantic conventions
- ❌ Uses arbitrary attribute names
- ❌ No standardized span naming

### Target Implementation
- ✅ All of the above, plus:
- ✅ Standardized `gen_ai.*` attributes
- ✅ Proper span naming conventions
- ✅ Correct span kinds (CLIENT vs INTERNAL)
- ✅ Required and recommended attributes
- ✅ Error handling with `error.type`

## Key Semantic Convention Attributes

### 1. Create Agent Span

**Span Name:** `create_agent {gen_ai.agent.name}`  
**Span Kind:** `CLIENT`

**Required Attributes:**
- `gen_ai.operation.name` = `"create_agent"`
- `gen_ai.provider.name` = `"meta.reference"` (or appropriate provider)

**Conditionally Required:**
- `gen_ai.agent.id` - Agent unique identifier
- `gen_ai.agent.name` - Human-readable agent name
- `gen_ai.agent.description` - Agent description
- `gen_ai.request.model` - Model being used

**Example:**
```python
attributes = {
    "gen_ai.operation.name": "create_agent",
    "gen_ai.provider.name": "meta.reference",
    "gen_ai.agent.id": "agent_123",
    "gen_ai.agent.name": "Research Assistant",
    "gen_ai.agent.description": "Helpful research assistant",
    "gen_ai.request.model": "meta-llama/Llama-3.3-70B-Instruct"
}
span_name = "create_agent Research Assistant"
```

### 2. Invoke Agent Span

**Span Name:** `invoke_agent {gen_ai.agent.name}`  
**Span Kind:** `INTERNAL` (for in-process agents) or `CLIENT` (for remote agents)

**Required Attributes:**
- `gen_ai.operation.name` = `"invoke_agent"`
- `gen_ai.provider.name` = `"meta.reference"`

**Conditionally Required:**
- `gen_ai.agent.id` - Agent identifier
- `gen_ai.agent.name` - Agent name
- `gen_ai.conversation.id` - Session/conversation ID
- `gen_ai.request.model` - Model being used

**Recommended:**
- `gen_ai.request.temperature`
- `gen_ai.request.max_tokens`
- `gen_ai.request.top_p`
- `gen_ai.response.finish_reasons`
- `gen_ai.response.id`

**Example:**
```python
attributes = {
    "gen_ai.operation.name": "invoke_agent",
    "gen_ai.provider.name": "meta.reference",
    "gen_ai.agent.id": "agent_123",
    "gen_ai.agent.name": "Research Assistant",
    "gen_ai.conversation.id": "session_456",
    "gen_ai.request.model": "meta-llama/Llama-3.3-70B-Instruct",
    "gen_ai.request.temperature": 0.7,
    "gen_ai.request.max_tokens": 1024,
    "gen_ai.request.top_p": 0.9
}
span_name = "invoke_agent Research Assistant"
```

### 3. Execute Tool Span

**Span Name:** `execute_tool {tool.name}`  
**Span Kind:** `INTERNAL` or `CLIENT` (depending on tool location)

**Required Attributes:**
- `gen_ai.operation.name` = `"execute_tool"`
- `gen_ai.provider.name` = `"meta.reference"`
- `tool.name` - Name of the tool

**Recommended:**
- `tool.call_id` - Unique identifier for this tool call
- `tool.arguments` - JSON string of arguments

**Example:**
```python
attributes = {
    "gen_ai.operation.name": "execute_tool",
    "gen_ai.provider.name": "meta.reference",
    "tool.name": "web_search",
    "tool.call_id": "call_abc123",
    "tool.arguments": '{"query": "latest AI news"}'
}
span_name = "execute_tool web_search"
```

### 4. Chat Completion Span

**Span Name:** `chat {gen_ai.request.model}`  
**Span Kind:** `CLIENT`

**Required Attributes:**
- `gen_ai.operation.name` = `"chat"`
- `gen_ai.provider.name` = Provider name (e.g., `"openai"`, `"anthropic"`)
- `gen_ai.request.model` - Model identifier

**Recommended:**
- `gen_ai.request.temperature`
- `gen_ai.request.max_tokens`
- `gen_ai.request.top_p`
- `gen_ai.response.finish_reasons`
- `gen_ai.usage.input_tokens`
- `gen_ai.usage.output_tokens`
- `gen_ai.usage.total_tokens`

## Integration Points in Llama Stack

### 1. Agent Creation
**File:** `llama_stack/providers/inline/agents/meta_reference/agents.py`  
**Method:** `create_agent()`

```python
async def create_agent(self, agent_config: AgentConfig) -> AgentCreateResponse:
    agent_id = str(uuid.uuid4())
    
    # Add semantic convention attributes
    attributes = SemanticConventions.create_agent_attributes(
        agent_config=agent_config,
        agent_id=agent_id,
        provider_name=SemanticConventions.Provider.META_REFERENCE,
        model=agent_config.model,
    )
    
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.CREATE_AGENT,
        agent_config.name
    )
    
    async with tracing.span(span_name, attributes):
        # Existing agent creation logic
        ...
```

### 2. Agent Turn Execution
**File:** `llama_stack/providers/inline/agents/meta_reference/agent_instance.py`  
**Method:** `create_and_execute_turn()` and `resume_turn()`

```python
async def create_and_execute_turn(self, request: AgentTurnCreateRequest):
    if self.telemetry_enabled:
        span = tracing.get_current_span()
        if span:
            # Add semantic convention attributes
            attributes = SemanticConventions.invoke_agent_attributes(
                agent_id=self.agent_id,
                agent_name=self.agent_config.name,
                agent_description=self.agent_config.instructions,
                session_id=request.session_id,
                model=self.agent_config.model,
                sampling_params=self.agent_config.sampling_params,
            )
            for key, value in attributes.items():
                span.set_attribute(key, value)
    
    # Existing turn execution logic
    ...
```

### 3. Tool Execution
**File:** `llama_stack/core/routers/tool_runtime.py`  
**Method:** `invoke_tool()`

```python
async def invoke_tool(self, tool_name: str, kwargs: dict[str, Any]) -> Any:
    attributes = SemanticConventions.execute_tool_attributes(
        tool_name=tool_name,
        tool_arguments=kwargs,
    )
    
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.EXECUTE_TOOL,
        tool_name
    )
    
    async with tracing.span(span_name, attributes):
        provider = await self.routing_table.get_provider_impl(tool_name)
        return await provider.invoke_tool(tool_name=tool_name, kwargs=kwargs)
```

### 4. Inference Calls
**File:** Various inference provider implementations  
**Example:** `llama_stack/providers/remote/inference/openai/openai.py`

```python
async def chat_completion(self, model: str, messages: list, **kwargs):
    attributes = SemanticConventions.chat_completion_attributes(
        model=model,
        provider_name=SemanticConventions.Provider.OPENAI,
        messages_count=len(messages),
        sampling_params=kwargs.get('sampling_params'),
    )
    
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.CHAT,
        model
    )
    
    async with tracing.span(span_name, attributes) as span:
        response = await self._call_openai_api(model, messages, **kwargs)
        
        # Add response attributes
        SemanticConventions.add_response_attributes(span, {
            'finish_reasons': [choice.finish_reason for choice in response.choices],
            'response_id': response.id,
            'model': response.model,
            'input_tokens': response.usage.prompt_tokens,
            'output_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        })
        
        return response
```

## Span Hierarchy Example

A typical agent turn would create the following span hierarchy:

```
invoke_agent Research Assistant (INTERNAL)
├── chat meta-llama/Llama-3.3-70B-Instruct (CLIENT)
├── execute_tool web_search (INTERNAL)
├── execute_tool knowledge_search (INTERNAL)
└── chat meta-llama/Llama-3.3-70B-Instruct (CLIENT)
```

Each span would have the appropriate semantic convention attributes.

## Benefits

1. **Standardization**: Consistent attribute names across all GenAI operations
2. **Interoperability**: Works with any OpenTelemetry-compatible observability platform
3. **Discoverability**: Standard attributes make it easy to query and analyze traces
4. **Best Practices**: Follows industry-standard conventions for GenAI telemetry
5. **Future-Proof**: Aligned with evolving OpenTelemetry standards

## Testing

To verify the implementation:

1. Enable telemetry in Llama Stack:
```bash
OTEL_SERVICE_NAME=llama-stack \
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 \
llama stack run starter
```

2. Run an agent turn and check the exported spans contain:
   - Correct `gen_ai.operation.name` values
   - Proper `gen_ai.provider.name`
   - Required attributes for each operation type
   - Correct span naming format

3. Verify in your observability platform (Jaeger, Grafana, etc.) that:
   - Spans are properly nested
   - Attributes are searchable
   - Metrics can be derived from standard attributes

## References

- [Semantic Conventions Document](./Semantic_conventions_otel.md)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [GenAI Semantic Conventions](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/README.md)

