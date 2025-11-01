# Experiments Directory

This directory contains experimental configurations, demos, and setups for Llama Stack.

## 🎯 Featured Demos

### 7. Agentic Tools with Llama Stack Eval/Scoring/Dataset APIs ⭐ RECOMMENDED
**Production-ready evaluation using Llama Stack's built-in Eval, Scoring, and DatasetIO APIs**

**File**: [`7-agentic-tools-with-llama-stack-evals.py`](./7-agentic-tools-with-llama-stack-evals.py)
**Documentation**: [`LLAMA_STACK_EVALS.md`](./LLAMA_STACK_EVALS.md)

**What it demonstrates**:
- ✅ **DatasetIO API** - Create and manage evaluation datasets
- ✅ **Scoring API** - Custom metrics and aggregations
- ✅ **Eval API** - Automated benchmark runs with job tracking
- ✅ Agentic tool calling with HuggingFace models
- ✅ Built-in telemetry and observability
- ✅ Production-ready evaluation framework

**Quick Start**:
```bash
export LLAMA_STACK_PORT=8080
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"
python experiments/7-agentic-tools-with-llama-stack-evals.py
```

### 6. Agentic Tools + Evals + Observability (Custom Implementation)
**Integration with open source agentic tools and custom evaluation framework**

**File**: [`6-agentic-tools-evals-observability.py`](./6-agentic-tools-evals-observability.py)
**Documentation**: [`AGENTIC_TOOLS_EVALS_OBSERVABILITY.md`](./AGENTIC_TOOLS_EVALS_OBSERVABILITY.md)

**What it demonstrates**:
- ✅ Agentic tool calling with HuggingFace models
- ✅ Custom evaluation framework for testing accuracy
- ✅ Observability with Llama Stack telemetry
- ✅ OpenTelemetry export support
- ✅ Performance metrics and analysis

**Note**: For production use, prefer Demo 7 which uses Llama Stack's native APIs.

**Quick Start**:
```bash
export LLAMA_STACK_PORT=8080
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"
python experiments/6-agentic-tools-evals-observability.py
```

## 📝 All Demos

### 0. Check Models
**File**: [`0-check-models.py`](./0-check-models.py)
Check available models in your Llama Stack instance.

### 1. Simple Client
**File**: [`1-simpleclient.py`](./1-simpleclient.py)
Basic client example for Llama Stack.

### 2. RAG (Retrieval-Augmented Generation)
**File**: [`2-rag.py`](./2-rag.py)
RAG implementation with vector stores.

### 3. Function Tools with Responses API
**File**: [`3-responses-function-tools.py`](./3-responses-function-tools.py)
Complete example of function calling with the Responses API.

**Features**:
- Function tool schema definition
- Tool execution handling
- Result processing

### 4. MCP with Responses API
**File**: [`4-mcp-with-responses.py`](./4-mcp-with-responses.py)
Model Context Protocol (MCP) integration.

**Features**:
- Direct MCP server connection
- Dynamic tool discovery
- No toolgroup registration needed

### 5. Responses with Safety
**File**: [`5-responses-with-safety.py`](./5-responses-with-safety.py)
Safety features with the Responses API.

## 📁 Advanced Projects

### Telemetry Analysis Tools
**Location**: [`telemetry/`](./telemetry/)

Comprehensive suite for analyzing Llama Stack telemetry data.

**Tools**:
- `conversation_replay.py` - Replay conversations step-by-step
- `conversation_patterns.py` - Analyze usage patterns
- `otel_conversation_exporter.py` - Export to OpenTelemetry format
- `otel_validator.py` - Validate OTLP exports

**Quick Start**:
```bash
cd experiments/telemetry
python conversation_replay.py list
python conversation_patterns.py report
```

### RedHat AI Model Recommender
**Location**: [`redhatai_validated_models/`](./redhatai_validated_models/)

Intelligent AI model search and recommendation system using MCP and RAG.

**Features**:
- Semantic search over HuggingFace models
- MCP server with 4 tools
- Dual retrieval modes (MCP + file_search)
- FAISS vector store integration

**Quick Start**:
```bash
cd experiments/redhatai_validated_models
python scripts/ingest_with_direct_vector_io.py
python -m src.mcp_server.server
python scripts/cli/cli_client.py
```

### Conversational AI
**Location**: [`conversational_ai_llamastack/`](./conversational_ai_llamastack/)

Conversational AI examples with Llama Stack.

## 📁 Available Setups

### Ollama Setup
Complete setup for running Llama Stack with Ollama.

**Location**: [`ollama-setup/`](./ollama-setup/)

**Quick Start**:
```bash
# Install dependencies
./experiments/ollama-setup/install-deps.sh

# Run the stack
./experiments/ollama-setup/run-ollama-stack.sh
```

**Documentation**:
- [Quick Start Guide](./ollama-setup/QUICKSTART.md)
- [Migration Guide](./ollama-setup/MIGRATION-GUIDE.md)
- [Main README](./ollama-setup/README.md)

## 🔧 Other Files

- `ollama-stack-build.yaml` - Build configuration (for Docker builds only)
- `rag_utils.py` - Utilities for RAG implementations
- `server.py` - Example server implementation
- `tool-calling-comparison.md` - Comparison of tool calling approaches

## 📚 Learn More

For more information about Llama Stack distributions, see:
- [Llama Stack Distributions](../llama_stack/distributions/)
- [Building Custom Distributions](../docs/docs/distributions/building_distro.mdx)

## 🎓 Learning Path

**Beginner**:
1. Start with `0-check-models.py` to verify your setup
2. Try `1-simpleclient.py` for basic usage
3. Explore `3-responses-function-tools.py` for tool calling

**Intermediate**:
4. Learn RAG with `2-rag.py`
5. Try MCP integration with `4-mcp-with-responses.py`
6. Run evals with `7-agentic-tools-with-llama-stack-evals.py` ⭐

**Advanced**:
7. Explore `redhatai_validated_models/` for production RAG+MCP
8. Use `telemetry/` tools for observability
9. Build custom integrations

## 🔍 Key Concepts Demonstrated

- **Agentic AI**: Tool calling, function execution, MCP integration
- **RAG**: Vector stores, semantic search, retrieval
- **Evaluation**: Automated testing, metrics, reporting
- **Observability**: Telemetry, tracing, OpenTelemetry export
- **Safety**: Content moderation, safety checks
- **HuggingFace Integration**: Open source models, model cards

