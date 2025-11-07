# Llama Stack with Ollama Setup

> ✅ **Status**: Working with v2 configuration format
> 📅 **Last Updated**: 2024-11-07

Complete guide for running Llama Stack with Ollama, including direct execution and containerized deployment.

---

## 📁 Files in This Directory

### Configuration
- **`ollama-stack-run.yaml`** - Main v2 format configuration file

### Scripts
- **`run-ollama-stack.sh`** - Convenience script to run the stack
- **`clean-and-restart.sh`** - Clean databases and restart

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with uv package manager
2. **Ollama** running locally or accessible via network

### Installation

```bash
# 1. Sync dependencies with uv
uv sync --all-groups
# or simply: uv sync

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Set environment variables (optional)
export OLLAMA_URL="http://localhost:11434"
export LLAMA_STACK_PORT=8321

# 4. Run the stack
./experiments/ollama-setup/run-ollama-stack.sh
```

### Verify It's Running

```bash
# Health check
curl http://localhost:8321/health

# List models
curl http://localhost:8321/models/list

# Test inference
curl -X POST http://localhost:8321/inference/chat_completion \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🐳 Running in Containers (Podman/Docker)

### Build Container with Custom Config

**Podman:**
```bash
# From the llama-stack repository root
cd /path/to/llama-stack

podman build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg RUN_CONFIG_PATH=/workspace/experiments/ollama-setup/ollama-stack-run.yaml \
  --tag llama-stack:ollama-custom
```

**Docker:**
```bash
# From the llama-stack repository root
cd /path/to/llama-stack

docker build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg RUN_CONFIG_PATH=/workspace/experiments/ollama-setup/ollama-stack-run.yaml \
  --tag llama-stack:ollama-custom
```

**Note:** The build context is the repository root (`.`), and the config file path is `/workspace/experiments/ollama-setup/ollama-stack-run.yaml` because the Containerfile copies the entire repo to `/workspace`.

### Run the Container

**Podman:**
```bash
podman run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.containers.internal:11434 \
  -e OPENAI_API_KEY="sk-..." \
  llama-stack:ollama-custom \
  --port 8321
```

**Docker:**
```bash
docker run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -e OPENAI_API_KEY="sk-..." \
  llama-stack:ollama-custom \
  --port 8321
```

**Important:** 
- Podman uses `host.containers.internal` to access host services
- Docker uses `host.docker.internal` to access host services
- Podman >= 4.7.0 also supports `host.docker.internal`

### Container Networking Options

#### Option 1: Host Network (Linux only)

**Podman:**
```bash
podman run -d \
  --network host \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://localhost:11434 \
  llama-stack:ollama-custom
```

**Docker:**
```bash
docker run -d \
  --network host \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://localhost:11434 \
  llama-stack:ollama-custom
```

#### Option 2: Run Ollama in Container Too

**Podman:**
```bash
# Start Ollama container
podman run -d --name ollama -p 11434:11434 ollama/ollama

# Start Llama Stack container
podman run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://ollama:11434 \
  --pod new:llama-pod \
  llama-stack:ollama-custom
```

**Docker:**
```bash
# Start Ollama container
docker run -d --name ollama -p 11434:11434 ollama/ollama

# Start Llama Stack container linked to Ollama
docker run -d \
  --name llama-stack-ollama \
  --link ollama:ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://ollama:11434 \
  llama-stack:ollama-custom
```

### Container Management

**Podman:**
```bash
# Check logs
podman logs -f llama-stack-ollama

# Stop and remove
podman stop llama-stack-ollama
podman rm llama-stack-ollama

# Execute commands
podman exec -it llama-stack-ollama bash
```

**Docker:**
```bash
# Check logs
docker logs -f llama-stack-ollama

# Stop and remove
docker stop llama-stack-ollama
docker rm llama-stack-ollama

# Execute commands
docker exec -it llama-stack-ollama bash
```

---

## 🔧 Troubleshooting

### Quick Diagnostics

```bash
# Verify virtual environment
which python
# Should show: .venv/bin/python

# Check Python version
python --version
# Should be Python 3.11+

# Verify llama-stack is installed
python -c "import llama_stack; print(llama_stack.__file__)"

# Validate configuration
python -c "import yaml; yaml.safe_load(open('experiments/ollama-setup/ollama-stack-run.yaml'))"
```

### Common Errors

#### 1. ModuleNotFoundError: No module named 'llama_stack_client'

**Solution:**
```bash
source .venv/bin/activate
uv sync --all-groups
```

#### 2. ValidationError: Field required - kvstore

**Cause:** Wrong field name for provider storage configuration

**Solution:** Use correct field names:
- `eval`, `datasetio`, `batches` → `kvstore`
- `vector_io`, `agents` → `persistence`
- `files` → `metadata_store`

```yaml
# ✅ CORRECT
eval:
- provider_id: meta-reference
  config:
    kvstore:  # Not 'persistence'
      namespace: eval
      backend: kv_default
```

#### 3. Provider 'rag-runtime' Not Available

**Cause:** Trying to register RAG as a tool runtime provider

**Solution:** Remove rag-runtime provider - RAG is built-in:
```yaml
# ✅ CORRECT - RAG doesn't need a provider
tool_runtime:
- provider_id: brave-search
  provider_type: remote::brave-search
# RAG tools are automatically available
```

#### 4. Input Tag 'vector_db' Does Not Match

**Cause:** Old database files with deprecated v1 schema

**Solution:**
```bash
rm -rf ~/.llama/distributions/distribution-myenv-ollama/*.db
./experiments/ollama-setup/run-ollama-stack.sh
```

#### 5. Ollama Connection Refused

**Solution:**
```bash
# Start Ollama
ollama serve

# Or with Podman
podman run -d -p 11434:11434 ollama/ollama

# Or with Docker
docker run -d -p 11434:11434 ollama/ollama

# Verify
curl http://localhost:11434/api/tags
```

#### 6. Port Already in Use

**Solution:**
```bash
# Find what's using the port
lsof -i :8321

# Kill the process
kill -9 <PID>

# Or use different port
export LLAMA_STACK_PORT=5000
./experiments/ollama-setup/run-ollama-stack.sh
```

#### 7. Container Can't Access Host Ollama

**Podman Solution:**
```bash
# Check Podman version
podman --version

# For Podman < 4.7.0, use:
-e OLLAMA_URL=http://host.containers.internal:11434

# For Podman >= 4.7.0, you can also use:
-e OLLAMA_URL=http://host.docker.internal:11434

# Test from inside container
podman exec llama-stack-ollama curl http://host.containers.internal:11434/api/tags
```

**Docker Solution:**
```bash
# Use host.docker.internal
-e OLLAMA_URL=http://host.docker.internal:11434

# Test from inside container
docker exec llama-stack-ollama curl http://host.docker.internal:11434/api/tags
```

### Debugging Tips

#### Enable Debug Logging
```bash
export LOG_LEVEL=DEBUG
./experiments/ollama-setup/run-ollama-stack.sh
```

#### Validate Configuration
```bash
python -c "
import yaml
with open('experiments/ollama-setup/ollama-stack-run.yaml') as f:
    config = yaml.safe_load(f)
    print('✅ YAML is valid')
    print(f'APIs: {config.get(\"apis\", [])}')
    print(f'Providers: {list(config.get(\"providers\", {}).keys())}')
"
```

#### Check Storage Backends
```bash
python -c "
import yaml
with open('experiments/ollama-setup/ollama-stack-run.yaml') as f:
    config = yaml.safe_load(f)
    backends = config.get('storage', {}).get('backends', {})
    print('Storage backends:')
    for name, backend in backends.items():
        print(f'  {name}: {backend.get(\"type\")} -> {backend.get(\"db_path\")}')
"
```

#### Test Components
```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test Llama Stack health
curl http://localhost:8321/health

# List models
curl http://localhost:8321/models/list
```

---

## 📋 Configuration Checklist

Before running, verify your configuration has:

- [ ] `version: 2` at the top
- [ ] Centralized `storage.backends` section
- [ ] Correct field names for each provider type
- [ ] No `inline::rag-runtime` provider
- [ ] Empty `tool_groups: []` or valid tool groups
- [ ] Valid environment variable syntax
- [ ] Proper namespace prefixes (e.g., `datasetio::huggingface`)
- [ ] Backend references match defined backend names

---

## 🔄 Clean Restart

If you encounter persistent issues:

```bash
# Use the clean restart script
./experiments/ollama-setup/clean-and-restart.sh

# Or manually
rm -rf ~/.llama/distributions/distribution-myenv-ollama/*.db
./experiments/ollama-setup/run-ollama-stack.sh
```

---

## 📊 Direct vs Container Comparison

| Aspect | Direct Run | Container |
|--------|-----------|-----------|
| **Setup** | uv + .venv | Container image |
| **Isolation** | Process-level | Full OS-level |
| **Portability** | Platform-dependent | Cross-platform |
| **Updates** | `uv sync` | Rebuild image |
| **Debugging** | Direct access | Via exec/logs |
| **Performance** | Native | Near-native |

**Use Direct Run when:**
- Developing/debugging
- Frequent config changes
- Need direct file access

**Use Containers when:**
- Production deployment
- Need isolation
- Multiple environments
- CI/CD pipelines

---

## 🎯 Environment Variables

The configuration supports these environment variables:

```bash
# Ollama connection
export OLLAMA_URL="http://localhost:11434"

# Server port
export LLAMA_STACK_PORT=8321

# Optional API keys
export OPENAI_API_KEY="sk-..."
export BRAVE_SEARCH_API_KEY="..."
export TAVILY_SEARCH_API_KEY="..."
```

---

## 📚 Additional Resources

- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Podman Documentation](https://docs.podman.io/)
- Configuration reference: `ollama-stack-run.yaml`

---

## 🆘 Getting Help

If you're still stuck:

1. **Check the logs** - Look for the first error in the stack trace
2. **Verify the basics** - Python environment, Ollama running, ports available
3. **Clean slate** - Remove databases and try again
4. **Simplify** - Start with minimal configuration and add providers incrementally
