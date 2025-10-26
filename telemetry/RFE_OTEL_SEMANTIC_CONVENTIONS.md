# RFE: Implement OpenTelemetry Semantic Conventions for GenAI in Llama Stack

**Status:** Proposal  
**Created:** 2025-01-24  
**Priority:** High  
**Category:** Observability, Telemetry, Standards Compliance

---

## Problem Statement

Llama Stack currently implements OpenTelemetry (OTel) for distributed tracing and telemetry but **does not follow the standardized OpenTelemetry Semantic Conventions for Generative AI systems**. This creates several critical issues:

### Current State Issues

1. **Non-Standard Attribute Names**
   - Uses custom attributes like `agent_id`, `agent_name`, `session_id`
   - Does not use standardized `gen_ai.*` namespace attributes
   - Lacks `gen_ai.operation.name` and `gen_ai.provider.name` discriminators

2. **Inconsistent Span Naming**
   - Uses arbitrary span names like `"list_mcp_tools"`, `"create_and_execute_turn"`
   - Does not follow OTel convention: `{operation} {entity_name}` format
   - Example: Should be `"invoke_agent Research Assistant"` not `"create_and_execute_turn"`

3. **Missing Required Attributes**
   - No operation type identification (`gen_ai.operation.name`)
   - No provider identification (`gen_ai.provider.name`)
   - Missing model parameters (`gen_ai.request.temperature`, `gen_ai.request.max_tokens`)
   - No token usage tracking (`gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`)

4. **Limited Interoperability**
   - Telemetry data is not compatible with industry-standard observability platforms
   - Cannot leverage existing GenAI monitoring dashboards and tools
   - Difficult to compare performance across different GenAI systems
   - Non-standard format prevents integration with tools like Traceloop, LangSmith, Arize Phoenix

5. **Poor Discoverability**
   - Custom attribute names make it difficult to query and analyze traces
   - No standard way to filter by operation type, model, or provider
   - Inconsistent with other GenAI frameworks (LangChain, LlamaIndex, etc.)

### Impact

- **Developers:** Cannot use standard observability tools and dashboards
- **Operators:** Difficult to monitor and debug GenAI applications in production
- **Ecosystem:** Llama Stack telemetry is incompatible with industry standards
- **Compliance:** Not aligned with OpenTelemetry Working Group recommendations

---

## Overview

This RFE proposes implementing the **OpenTelemetry Semantic Conventions for Generative AI** (v1.37.0) in Llama Stack to standardize telemetry data and enable interoperability with industry-standard observability platforms.

### What Are OTel Semantic Conventions?

OpenTelemetry Semantic Conventions define standardized attribute names, span naming patterns, and telemetry structures for specific domains. The GenAI conventions (currently in Development/Experimental status) provide:

- **Standardized Attributes:** `gen_ai.*` namespace for all GenAI operations
- **Operation Types:** `create_agent`, `invoke_agent`, `execute_tool`, `chat`, `embeddings`
- **Provider Identification:** `openai`, `anthropic`, `aws.bedrock`, `meta.reference`, etc.
- **Span Naming Format:** `{operation} {entity_name}` (e.g., `"invoke_agent Math Tutor"`)
- **Required Metadata:** Model name, temperature, token usage, finish reasons

### References

- **OpenTelemetry GenAI Conventions:** https://opentelemetry.io/docs/specs/semconv/gen-ai/
- **Agent Spans:** https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/
- **Model Spans:** https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/
- **Traceloop/OpenLLMetry:** https://www.traceloop.com/docs/openllmetry/contributing/semantic-conventions
- **OTel Working Group:** https://github.com/open-telemetry/community/blob/main/projects/gen-ai.md

---

## Goals (One-Liners)

### Primary Goals

1. **Standardize span attributes** to use `gen_ai.*` namespace following OTel v1.37.0 conventions
2. **Implement operation-based span naming** using `{operation} {entity_name}` format
3. **Add required discriminator attributes** (`gen_ai.operation.name`, `gen_ai.provider.name`)
4. **Capture model parameters and usage** (temperature, max_tokens, input/output tokens)
5. **Enable backward compatibility** through opt-in environment variable `OTEL_SEMCONV_STABILITY_OPT_IN`

### Secondary Goals

6. **Support tool execution spans** with standardized `execute_tool` operation
7. **Implement conversation tracking** using `gen_ai.conversation.id`
8. **Add finish reason tracking** via `gen_ai.response.finish_reasons`
9. **Document provider-specific extensions** for Llama Stack (`meta.reference` provider)
10. **Create migration guide** for existing Llama Stack users

---

## Success Criteria

### Functional Requirements

✅ **SR-1: Standardized Attributes**
- All GenAI spans MUST include `gen_ai.operation.name` attribute
- All GenAI spans MUST include `gen_ai.provider.name` attribute
- Agent operations MUST include `gen_ai.agent.id`, `gen_ai.agent.name`, `gen_ai.agent.description`
- Model operations MUST include `gen_ai.request.model`, `gen_ai.response.model`
- Tool operations MUST include `tool.name`, `tool.call_id`, `tool.arguments`

✅ **SR-2: Span Naming Convention**
- Create agent spans: `"create_agent {agent_name}"`
- Invoke agent spans: `"invoke_agent {agent_name}"`
- Execute tool spans: `"execute_tool {tool_name}"`
- Chat completion spans: `"chat {model_name}"`
- Embeddings spans: `"embeddings {model_name}"`

✅ **SR-3: Operation Types**
- Support `create_agent` operation for agent creation
- Support `invoke_agent` operation for agent invocation
- Support `execute_tool` operation for tool execution
- Support `chat` operation for inference calls
- Support `embeddings` operation for embedding generation

✅ **SR-4: Provider Identification**
- Use `meta.reference` for Llama Stack's own implementation
- Use appropriate provider names for proxied calls (`openai`, `anthropic`, etc.)
- Document provider-specific attributes in semantic conventions

✅ **SR-5: Model Parameters**
- Capture `gen_ai.request.temperature` when available
- Capture `gen_ai.request.max_tokens` when available
- Capture `gen_ai.request.top_p` when available
- Capture `gen_ai.request.frequency_penalty` when available
- Capture `gen_ai.request.presence_penalty` when available

✅ **SR-6: Token Usage Tracking**
- Record `gen_ai.usage.input_tokens` for all inference operations
- Record `gen_ai.usage.output_tokens` for all inference operations
- Record `gen_ai.usage.total_tokens` as sum of input and output

✅ **SR-7: Conversation Tracking**
- Populate `gen_ai.conversation.id` with session ID when available
- Maintain conversation context across multiple turns
- Support thread/session-based correlation

✅ **SR-8: Backward Compatibility**
- Implement `OTEL_SEMCONV_STABILITY_OPT_IN` environment variable
- Default behavior: continue emitting current (v1.36.0 or prior) conventions
- When `gen_ai_latest_experimental` is set: emit v1.37.0+ conventions
- Do NOT emit both old and new conventions simultaneously

### Non-Functional Requirements

✅ **SR-9: Performance**
- Adding semantic convention attributes MUST NOT increase span creation overhead by >5%
- Attribute serialization MUST be efficient (avoid unnecessary JSON encoding)
- Span naming MUST be computed lazily when possible

✅ **SR-10: Documentation**
- Provide comprehensive migration guide from current to new conventions
- Document all supported `gen_ai.operation.name` values
- Document Llama Stack-specific provider attributes
- Include examples for each operation type

✅ **SR-11: Testing**
- Unit tests for semantic convention attribute generation
- Integration tests verifying span structure and naming
- Validation tests against OTel specification
- Backward compatibility tests

✅ **SR-12: Interoperability**
- Telemetry MUST be compatible with Jaeger, Grafana Tempo, Honeycomb
- Telemetry MUST be compatible with Traceloop/OpenLLMetry
- Telemetry MUST be compatible with LangSmith, Arize Phoenix
- Telemetry MUST be queryable using standard OTel query patterns

### Acceptance Criteria

**The implementation is considered successful when:**

1. ✅ All agent creation operations emit spans with `gen_ai.operation.name=create_agent`
2. ✅ All agent invocation operations emit spans with `gen_ai.operation.name=invoke_agent`
3. ✅ All tool execution operations emit spans with `gen_ai.operation.name=execute_tool`
4. ✅ All inference operations emit spans with `gen_ai.operation.name=chat`
5. ✅ Span names follow the `{operation} {entity}` format
6. ✅ All required attributes are present on appropriate span types
7. ✅ Token usage is accurately tracked and reported
8. ✅ Backward compatibility is maintained via environment variable
9. ✅ Documentation is complete and includes migration guide
10. ✅ Telemetry is validated against OTel specification
11. ✅ Integration with at least 2 major observability platforms is verified
12. ✅ Performance impact is measured and within acceptable limits (<5% overhead)

---

## Implementation Scope

### In Scope

- ✅ Modify span creation in agent operations (`agents.py`, `agent_instance.py`)
- ✅ Modify span creation in tool execution (`tool_runtime.py`)
- ✅ Modify span creation in inference providers
- ✅ Create `SemanticConventions` helper class
- ✅ Implement environment variable-based opt-in
- ✅ Add token usage tracking
- ✅ Update span naming logic
- ✅ Add comprehensive documentation
- ✅ Create migration guide
- ✅ Add validation tests

### Out of Scope

- ❌ Changing existing telemetry infrastructure (OTLPSpanExporter, etc.)
- ❌ Implementing metrics semantic conventions (separate RFE)
- ❌ Implementing events semantic conventions (separate RFE)
- ❌ Modifying log format or structure
- ❌ Adding new telemetry backends
- ❌ Implementing content capture (`gen_ai.input.messages`, `gen_ai.output.messages`) - opt-in only

---

## Technical Approach

### Phase 1: Foundation (Week 1-2)

1. Create `SemanticConventions` helper class in `llama_stack/providers/utils/telemetry/semantic_conventions.py`
2. Implement attribute generation methods for each operation type
3. Implement span naming logic
4. Add environment variable support (`OTEL_SEMCONV_STABILITY_OPT_IN`)

### Phase 2: Integration (Week 3-4)

1. Integrate into agent creation (`llama_stack/providers/inline/agents/meta_reference/agents.py`)
2. Integrate into agent invocation (`llama_stack/providers/inline/agents/meta_reference/agent_instance.py`)
3. Integrate into tool execution (`llama_stack/core/routers/tool_runtime.py`)
4. Integrate into inference providers

### Phase 3: Validation (Week 5)

1. Add unit tests for semantic conventions
2. Add integration tests for span structure
3. Validate against OTel specification
4. Test with Jaeger, Grafana Tempo, Traceloop

### Phase 4: Documentation (Week 6)

1. Write migration guide
2. Document all attributes and operations
3. Create examples and tutorials
4. Update API documentation

---

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking changes for existing users | High | Medium | Use opt-in environment variable, maintain backward compatibility |
| Performance degradation | Medium | Low | Lazy evaluation, efficient serialization, performance testing |
| OTel spec changes | Medium | Medium | Follow stable conventions, document experimental status |
| Incomplete provider coverage | Low | Medium | Start with `meta.reference`, add others incrementally |
| Complex migration path | Medium | Low | Comprehensive documentation, examples, migration guide |

---

## Dependencies

- OpenTelemetry Python SDK (already in use)
- OpenTelemetry Semantic Conventions v1.37.0 specification
- Existing Llama Stack telemetry infrastructure

---

## Timeline

- **Week 1-2:** Foundation and helper class implementation
- **Week 3-4:** Integration into Llama Stack components
- **Week 5:** Testing and validation
- **Week 6:** Documentation and migration guide
- **Week 7:** Review and refinement
- **Week 8:** Release and rollout

**Total Duration:** 8 weeks

---

## Metrics for Success

1. **Adoption Rate:** % of Llama Stack deployments using new conventions (target: 50% within 3 months)
2. **Compatibility:** Number of observability platforms successfully integrated (target: 5+)
3. **Performance:** Overhead of semantic conventions (target: <5%)
4. **Query Efficiency:** Time to query traces by operation type (target: <100ms)
5. **Developer Satisfaction:** Survey score on ease of use (target: 4.5/5)

---

## Appendix: Example Transformations

### Before (Current)
```python
span.set_attribute("agent_id", self.agent_id)
span.set_attribute("session_id", request.session_id)
span.set_attribute("agent_name", self.agent_config.name)
```

### After (With Semantic Conventions)
```python
attributes = SemanticConventions.invoke_agent_attributes(
    agent_id=self.agent_id,
    agent_name=self.agent_config.name,
    session_id=request.session_id,
    model=self.agent_config.model,
    sampling_params=self.agent_config.sampling_params,
)
for key, value in attributes.items():
    span.set_attribute(key, value)
```

### Resulting Attributes
```json
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

---

## References

1. OpenTelemetry Semantic Conventions for GenAI: https://opentelemetry.io/docs/specs/semconv/gen-ai/
2. Traceloop OpenLLMetry: https://www.traceloop.com/docs/openllmetry/
3. OTel GenAI Working Group: https://github.com/open-telemetry/community/blob/main/projects/gen-ai.md
4. Implementation Examples: `/experiments/telemetry/semantic_conventions_example.py`

