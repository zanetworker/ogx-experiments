# V2 Format Migration Summary

## ✅ Configuration Updated to v2 Format

The `ollama-stack-run.yaml` file has been completely rewritten to follow the StackRunConfig v2 schema.

## Key Changes Summary

### 1. Centralized Storage Configuration ⭐ MAJOR CHANGE

**Old (v1)**: Each provider had its own database configuration
```yaml
providers:
  vector_io:
  - config:
      kvstore:
        type: sqlite
        db_path: ~/.llama/.../faiss_store.db
```

**New (v2)**: Centralized storage with reusable backends
```yaml
storage:
  backends:
    kv_default:
      type: kv_sqlite
      db_path: ~/.llama/distributions/distribution-myenv-ollama/kvstore.db
    sql_default:
      type: sql_sqlite
      db_path: ~/.llama/distributions/distribution-myenv-ollama/sql_store.db

providers:
  vector_io:
  - config:
      persistence:
        namespace: vector_io::faiss
        backend: kv_default  # References the backend above
```

### 2. Provider Persistence Format

**All providers now use `persistence` instead of `kvstore`, `persistence_store`, etc.**

| Provider | Old Format | New Format |
|----------|-----------|------------|
| FAISS | `kvstore: {...}` | `persistence: {namespace, backend}` |
| Agents | `persistence_store: {...}` | `persistence: {agent_state, responses}` |
| Eval | `kvstore: {...}` | `persistence: {namespace, backend}` |
| DatasetIO | `kvstore: {...}` | `persistence: {namespace, backend}` |
| Files | `metadata_store: {...}` | `metadata_store: {table_name, backend}` |

### 3. Conditional Provider Activation

Providers are now only enabled when their API keys are set:

```yaml
# Only enabled if OPENAI_API_KEY is set
- provider_id: ${env.OPENAI_API_KEY:+openai}
  provider_type: remote::openai
  config:
    api_key: ${env.OPENAI_API_KEY:=}

# Only enabled if TAVILY_SEARCH_API_KEY is set
- provider_id: ${env.TAVILY_SEARCH_API_KEY:+tavily-search}
  provider_type: remote::tavily-search
  config:
    api_key: ${env.TAVILY_SEARCH_API_KEY:=}
```

**Benefits**:
- No errors when API keys are missing
- Cleaner provider list
- Automatic provider discovery based on environment

### 4. Registered Resources Structure

**Old**: Flat at root level
```yaml
models: []
shields: []
datasets: []
```

**New**: Nested under `registered_resources`
```yaml
registered_resources:
  models: []
  shields: []
  vector_dbs: []
  datasets: []
  scoring_fns: []
  benchmarks: []
  tool_groups: []
```

### 5. Server Configuration

**Old**: Invalid or missing
```yaml
server:
  port: 8321
  host: ["::", "0.0.0.0"]  # ❌ Invalid - list not allowed
```

**New**: Clean with env var support
```yaml
server:
  port: ${env.LLAMA_STACK_PORT:=8321}
```

### 6. Telemetry Configuration

**Old**: Invalid fields
```yaml
telemetry:
  enabled: true
  service_name: llama-stack  # ❌ Not in schema
  sinks: console,sqlite      # ❌ Not in schema
```

**New**: Schema-compliant
```yaml
telemetry:
  enabled: true
```

Use OpenTelemetry env vars for detailed config:
```bash
export OTEL_SERVICE_NAME=llama-stack
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
```

## Complete Provider List

### Always Enabled
- ✅ Ollama (inference)
- ✅ FAISS (vector_io)
- ✅ Llama Guard (safety)
- ✅ Meta Reference (agents, eval)
- ✅ Hugging Face (datasetio)
- ✅ LocalFS (datasetio, files)
- ✅ Basic Scoring
- ✅ LLM-as-Judge Scoring
- ✅ RAG Runtime (tool_runtime)
- ✅ Model Context Protocol (tool_runtime)

### Conditionally Enabled (require env vars)
- 🔑 OpenAI (requires `OPENAI_API_KEY`)
- 🔑 Braintrust (requires `OPENAI_API_KEY`)
- 🔑 Brave Search (requires `BRAVE_SEARCH_API_KEY`)
- 🔑 Tavily Search (requires `TAVILY_SEARCH_API_KEY`)

## Tool Groups

### Built-in Tools (no registration needed)
- ✅ **RAG Tools** - `builtin::rag/*`
  - `builtin::rag/knowledge_search` - Search vector databases
  - `builtin::rag/insert` - Insert documents into vector databases
  - No provider or tool group registration required
  - Use directly in agent tools configuration

### Registered Tool Groups
- Currently: None (empty list)
- Can manually add websearch if needed (requires API key)

## Storage Backends

### KV Store (kv_default)
- **Type**: SQLite
- **Path**: `~/.llama/distributions/distribution-myenv-ollama/kvstore.db`
- **Used by**:
  - Vector I/O (FAISS)
  - Agents (agent state)
  - Eval
  - DatasetIO (Hugging Face, LocalFS)
  - Metadata registry

### SQL Store (sql_default)
- **Type**: SQLite
- **Path**: `~/.llama/distributions/distribution-myenv-ollama/sql_store.db`
- **Used by**:
  - Agents (responses)
  - Files (metadata)
  - Inference store
  - Conversations

## Environment Variables

### Required
```bash
export OLLAMA_URL="http://localhost:11434"  # Ollama server URL
```

### Optional
```bash
export LLAMA_STACK_PORT=8321                # Server port (default: 8321)
export OPENAI_API_KEY="sk-..."             # Enable OpenAI provider
export BRAVE_SEARCH_API_KEY="..."          # Enable Brave Search
export TAVILY_SEARCH_API_KEY="..."         # Enable Tavily Search
export FILES_STORAGE_DIR="~/.llama/files"  # Files storage location
export SQLITE_STORE_DIR="~/.llama/..."     # SQLite database directory
```

### OpenTelemetry (for telemetry)
```bash
export OTEL_SERVICE_NAME=llama-stack
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_TRACES_EXPORTER=otlp
```

## Migration Checklist

- [x] Updated version to integer `2`
- [x] Added centralized `storage` configuration
- [x] Converted all provider persistence to use backend references
- [x] Moved resources under `registered_resources`
- [x] Fixed server configuration
- [x] Fixed telemetry configuration
- [x] Added conditional provider activation
- [x] Removed invalid fields
- [x] Updated environment variable patterns

## Testing

To test the configuration:

```bash
# Make sure you're in the correct virtual environment
source /path/to/llamastack/bin/activate

# Set required environment variables
export OLLAMA_URL="http://localhost:11434"

# Run the stack
./experiments/ollama-setup/run-ollama-stack.sh
```

Expected output:
```
=== Running Llama Stack with Ollama ===
Python: /path/to/llamastack/bin/python
Config file: /path/to/ollama-stack-run.yaml
...
INFO:     Application startup complete.
INFO:     Uvicorn running on http://['::', '0.0.0.0']:8321
```

## Troubleshooting

### "Module not found" errors
```bash
# Install dependencies
./experiments/ollama-setup/install-deps.sh
```

### "Provider not found" errors
Check that required environment variables are set for conditional providers.

### Storage errors
Make sure the directory exists:
```bash
mkdir -p ~/.llama/distributions/distribution-myenv-ollama
```

## References

- [StackRunConfig Schema](../../llama_stack/core/datatypes.py)
- [Storage Configuration](../../llama_stack/core/storage/datatypes.py)
- [Starter Distribution Example](../../llama_stack/distributions/starter/run.yaml)

