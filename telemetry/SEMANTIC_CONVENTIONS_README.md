# OpenTelemetry Semantic Conventions for Llama Stack

This directory contains documentation and examples for implementing OpenTelemetry semantic conventions for GenAI operations in Llama Stack.

## 📁 Files in this Directory

### Specification
- **`Semantic_conventions_otel.md`** - The official semantic conventions specification for GenAI agent and framework spans. This defines the standard attributes and naming conventions.

### Implementation
- **`semantic_conventions_example.py`** - Helper class (`SemanticConventions`) that provides methods to create standardized span attributes for different operations (create_agent, invoke_agent, execute_tool, chat).

- **`usage_example.py`** - Practical examples showing how to integrate semantic conventions into Llama Stack's existing code, with before/after comparisons.

- **`complete_example.py`** - A complete, runnable example demonstrating the full flow with OpenTelemetry setup and nested spans.

- **`IMPLEMENTATION_GUIDE.md`** - Comprehensive guide explaining how to implement semantic conventions in Llama Stack, including integration points and benefits.

## 🚀 Quick Start

### 1. Run the Complete Example

First, start an OpenTelemetry collector or Jaeger:

```bash
# Using Docker with Jaeger all-in-one
docker run -d \
  -p 4318:4318 \
  -p 16686:16686 \
  --name jaeger \
  jaegertracing/all-in-one:latest
```

Then run the example:

```bash
cd experiments/telemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 python complete_example.py
```

View traces at: http://localhost:16686

### 2. Understand the Conventions

Read the specification:
```bash
cat Semantic_conventions_otel.md
```

Key concepts:
- **Operation Names**: `create_agent`, `invoke_agent`, `execute_tool`, `chat`
- **Provider Names**: `meta.reference`, `openai`, `anthropic`, etc.
- **Span Naming**: `{operation} {entity_name}` (e.g., "invoke_agent Research Assistant")
- **Required Attributes**: `gen_ai.operation.name`, `gen_ai.provider.name`
- **Recommended Attributes**: `gen_ai.request.temperature`, `gen_ai.usage.input_tokens`, etc.

### 3. Review Integration Examples

See how to integrate into existing code:
```bash
cat usage_example.py
```

This shows practical integration points in:
- Agent creation (`agents.py`)
- Agent turn execution (`agent_instance.py`)
- Tool execution (`tool_runtime.py`)
- Inference calls (provider implementations)

## 📊 Semantic Convention Attributes

### Create Agent Operation

```python
{
    "gen_ai.operation.name": "create_agent",
    "gen_ai.provider.name": "meta.reference",
    "gen_ai.agent.id": "agent_123",
    "gen_ai.agent.name": "Research Assistant",
    "gen_ai.agent.description": "Helpful research assistant",
    "gen_ai.request.model": "meta-llama/Llama-3.3-70B-Instruct"
}
```

**Span Name**: `create_agent Research Assistant`

### Invoke Agent Operation

```python
{
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
```

**Span Name**: `invoke_agent Research Assistant`

### Execute Tool Operation

```python
{
    "gen_ai.operation.name": "execute_tool",
    "gen_ai.provider.name": "meta.reference",
    "tool.name": "web_search",
    "tool.call_id": "call_abc123",
    "tool.arguments": '{"query": "latest AI news"}'
}
```

**Span Name**: `execute_tool web_search`

### Chat Completion Operation

```python
{
    "gen_ai.operation.name": "chat",
    "gen_ai.provider.name": "openai",
    "gen_ai.request.model": "gpt-4",
    "gen_ai.request.temperature": 0.7,
    "gen_ai.request.max_tokens": 1024,
    "gen_ai.usage.input_tokens": 150,
    "gen_ai.usage.output_tokens": 75,
    "gen_ai.usage.total_tokens": 225
}
```

**Span Name**: `chat gpt-4`

## 🏗️ Span Hierarchy Example

A typical agent turn creates this span hierarchy:

```
invoke_agent Research Assistant (INTERNAL)
├── chat meta-llama/Llama-3.3-70B-Instruct (CLIENT)
├── execute_tool web_search (INTERNAL)
├── execute_tool knowledge_search (INTERNAL)
└── chat meta-llama/Llama-3.3-70B-Instruct (CLIENT)
```

## 🔧 Integration into Llama Stack

### Current State
- ✅ Uses OpenTelemetry SDK
- ✅ Creates spans with custom attributes
- ❌ Does NOT follow semantic conventions

### Target State
- ✅ All of the above, plus:
- ✅ Standardized `gen_ai.*` attributes
- ✅ Proper span naming conventions
- ✅ Correct span kinds (CLIENT vs INTERNAL)

### Key Integration Points

1. **Agent Creation** (`llama_stack/providers/inline/agents/meta_reference/agents.py`)
   - Add semantic convention attributes to `create_agent()` method

2. **Agent Invocation** (`llama_stack/providers/inline/agents/meta_reference/agent_instance.py`)
   - Add attributes to `create_and_execute_turn()` and `resume_turn()` methods

3. **Tool Execution** (`llama_stack/core/routers/tool_runtime.py`)
   - Add attributes to `invoke_tool()` method

4. **Inference Calls** (Various provider implementations)
   - Add attributes to chat completion methods

See `IMPLEMENTATION_GUIDE.md` for detailed integration instructions.

## 📚 Usage in Code

### Using the SemanticConventions Helper

```python
from semantic_conventions_example import SemanticConventions
from llama_stack.providers.utils.telemetry import tracing

# Create agent with semantic conventions
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

async with tracing.span(span_name, attributes) as span:
    # Your agent creation logic
    ...
    
    # Add response attributes
    SemanticConventions.add_response_attributes(span, {
        'response_id': agent_id,
        'model': agent_config.model,
    })
```

## 🎯 Benefits

1. **Standardization**: Consistent attribute names across all GenAI operations
2. **Interoperability**: Works with any OpenTelemetry-compatible observability platform
3. **Discoverability**: Standard attributes make it easy to query and analyze traces
4. **Best Practices**: Follows industry-standard conventions for GenAI telemetry
5. **Future-Proof**: Aligned with evolving OpenTelemetry standards

## 🔍 Querying Traces

With semantic conventions, you can easily query traces:

```
# Find all agent invocations
gen_ai.operation.name = "invoke_agent"

# Find all tool executions for a specific tool
gen_ai.operation.name = "execute_tool" AND tool.name = "web_search"

# Find all high-temperature inference calls
gen_ai.operation.name = "chat" AND gen_ai.request.temperature > 0.8

# Find all operations using a specific model
gen_ai.request.model = "meta-llama/Llama-3.3-70B-Instruct"

# Find all agent operations for a specific session
gen_ai.conversation.id = "session_456"
```

## 📖 References

- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [GenAI Semantic Conventions (GitHub)](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/gen-ai/README.md)
- [OpenTelemetry Python SDK](https://opentelemetry-python.readthedocs.io/)
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)

## 🤝 Contributing

To contribute improvements to the semantic conventions implementation:

1. Review the specification in `Semantic_conventions_otel.md`
2. Update the helper class in `semantic_conventions_example.py`
3. Add usage examples to `usage_example.py`
4. Update the implementation guide in `IMPLEMENTATION_GUIDE.md`
5. Test with the complete example in `complete_example.py`

## ❓ FAQ

**Q: Why use semantic conventions?**  
A: They provide standardized attribute names that work across different observability platforms and make traces easier to query and analyze.

**Q: Do I need to change existing code?**  
A: Yes, but the changes are minimal. You mainly need to add standardized attributes to existing span creation calls.

**Q: Will this break existing telemetry?**  
A: No, you can add semantic convention attributes alongside existing custom attributes for backward compatibility.

**Q: What if I'm using a different provider (OpenAI, Anthropic, etc.)?**  
A: Use the appropriate provider name from `SemanticConventions.Provider` (e.g., `Provider.OPENAI`, `Provider.ANTHROPIC`).

**Q: How do I test this?**  
A: Run the `complete_example.py` with an OpenTelemetry collector or Jaeger, then view the traces in the UI.

