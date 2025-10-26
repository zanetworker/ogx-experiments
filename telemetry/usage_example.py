"""
Practical usage examples showing how to integrate OpenTelemetry semantic conventions
into Llama Stack's agent and tool execution flows.

This demonstrates how the existing code would be modified to follow the conventions.
"""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from llama_stack.apis.agents import AgentConfig, AgentTurnCreateRequest
from llama_stack.apis.inference import SamplingParams, ToolCall
from llama_stack.providers.utils.telemetry import tracing

from semantic_conventions_example import SemanticConventions


# ============================================================================
# Example 1: Create Agent with Semantic Conventions
# ============================================================================


async def create_agent_with_conventions(agent_config: AgentConfig) -> str:
    """
    Example of creating an agent with proper semantic convention attributes.

    This would be integrated into:
    llama_stack/providers/inline/agents/meta_reference/agents.py::create_agent()
    """
    agent_id = str(uuid.uuid4())

    # Create span attributes following semantic conventions
    attributes = SemanticConventions.create_agent_attributes(
        agent_config=agent_config,
        agent_id=agent_id,
        provider_name=SemanticConventions.Provider.META_REFERENCE,
        model=agent_config.model,
    )

    # Create span with proper naming convention
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.CREATE_AGENT, agent_config.name
    )

    # Use the span with semantic convention attributes
    async with tracing.span(span_name, attributes) as span:
        try:
            # Actual agent creation logic would go here
            # ... store agent config, initialize resources, etc.

            # Add response attributes
            SemanticConventions.add_response_attributes(
                span,
                {
                    "response_id": agent_id,
                    "model": agent_config.model,
                },
            )

            return agent_id

        except Exception as e:
            # Add error attributes following conventions
            SemanticConventions.add_error_attributes(span, e)
            raise


# ============================================================================
# Example 2: Invoke Agent (Agent Turn) with Semantic Conventions
# ============================================================================


async def invoke_agent_with_conventions(
    agent_id: str,
    agent_name: str,
    agent_description: str,
    session_id: str,
    turn_id: str,
    model: str,
    sampling_params: SamplingParams,
    messages: list,
) -> AsyncGenerator:
    """
    Example of invoking an agent with proper semantic convention attributes.

    This would be integrated into:
    llama_stack/providers/inline/agents/meta_reference/agent_instance.py::create_and_execute_turn()
    """

    # Create span attributes following semantic conventions
    attributes = SemanticConventions.invoke_agent_attributes(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_description=agent_description,
        session_id=session_id,
        turn_id=turn_id,
        conversation_id=session_id,  # In Llama Stack, session_id is the conversation
        model=model,
        provider_name=SemanticConventions.Provider.META_REFERENCE,
        sampling_params=sampling_params,
        output_type="text",  # or "json" based on response format
    )

    # Create span with proper naming convention
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.INVOKE_AGENT, agent_name
    )

    # Use the span with semantic convention attributes
    async with tracing.span(span_name, attributes) as span:
        try:
            # Simulate agent execution
            # In real implementation, this would call the actual agent logic
            response_data = {
                "finish_reasons": ["stop"],
                "response_id": f"resp_{uuid.uuid4()}",
                "model": model,
                "input_tokens": 150,
                "output_tokens": 75,
                "total_tokens": 225,
            }

            # Add response attributes
            SemanticConventions.add_response_attributes(span, response_data)

            # Yield results (in streaming mode)
            yield {"type": "response.completed", "data": response_data}

        except Exception as e:
            SemanticConventions.add_error_attributes(span, e)
            raise


# ============================================================================
# Example 3: Execute Tool with Semantic Conventions
# ============================================================================


async def execute_tool_with_conventions(
    tool_name: str, tool_call_id: str, tool_arguments: dict
) -> dict:
    """
    Example of executing a tool with proper semantic convention attributes.

    This would be integrated into:
    llama_stack/providers/inline/agents/meta_reference/agent_instance.py::_execute_tool_call()
    or
    llama_stack/core/routers/tool_runtime.py::invoke_tool()
    """

    # Create span attributes following semantic conventions
    attributes = SemanticConventions.execute_tool_attributes(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        tool_arguments=tool_arguments,
        provider_name=SemanticConventions.Provider.META_REFERENCE,
    )

    # Create span with proper naming convention
    span_name = SemanticConventions.get_span_name(
        SemanticConventions.Operation.EXECUTE_TOOL, tool_name
    )

    # Use the span with semantic convention attributes
    async with tracing.span(span_name, attributes) as span:
        try:
            # Simulate tool execution
            # In real implementation, this would call the actual tool
            result = {"status": "success", "output": "Tool executed successfully"}

            # Add result as attribute
            span.set_attribute("tool.result", str(result))

            return result

        except Exception as e:
            SemanticConventions.add_error_attributes(span, e, error_type="tool_execution_error")
            raise


# ============================================================================
# Example 4: Chat Completion with Semantic Conventions
# ============================================================================


async def chat_completion_with_conventions(
    model: str,
    messages: list,
    sampling_params: SamplingParams,
    tools: list | None = None,
    provider_name: str = "openai",
) -> dict:
    """
    Example of a chat completion call with proper semantic convention attributes.

    This would be integrated into:
    llama_stack/providers/remote/inference/*/inference.py
    or any inference provider implementation
    """

    # Create span attributes following semantic conventions
    attributes = SemanticConventions.chat_completion_attributes(
        model=model,
        provider_name=provider_name,
        messages_count=len(messages),
        sampling_params=sampling_params,
        tools_count=len(tools) if tools else 0,
    )

    # Create span with proper naming convention
    span_name = SemanticConventions.get_span_name(SemanticConventions.Operation.CHAT, model)

    # Use the span with semantic convention attributes
    async with tracing.span(span_name, attributes) as span:
        try:
            # Simulate inference call
            # In real implementation, this would call the actual inference API
            response = {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "model": model,
                "choices": [{"message": {"role": "assistant", "content": "Hello!"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            }

            # Add response attributes
            SemanticConventions.add_response_attributes(
                span,
                {
                    "finish_reasons": [choice["finish_reason"] for choice in response["choices"]],
                    "response_id": response["id"],
                    "model": response["model"],
                    "input_tokens": response["usage"]["prompt_tokens"],
                    "output_tokens": response["usage"]["completion_tokens"],
                    "total_tokens": response["usage"]["total_tokens"],
                },
            )

            return response

        except Exception as e:
            SemanticConventions.add_error_attributes(span, e)
            raise


# ============================================================================
# Example 5: Complete Agent Turn Flow with Nested Spans
# ============================================================================


async def complete_agent_turn_flow_example():
    """
    Example showing a complete agent turn with nested spans following semantic conventions.

    This demonstrates the hierarchy:
    - invoke_agent (root)
      - chat (inference call)
      - execute_tool (tool 1)
      - execute_tool (tool 2)
      - chat (final inference call)
    """

    agent_config = AgentConfig(
        model="meta-llama/Llama-3.3-70B-Instruct",
        name="Research Assistant",
        instructions="You are a helpful research assistant with access to web search.",
        sampling_params=SamplingParams(
            strategy={"type": "top_p", "temperature": 0.7, "top_p": 0.9}, max_tokens=1024
        ),
    )

    agent_id = "agent_123"
    session_id = "session_456"
    turn_id = "turn_789"

    # Root span: invoke_agent
    invoke_attributes = SemanticConventions.invoke_agent_attributes(
        agent_id=agent_id,
        agent_name=agent_config.name,
        agent_description=agent_config.instructions,
        session_id=session_id,
        turn_id=turn_id,
        model=agent_config.model,
        sampling_params=agent_config.sampling_params,
    )

    async with tracing.span(
        SemanticConventions.get_span_name(SemanticConventions.Operation.INVOKE_AGENT, agent_config.name),
        invoke_attributes,
    ) as agent_span:
        # Step 1: Initial inference call
        chat_attributes = SemanticConventions.chat_completion_attributes(
            model=agent_config.model,
            provider_name="meta.reference",
            messages_count=1,
            sampling_params=agent_config.sampling_params,
            tools_count=2,
        )

        async with tracing.span(
            SemanticConventions.get_span_name(SemanticConventions.Operation.CHAT, agent_config.model),
            chat_attributes,
        ):
            # Simulate inference returning tool calls
            pass

        # Step 2: Execute tool 1 (web search)
        tool1_attributes = SemanticConventions.execute_tool_attributes(
            tool_name="web_search", tool_call_id="call_1", tool_arguments={"query": "latest AI news"}
        )

        async with tracing.span(
            SemanticConventions.get_span_name(SemanticConventions.Operation.EXECUTE_TOOL, "web_search"),
            tool1_attributes,
        ):
            # Simulate tool execution
            pass

        # Step 3: Execute tool 2 (knowledge search)
        tool2_attributes = SemanticConventions.execute_tool_attributes(
            tool_name="knowledge_search",
            tool_call_id="call_2",
            tool_arguments={"query": "AI research papers"},
        )

        async with tracing.span(
            SemanticConventions.get_span_name(SemanticConventions.Operation.EXECUTE_TOOL, "knowledge_search"),
            tool2_attributes,
        ):
            # Simulate tool execution
            pass

        # Step 4: Final inference call with tool results
        async with tracing.span(
            SemanticConventions.get_span_name(SemanticConventions.Operation.CHAT, agent_config.model),
            chat_attributes,
        ):
            # Simulate final inference
            pass

        # Add final response attributes to agent span
        SemanticConventions.add_response_attributes(
            agent_span,
            {
                "finish_reasons": ["stop"],
                "response_id": f"turn_{turn_id}",
                "model": agent_config.model,
                "input_tokens": 500,
                "output_tokens": 250,
                "total_tokens": 750,
            },
        )


# ============================================================================
# Example 6: Integration Point in Existing Code
# ============================================================================


def show_integration_in_existing_code():
    """
    This shows how to modify the existing agent_instance.py code.

    BEFORE (current code in agent_instance.py around line 200):
    ```python
    async def resume_turn(self, request: AgentTurnResumeRequest) -> AsyncGenerator:
        if self.telemetry_enabled:
            span = tracing.get_current_span()
            if span is not None:
                span.set_attribute("agent_id", self.agent_id)
                span.set_attribute("session_id", request.session_id)
                span.set_attribute("request", request.model_dump_json())
                span.set_attribute("turn_id", request.turn_id)
                if self.agent_config.name:
                    span.set_attribute("agent_name", self.agent_config.name)
    ```

    AFTER (with semantic conventions):
    ```python
    async def resume_turn(self, request: AgentTurnResumeRequest) -> AsyncGenerator:
        if self.telemetry_enabled:
            span = tracing.get_current_span()
            if span is not None:
                # Add semantic convention attributes
                attributes = SemanticConventions.invoke_agent_attributes(
                    agent_id=self.agent_id,
                    agent_name=self.agent_config.name,
                    agent_description=self.agent_config.instructions,
                    session_id=request.session_id,
                    turn_id=request.turn_id,
                    model=self.agent_config.model,
                    sampling_params=self.agent_config.sampling_params,
                )
                for key, value in attributes.items():
                    span.set_attribute(key, value)

                # Keep existing custom attributes for backward compatibility
                span.set_attribute("request", request.model_dump_json())
    ```
    """
    pass

