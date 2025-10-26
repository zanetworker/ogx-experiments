#!/usr/bin/env python3
"""
Complete runnable example demonstrating OpenTelemetry semantic conventions
for Llama Stack agent operations.

This example shows:
1. Setting up OpenTelemetry with OTLP exporter
2. Creating an agent with semantic conventions
3. Invoking the agent with proper attributes
4. Executing tools with proper attributes
5. Making inference calls with proper attributes

Run this example with:
    OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 python complete_example.py

Prerequisites:
- OpenTelemetry Collector or compatible backend running on localhost:4318
- Or use Jaeger all-in-one: docker run -d -p 4318:4318 -p 16686:16686 jaegertracing/all-in-one:latest
"""

import asyncio
import json
import os
import uuid
from datetime import UTC, datetime

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


class SemanticConventions:
    """Simplified version of semantic conventions for this example."""

    class Operation:
        CREATE_AGENT = "create_agent"
        INVOKE_AGENT = "invoke_agent"
        EXECUTE_TOOL = "execute_tool"
        CHAT = "chat"

    class Provider:
        META_REFERENCE = "meta.reference"
        OPENAI = "openai"

    @staticmethod
    def create_agent_attributes(agent_id, agent_name, model, instructions=None):
        attrs = {
            "gen_ai.operation.name": SemanticConventions.Operation.CREATE_AGENT,
            "gen_ai.provider.name": SemanticConventions.Provider.META_REFERENCE,
            "gen_ai.agent.id": agent_id,
            "gen_ai.agent.name": agent_name,
            "gen_ai.request.model": model,
        }
        if instructions:
            attrs["gen_ai.agent.description"] = instructions
        return attrs

    @staticmethod
    def invoke_agent_attributes(
        agent_id, agent_name, session_id, model, temperature=None, max_tokens=None, top_p=None
    ):
        attrs = {
            "gen_ai.operation.name": SemanticConventions.Operation.INVOKE_AGENT,
            "gen_ai.provider.name": SemanticConventions.Provider.META_REFERENCE,
            "gen_ai.agent.id": agent_id,
            "gen_ai.agent.name": agent_name,
            "gen_ai.conversation.id": session_id,
            "gen_ai.request.model": model,
        }
        if temperature is not None:
            attrs["gen_ai.request.temperature"] = temperature
        if max_tokens is not None:
            attrs["gen_ai.request.max_tokens"] = max_tokens
        if top_p is not None:
            attrs["gen_ai.request.top_p"] = top_p
        return attrs

    @staticmethod
    def execute_tool_attributes(tool_name, tool_call_id, tool_arguments):
        return {
            "gen_ai.operation.name": SemanticConventions.Operation.EXECUTE_TOOL,
            "gen_ai.provider.name": SemanticConventions.Provider.META_REFERENCE,
            "tool.name": tool_name,
            "tool.call_id": tool_call_id,
            "tool.arguments": json.dumps(tool_arguments),
        }

    @staticmethod
    def chat_attributes(model, provider, messages_count, temperature=None, max_tokens=None):
        attrs = {
            "gen_ai.operation.name": SemanticConventions.Operation.CHAT,
            "gen_ai.provider.name": provider,
            "gen_ai.request.model": model,
            "gen_ai.request.message_count": messages_count,
        }
        if temperature is not None:
            attrs["gen_ai.request.temperature"] = temperature
        if max_tokens is not None:
            attrs["gen_ai.request.max_tokens"] = max_tokens
        return attrs


def setup_telemetry():
    """Initialize OpenTelemetry with OTLP exporter."""
    # Check if OTLP endpoint is configured
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        print("⚠️  OTEL_EXPORTER_OTLP_ENDPOINT not set. Telemetry will not be exported.")
        print("   Set it to http://localhost:4318 if you have a collector running.")
        return None

    # Create tracer provider
    provider = TracerProvider()
    trace.set_tracer_provider(provider)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter()
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)

    print(f"✅ OpenTelemetry configured to export to {endpoint}")
    return trace.get_tracer(__name__)


async def simulate_create_agent(tracer):
    """Simulate creating an agent with semantic conventions."""
    agent_id = str(uuid.uuid4())
    agent_name = "Research Assistant"
    model = "meta-llama/Llama-3.3-70B-Instruct"
    instructions = "You are a helpful research assistant with access to web search and knowledge base."

    # Create span with semantic convention attributes
    attributes = SemanticConventions.create_agent_attributes(
        agent_id=agent_id, agent_name=agent_name, model=model, instructions=instructions
    )

    # Span name follows convention: "create_agent {agent_name}"
    with tracer.start_as_current_span(f"create_agent {agent_name}", attributes=attributes) as span:
        print(f"\n📝 Creating agent: {agent_name}")
        print(f"   Agent ID: {agent_id}")
        print(f"   Model: {model}")

        # Simulate agent creation work
        await asyncio.sleep(0.1)

        # Add response attributes
        span.set_attribute("gen_ai.response.id", agent_id)
        span.set_attribute("gen_ai.response.model", model)

        print(f"✅ Agent created successfully")

    return agent_id, agent_name, model


async def simulate_tool_execution(tracer, tool_name, tool_call_id, arguments):
    """Simulate executing a tool with semantic conventions."""
    attributes = SemanticConventions.execute_tool_attributes(
        tool_name=tool_name, tool_call_id=tool_call_id, tool_arguments=arguments
    )

    # Span name follows convention: "execute_tool {tool_name}"
    with tracer.start_as_current_span(f"execute_tool {tool_name}", attributes=attributes) as span:
        print(f"   🔧 Executing tool: {tool_name}")
        print(f"      Arguments: {arguments}")

        # Simulate tool execution
        await asyncio.sleep(0.2)

        # Simulate tool result
        result = {"status": "success", "data": f"Results from {tool_name}"}
        span.set_attribute("tool.result", json.dumps(result))

        print(f"   ✅ Tool completed: {tool_name}")

        return result


async def simulate_chat_completion(tracer, model, provider, messages_count, temperature, max_tokens):
    """Simulate a chat completion call with semantic conventions."""
    attributes = SemanticConventions.chat_attributes(
        model=model,
        provider=provider,
        messages_count=messages_count,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Span name follows convention: "chat {model}"
    with tracer.start_as_current_span(f"chat {model}", attributes=attributes) as span:
        print(f"   💬 Chat completion with {model}")
        print(f"      Messages: {messages_count}, Temperature: {temperature}")

        # Simulate inference call
        await asyncio.sleep(0.3)

        # Add response attributes
        response_id = f"chatcmpl-{uuid.uuid4()}"
        span.set_attribute("gen_ai.response.id", response_id)
        span.set_attribute("gen_ai.response.finish_reasons", ["stop"])
        span.set_attribute("gen_ai.usage.input_tokens", 150)
        span.set_attribute("gen_ai.usage.output_tokens", 75)
        span.set_attribute("gen_ai.usage.total_tokens", 225)

        print(f"   ✅ Chat completed (tokens: 150 in, 75 out)")

        return {"response_id": response_id, "content": "Here are the results..."}


async def simulate_agent_turn(tracer, agent_id, agent_name, model):
    """Simulate a complete agent turn with nested spans."""
    session_id = str(uuid.uuid4())
    turn_id = str(uuid.uuid4())

    # Create root span for agent invocation
    attributes = SemanticConventions.invoke_agent_attributes(
        agent_id=agent_id,
        agent_name=agent_name,
        session_id=session_id,
        model=model,
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9,
    )

    # Span name follows convention: "invoke_agent {agent_name}"
    with tracer.start_as_current_span(f"invoke_agent {agent_name}", attributes=attributes) as span:
        print(f"\n🤖 Invoking agent: {agent_name}")
        print(f"   Session ID: {session_id}")
        print(f"   Turn ID: {turn_id}")

        # Step 1: Initial inference call
        print(f"\n   Step 1: Initial inference")
        await simulate_chat_completion(
            tracer, model=model, provider=SemanticConventions.Provider.META_REFERENCE, messages_count=1, temperature=0.7, max_tokens=1024
        )

        # Step 2: Execute web search tool
        print(f"\n   Step 2: Tool execution")
        await simulate_tool_execution(
            tracer, tool_name="web_search", tool_call_id="call_1", arguments={"query": "latest AI research"}
        )

        # Step 3: Execute knowledge search tool
        await simulate_tool_execution(
            tracer,
            tool_name="knowledge_search",
            tool_call_id="call_2",
            arguments={"query": "machine learning papers", "top_k": 5},
        )

        # Step 4: Final inference call with tool results
        print(f"\n   Step 3: Final inference with tool results")
        await simulate_chat_completion(
            tracer, model=model, provider=SemanticConventions.Provider.META_REFERENCE, messages_count=5, temperature=0.7, max_tokens=1024
        )

        # Add final response attributes to agent span
        span.set_attribute("gen_ai.response.finish_reasons", ["stop"])
        span.set_attribute("gen_ai.response.id", turn_id)
        span.set_attribute("gen_ai.usage.input_tokens", 500)
        span.set_attribute("gen_ai.usage.output_tokens", 250)
        span.set_attribute("gen_ai.usage.total_tokens", 750)

        print(f"\n✅ Agent turn completed successfully")
        print(f"   Total tokens: 750 (500 in, 250 out)")


async def main():
    """Main function demonstrating the complete flow."""
    print("=" * 80)
    print("OpenTelemetry Semantic Conventions Example for Llama Stack")
    print("=" * 80)

    # Setup telemetry
    tracer = setup_telemetry()
    if not tracer:
        tracer = trace.get_tracer(__name__)  # Use no-op tracer

    # Example 1: Create an agent
    agent_id, agent_name, model = await simulate_create_agent(tracer)

    # Example 2: Execute an agent turn with nested operations
    await simulate_agent_turn(tracer, agent_id, agent_name, model)

    print("\n" + "=" * 80)
    print("✅ Example completed!")
    print("\nTo view traces:")
    print("1. Ensure OpenTelemetry Collector or Jaeger is running")
    print("2. Visit http://localhost:16686 (for Jaeger)")
    print("3. Search for service: 'llama-stack' or your OTEL_SERVICE_NAME")
    print("=" * 80)

    # Force flush to ensure all spans are exported
    if os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"):
        trace.get_tracer_provider().force_flush()
        await asyncio.sleep(1)  # Give time for export


if __name__ == "__main__":
    asyncio.run(main())

