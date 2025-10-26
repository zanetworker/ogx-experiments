# Llama Stack Configuration Migration Guide

## Overview

This guide documents the complete migration from the deprecated two-step workflow (`llama stack build` + `llama stack run`) to the new simplified single-step workflow using only `llama stack run` with a v2 format configuration file.

## What Changed

### Old Workflow (Deprecated)
```bash
# Step 1: Build a distribution
llama stack build --template ollama --image-type conda

# Step 2: Run the distribution
llama stack run distribution-myenv-ollama
```

### New Workflow (Current)
```bash
# Single step: Run with configuration file
llama stack run experiments/ollama-setup/ollama-stack-run.yaml --port 5000
```

## Key Migration Steps

### 1. Configuration Format: v1 → v2

The biggest change is the configuration file structure. v2 introduces **centralized storage backends** instead of per-provider database configurations.

#### v1 Format (Old)
```yaml
providers:
  vector_io:
  - provider_id: faiss
    config:
      # Each provider had its own database config
      kvstore:
        type: sqlite
        db_path: ~/.llama/vector_store.db
        namespace: faiss
```

#### v2 Format (New)
```yaml
# Centralized storage backends
storage:
  backends:
    kv_default:
      type: kv_sqlite
      db_path: ~/.llama/distributions/distribution-myenv-ollama/kvstore.db
    sql_default:
      type: sql_sqlite
      db_path: ~/.llama/distributions/distribution-myenv-ollama/sql_store.db

# Providers reference the backends
providers:
  vector_io:
  - provider_id: faiss
    config:
      persistence:
        namespace: vector_io::faiss
        backend: kv_default  # Reference to centralized backend
```

### 2. Storage Field Names by Provider

Different providers use different field names for storage configuration:

| Provider API | Field Name | Structure |
|-------------|------------|-----------|
| `datasetio` | `kvstore` | `{namespace, backend}` |
| `eval` | `kvstore` | `{namespace, backend}` |
| `batches` | `kvstore` | `{namespace, backend}` |
| `vector_io` | `persistence` | `{namespace, backend}` |
| `agents` | `persistence` | `{agent_state: {namespace, backend}, responses: {table_name, backend}}` |
| `files` | `metadata_store` | `{table_name, backend}` |

### 3. Registered Resources

Resources are now nested under `registered_resources`:

```yaml
registered_resources:
  models:
  - model_id: all-MiniLM-L6-v2
    provider_id: ollama
    provider_model_id: all-minilm:latest
    model_type: embedding
    metadata:
      embedding_dimension: 384
  
  shields: []
  vector_dbs: []
  datasets: []
  scoring_fns: []
  benchmarks: []
  tool_groups: []
```

### 4. Tool Groups vs Tool Runtime

**Important distinction**:
- **Tool Runtime Providers**: Register external tool providers (Brave Search, Tavily, MCP)
- **Tool Groups**: Register collections of tools (optional, RAG is built-in)

```yaml
# Tool runtime providers
tool_runtime:
- provider_id: brave-search
  provider_type: remote::brave-search
  config:
    api_key: ${env.BRAVE_SEARCH_API_KEY:=}

# Tool groups (usually empty - RAG is built-in)
registered_resources:
  tool_groups: []
```

**Common mistake**: Don't create a `rag-runtime` provider - RAG tools are built-in!

### 5. Environment Variable Syntax

v2 supports advanced environment variable substitution:

```yaml
# Default value
url: ${env.OLLAMA_URL:=http://localhost:11434}

# Conditional provider (only enabled if env var is set)
provider_id: ${env.OPENAI_API_KEY:+openai}

# Required value (no default)
api_key: ${env.BRAVE_SEARCH_API_KEY}
```

### 6. Server Configuration

Simplified server configuration:

```yaml
server:
  port: ${env.LLAMA_STACK_PORT:=8321}
  # host is optional, defaults to None (all interfaces)
```

### 7. Telemetry Configuration

Simplified to just an enabled flag:

```yaml
telemetry:
  enabled: true
```

## Common Migration Issues & Solutions

### Issue 1: Field Name Errors

**Error**: `Field required [type=missing, input_value={'persistence': ...}]`

**Cause**: Using wrong field name for storage configuration

**Solution**: Check the field name reference table above and use the correct field name for each provider type.

### Issue 2: Invalid RAG Runtime Provider

**Error**: `Provider 'inline::rag-runtime' is not available for API 'Api.tool_runtime'`

**Cause**: Trying to register RAG as a tool runtime provider

**Solution**: Remove any `rag-runtime` provider. RAG is a built-in tool group and doesn't need registration.

### Issue 3: Conditional Provider ID in Tool Groups

**Error**: `Input should be a valid string [type=string_type, input_value=None]`

**Cause**: Using conditional syntax like `${env.VAR:+value}` in tool_groups provider_id

**Solution**: Either use a fixed provider_id or set `tool_groups: []`

### Issue 4: Stale Database with Old Schema

**Error**: `Input tag 'vector_db' found using 'type' does not match any of the expected tags`

**Cause**: Old database files with deprecated schema (v1 used `vector_db`, v2 uses `vector_store`)

**Solution**: Clean up old databases:
```bash
rm -rf ~/.llama/distributions/distribution-myenv-ollama/*.db
```

### Issue 5: Server Host Validation

**Error**: `Input should be a valid string [type=string_type, input_value=['::', '0.0.0.0']]`

**Cause**: Using list format for host

**Solution**: Remove the host field or set to None:
```yaml
server:
  port: 8321
  # host field removed - defaults to None
```

## Complete v2 Configuration Template

See `experiments/ollama-setup/ollama-stack-run.yaml` for a complete working example with:

- ✅ Centralized storage backends (KV and SQL)
- ✅ All provider types with correct field names
- ✅ Conditional provider activation
- ✅ Environment variable substitution
- ✅ Registered resources
- ✅ Proper namespace organization

## Running the Migrated Configuration

### Prerequisites

1. **Activate virtual environment**:
   ```bash
   source ~/.pyenv/versions/3.11/envs/llamastack/bin/activate
   ```

2. **Verify Python environment**:
   ```bash
   which python
   # Should show: /path/to/llamastack/bin/python
   ```

3. **Set environment variables** (optional):
   ```bash
   export OLLAMA_URL="http://localhost:11434"
   export LLAMA_STACK_PORT=5000
   export OPENAI_API_KEY="sk-..."  # Optional
   export BRAVE_SEARCH_API_KEY="..."  # Optional
   export TAVILY_SEARCH_API_KEY="..."  # Optional
   ```

### Run the Stack

**Option 1: Using the convenience script**
```bash
./experiments/ollama-setup/run-ollama-stack.sh
```

**Option 2: Direct command**
```bash
python -m llama_stack.cli.llama stack run \
  experiments/ollama-setup/ollama-stack-run.yaml \
  --port 5000
```

### Verify It's Running

```bash
# Check the health endpoint
curl http://localhost:5000/health

# List available models
curl http://localhost:5000/models/list
```

## Understanding Namespaces

The `namespace` field in storage configuration is a **key prefix** used for data isolation:

```
Database: ~/.llama/distributions/distribution-myenv-ollama/kvstore.db
├── Keys: "datasetio::huggingface::*" → Hugging Face provider data
├── Keys: "datasetio::localfs::*" → LocalFS provider data  
├── Keys: "vector_io::faiss::*" → FAISS provider data
├── Keys: "registry::*" → Metadata registry
└── Keys: "eval::*" → Eval provider data
```

**Benefits**:
- Multiple providers can share one database file
- Easy cleanup (delete all keys with a prefix)
- Clear data ownership for debugging

## Additional Resources

- **`FIXES.md`** - Detailed technical documentation of all fixes applied
- **`V2-FORMAT-CHANGES.md`** - Complete v2 format reference
- **`QUICKSTART.md`** - Quick reference guide
- **`README.md`** - Main documentation

## Summary

The migration from v1 to v2 configuration format brings:

1. **Simplified workflow** - No more `llama stack build` step
2. **Centralized storage** - Reusable backend definitions
3. **Better organization** - Clear separation of concerns
4. **Environment flexibility** - Advanced variable substitution
5. **Cleaner configuration** - Less duplication, more maintainable

The key is understanding:
- Which field name each provider uses for storage
- How to reference centralized backends
- That RAG is built-in (no provider needed)
- How to properly use environment variables

