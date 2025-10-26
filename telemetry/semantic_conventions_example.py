"""
Example implementation of OpenTelemetry Semantic Conventions for GenAI in Llama Stack.

This module demonstrates how to implement the semantic conventions defined in
Semantic_conventions_otel.md for agent operations, tool execution, and inference.

Reference: experiments/telemetry/Semantic_conventions_otel.md
"""

from datetime import UTC, datetime
from typing import Any

from llama_stack.apis.agents import AgentConfig
from llama_stack.apis.inference import SamplingParams
from llama_stack.providers.utils.telemetry import tracing


class SemanticConventions:
    """
    Helper class to create standardized span attributes following OpenTelemetry
    semantic conventions for GenAI operations.
    """

    # Operation names as defined in the semantic conventions
    class Operation:
        CREATE_AGENT = "create_agent"
        INVOKE_AGENT = "invoke_agent"
        EXECUTE_TOOL = "execute_tool"
        CHAT = "chat"
        EMBEDDINGS = "embeddings"
        GENERATE_CONTENT = "generate_content"
        TEXT_COMPLETION = "text_completion"

    # Provider names
    class Provider:
        OPENAI = "openai"
        ANTHROPIC = "anthropic"
        AWS_BEDROCK = "aws.bedrock"
        AZURE_OPENAI = "azure.ai.openai"
        GCP_VERTEX_AI = "gcp.vertex_ai"
        GCP_GEMINI = "gcp.gemini"
        META_REFERENCE = "meta.reference"  # For Llama Stack's own implementation

    @staticmethod
    def create_agent_attributes(
        agent_config: AgentConfig,
        agent_id: str | None = None,
        provider_name: str = Provider.META_REFERENCE,
        model: str | None = None,
        server_address: str | None = None,
        server_port: int | None = None,
    ) -> dict[str, Any]:
        """
        Create attributes for a 'create_agent' span following semantic conventions.

        Args:
            agent_config: The agent configuration
            agent_id: Unique identifier for the agent
            provider_name: The GenAI provider name
            model: The model being used
            server_address: Server address if applicable
            server_port: Server port if applicable

        Returns:
            Dictionary of span attributes
        """
        attributes = {
            "gen_ai.operation.name": SemanticConventions.Operation.CREATE_AGENT,
            "gen_ai.provider.name": provider_name,
        }

        # Conditionally required attributes
        if agent_id:
            attributes["gen_ai.agent.id"] = agent_id

        if agent_config.name:
            attributes["gen_ai.agent.name"] = agent_config.name

        if agent_config.instructions:
            attributes["gen_ai.agent.description"] = agent_config.instructions

        if model or agent_config.model:
            attributes["gen_ai.request.model"] = model or agent_config.model

        # System instructions (opt-in)
        if agent_config.instructions:
            attributes["gen_ai.system_instructions"] = [
                {"type": "text", "content": agent_config.instructions}
            ]

        # Server information
        if server_address:
            attributes["server.address"] = server_address
        if server_port:
            attributes["server.port"] = server_port

        return attributes

    @staticmethod
    def invoke_agent_attributes(
        agent_id: str,
        agent_name: str | None = None,
        agent_description: str | None = None,
        session_id: str | None = None,
        turn_id: str | None = None,
        conversation_id: str | None = None,
        model: str | None = None,
        provider_name: str = Provider.META_REFERENCE,
        sampling_params: SamplingParams | None = None,
        data_source_id: str | None = None,
        output_type: str | None = None,
        server_address: str | None = None,
        server_port: int | None = None,
    ) -> dict[str, Any]:
        """
        Create attributes for an 'invoke_agent' span following semantic conventions.

        Args:
            agent_id: Unique identifier for the agent
            agent_name: Human-readable agent name
            agent_description: Agent description
            session_id: Session identifier
            turn_id: Turn identifier
            conversation_id: Conversation/thread identifier
            model: Model being used
            provider_name: The GenAI provider name
            sampling_params: Sampling parameters for the request
            data_source_id: Data source identifier if using RAG
            output_type: Output content type (text, json, image)
            server_address: Server address if applicable
            server_port: Server port if applicable

        Returns:
            Dictionary of span attributes
        """
        attributes = {
            "gen_ai.operation.name": SemanticConventions.Operation.INVOKE_AGENT,
            "gen_ai.provider.name": provider_name,
            "gen_ai.agent.id": agent_id,
        }

        # Conditionally required attributes
        if agent_name:
            attributes["gen_ai.agent.name"] = agent_name

        if agent_description:
            attributes["gen_ai.agent.description"] = agent_description

        if conversation_id or session_id:
            attributes["gen_ai.conversation.id"] = conversation_id or session_id

        if model:
            attributes["gen_ai.request.model"] = model

        if data_source_id:
            attributes["gen_ai.data_source.id"] = data_source_id

        if output_type:
            attributes["gen_ai.output.type"] = output_type

        # Recommended attributes from sampling params
        if sampling_params:
            if hasattr(sampling_params, "max_tokens") and sampling_params.max_tokens:
                attributes["gen_ai.request.max_tokens"] = sampling_params.max_tokens

            if hasattr(sampling_params, "strategy") and sampling_params.strategy:
                strategy = sampling_params.strategy
                if hasattr(strategy, "temperature") and strategy.temperature is not None:
                    attributes["gen_ai.request.temperature"] = strategy.temperature
                if hasattr(strategy, "top_p") and strategy.top_p is not None:
                    attributes["gen_ai.request.top_p"] = strategy.top_p

            if hasattr(sampling_params, "repetition_penalty") and sampling_params.repetition_penalty:
                attributes["gen_ai.request.frequency_penalty"] = sampling_params.repetition_penalty

        # Custom attributes for Llama Stack
        if session_id:
            attributes["llama_stack.session.id"] = session_id
        if turn_id:
            attributes["llama_stack.turn.id"] = turn_id

        # Server information
        if server_address:
            attributes["server.address"] = server_address
        if server_port:
            attributes["server.port"] = server_port

        return attributes

    @staticmethod
    def execute_tool_attributes(
        tool_name: str,
        tool_call_id: str | None = None,
        tool_arguments: dict[str, Any] | None = None,
        provider_name: str = Provider.META_REFERENCE,
        server_address: str | None = None,
        server_port: int | None = None,
    ) -> dict[str, Any]:
        """
        Create attributes for an 'execute_tool' span following semantic conventions.

        Args:
            tool_name: Name of the tool being executed
            tool_call_id: Unique identifier for this tool call
            tool_arguments: Arguments passed to the tool
            provider_name: The GenAI provider name
            server_address: Server address if applicable
            server_port: Server port if applicable

        Returns:
            Dictionary of span attributes
        """
        attributes = {
            "gen_ai.operation.name": SemanticConventions.Operation.EXECUTE_TOOL,
            "gen_ai.provider.name": provider_name,
            "tool.name": tool_name,
        }

        if tool_call_id:
            attributes["tool.call_id"] = tool_call_id

        if tool_arguments:
            # Serialize arguments as JSON string
            import json

            attributes["tool.arguments"] = json.dumps(tool_arguments)

        # Server information
        if server_address:
            attributes["server.address"] = server_address
        if server_port:
            attributes["server.port"] = server_port

        return attributes

    @staticmethod
    def chat_completion_attributes(
        model: str,
        provider_name: str,
        messages_count: int | None = None,
        sampling_params: SamplingParams | None = None,
        tools_count: int | None = None,
        server_address: str | None = None,
        server_port: int | None = None,
    ) -> dict[str, Any]:
        """
        Create attributes for a 'chat' completion span.

        Args:
            model: Model identifier
            provider_name: The GenAI provider name
            messages_count: Number of messages in the request
            sampling_params: Sampling parameters
            tools_count: Number of tools available
            server_address: Server address if applicable
            server_port: Server port if applicable

        Returns:
            Dictionary of span attributes
        """
        attributes = {
            "gen_ai.operation.name": SemanticConventions.Operation.CHAT,
            "gen_ai.provider.name": provider_name,
            "gen_ai.request.model": model,
        }

        if messages_count is not None:
            attributes["gen_ai.request.message_count"] = messages_count

        if tools_count is not None:
            attributes["gen_ai.request.tools_count"] = tools_count

        # Add sampling parameters
        if sampling_params:
            if hasattr(sampling_params, "max_tokens") and sampling_params.max_tokens:
                attributes["gen_ai.request.max_tokens"] = sampling_params.max_tokens

            if hasattr(sampling_params, "strategy") and sampling_params.strategy:
                strategy = sampling_params.strategy
                if hasattr(strategy, "temperature") and strategy.temperature is not None:
                    attributes["gen_ai.request.temperature"] = strategy.temperature
                if hasattr(strategy, "top_p") and strategy.top_p is not None:
                    attributes["gen_ai.request.top_p"] = strategy.top_p

        # Server information
        if server_address:
            attributes["server.address"] = server_address
        if server_port:
            attributes["server.port"] = server_port

        return attributes

    @staticmethod
    def get_span_name(operation: str, entity_name: str | None = None) -> str:
        """
        Generate a span name following semantic conventions.

        Args:
            operation: The operation name (e.g., "create_agent", "invoke_agent")
            entity_name: The entity name (e.g., agent name, tool name)

        Returns:
            Formatted span name
        """
        if entity_name:
            return f"{operation} {entity_name}"
        return operation

    @staticmethod
    def add_response_attributes(span, response_data: dict[str, Any]) -> None:
        """
        Add response attributes to an existing span.

        Args:
            span: The span object to add attributes to
            response_data: Response data containing finish reasons, token counts, etc.
        """
        if not span:
            return

        if "finish_reasons" in response_data:
            span.set_attribute("gen_ai.response.finish_reasons", response_data["finish_reasons"])

        if "response_id" in response_data:
            span.set_attribute("gen_ai.response.id", response_data["response_id"])

        if "model" in response_data:
            span.set_attribute("gen_ai.response.model", response_data["model"])

        # Token usage
        if "input_tokens" in response_data:
            span.set_attribute("gen_ai.usage.input_tokens", response_data["input_tokens"])
        if "output_tokens" in response_data:
            span.set_attribute("gen_ai.usage.output_tokens", response_data["output_tokens"])
        if "total_tokens" in response_data:
            span.set_attribute("gen_ai.usage.total_tokens", response_data["total_tokens"])

    @staticmethod
    def add_error_attributes(span, error: Exception, error_type: str | None = None) -> None:
        """
        Add error attributes to a span following semantic conventions.

        Args:
            span: The span object to add attributes to
            error: The exception that occurred
            error_type: Optional error type classification
        """
        if not span:
            return

        # Use the exception class name if error_type not provided
        if not error_type:
            error_type = error.__class__.__name__

        span.set_attribute("error.type", error_type)
        span.set_attribute("error.message", str(error))

