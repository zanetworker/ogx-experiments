# Llama Stack Troubleshooting Guide

## Quick Diagnostics

### Check Your Environment

```bash
# 1. Verify you're in the correct virtual environment
which python
# Should show: /path/to/llamastack/bin/python

# 2. Check Python version
python --version
# Should be Python 3.11 or higher

# 3. Verify llama-stack is installed
python -c "import llama_stack; print(llama_stack.__file__)"

# 4. Check configuration file syntax
python -c "import yaml; yaml.safe_load(open('experiments/ollama-setup/ollama-stack-run.yaml'))"
```

## Common Errors & Solutions

### 1. ModuleNotFoundError: No module named 'llama_stack_client'

**Error**:
```
ModuleNotFoundError: No module named 'llama_stack_client'
```

**Cause**: Not in the correct virtual environment or missing dependency

**Solution**:
```bash
# Activate your virtual environment
source ~/.pyenv/versions/3.11/envs/llamastack/bin/activate

# Install missing package
pip install llama-stack-client
```

---

### 2. ValidationError: Field required - kvstore

**Error**:
```
pydantic_core._pydantic_core.ValidationError: 1 validation error for MetaReferenceEvalConfig
kvstore
  Field required [type=missing, input_value={'persistence': ...}]
```

**Cause**: Using wrong field name (`persistence` instead of `kvstore`) for eval/datasetio providers

**Solution**: Check your configuration uses the correct field names:

```yaml
# ✅ CORRECT
eval:
- provider_id: meta-reference
  config:
    kvstore:  # Not 'persistence'
      namespace: eval
      backend: kv_default

datasetio:
- provider_id: huggingface
  config:
    kvstore:  # Not 'persistence'
      namespace: datasetio::huggingface
      backend: kv_default
```

**Field Name Reference**:
- `eval` → `kvstore`
- `datasetio` → `kvstore`
- `batches` → `kvstore`
- `vector_io` → `persistence`
- `agents` → `persistence`
- `files` → `metadata_store`

---

### 3. Provider Not Available for API

**Error**:
```
ValueError: Provider `inline::rag-runtime` is not available for API `Api.tool_runtime`
```

**Cause**: Trying to register RAG as a tool runtime provider

**Solution**: Remove the rag-runtime provider. RAG is built-in:

```yaml
# ❌ WRONG - Don't do this
tool_runtime:
- provider_id: rag-runtime
  provider_type: inline::rag-runtime

# ✅ CORRECT - RAG doesn't need a provider
tool_runtime:
- provider_id: brave-search
  provider_type: remote::brave-search
# ... other tool providers

# RAG tools are automatically available
```

---

### 4. Input Tag 'vector_db' Does Not Match

**Error**:
```
Input tag 'vector_db' found using 'type' does not match any of the expected tags
```

**Cause**: Old database files with deprecated v1 schema

**Solution**: Clean up old databases:

```bash
# Remove old database files
rm -rf ~/.llama/distributions/distribution-myenv-ollama/*.db

# Run the stack again
./experiments/ollama-setup/run-ollama-stack.sh
```

---

### 5. Server Host Validation Error

**Error**:
```
Input should be a valid string [type=string_type, input_value=['::', '0.0.0.0'], input_type=list]
```

**Cause**: Using list format for server host

**Solution**: Remove or simplify server.host:

```yaml
# ✅ CORRECT
server:
  port: 8321
  # host field omitted - defaults to None (all interfaces)
```

---

### 6. Conditional Provider ID is None

**Error**:
```
Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]
```

**Cause**: Using conditional syntax in tool_groups when environment variable is not set

**Solution**: Use empty tool_groups or fixed provider_id:

```yaml
# ✅ CORRECT - Empty tool groups
registered_resources:
  tool_groups: []

# ❌ WRONG - Conditional provider_id
registered_resources:
  tool_groups:
  - toolgroup_id: builtin::websearch
    provider_id: ${env.TAVILY_SEARCH_API_KEY:+tavily-search}  # Evaluates to None if not set
```

---

### 7. Ollama Connection Refused

**Error**:
```
ConnectionRefusedError: [Errno 61] Connection refused
```

**Cause**: Ollama is not running

**Solution**:
```bash
# Start Ollama
ollama serve

# Or if using Docker
docker run -d -p 11434:11434 ollama/ollama

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

---

### 8. Port Already in Use

**Error**:
```
OSError: [Errno 48] Address already in use
```

**Cause**: Another process is using the port

**Solution**:
```bash
# Find what's using the port
lsof -i :8321

# Kill the process
kill -9 <PID>

# Or use a different port
export LLAMA_STACK_PORT=5000
./experiments/ollama-setup/run-ollama-stack.sh
```

---

### 9. Configuration File Not Found

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'ollama-stack-run.yaml'
```

**Cause**: Running from wrong directory or incorrect path

**Solution**:
```bash
# Run from repository root
cd /Users/azaalouk/go/src/github.com/llama-stack

# Use absolute path
python -m llama_stack.cli.llama stack run \
  /Users/azaalouk/go/src/github.com/llama-stack/experiments/ollama-setup/ollama-stack-run.yaml
```

---

### 10. Environment Variable Not Substituted

**Error**: Configuration shows `${env.OLLAMA_URL:=http://localhost:11434}` literally

**Cause**: Environment variables are substituted at runtime by Llama Stack, not by shell

**Solution**: This is normal! The variables are substituted when the config is loaded. To override:

```bash
# Set before running
export OLLAMA_URL="http://custom-host:11434"
./experiments/ollama-setup/run-ollama-stack.sh
```

---

## Debugging Tips

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
./experiments/ollama-setup/run-ollama-stack.sh
```

### Validate Configuration

```bash
# Check YAML syntax
python -c "
import yaml
with open('experiments/ollama-setup/ollama-stack-run.yaml') as f:
    config = yaml.safe_load(f)
    print('✅ YAML is valid')
    print(f'APIs: {config.get(\"apis\", [])}')
    print(f'Providers: {list(config.get(\"providers\", {}).keys())}')
"
```

### Check Storage Backends

```bash
# Verify storage backend configuration
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

### Inspect Database Files

```bash
# List database files
ls -lh ~/.llama/distributions/distribution-myenv-ollama/

# Check database size
du -sh ~/.llama/distributions/distribution-myenv-ollama/*.db

# Query SQLite database (if sqlite3 installed)
sqlite3 ~/.llama/distributions/distribution-myenv-ollama/kvstore.db ".tables"
```

### Test Individual Components

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test Llama Stack health (after starting)
curl http://localhost:8321/health

# List models
curl http://localhost:8321/models/list
```

---

## Configuration Validation Checklist

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

## Getting Help

If you're still stuck:

1. **Check the logs**: Look for the first error in the stack trace
2. **Verify the basics**: Python environment, Ollama running, ports available
3. **Compare with reference**: Check `llama_stack/distributions/starter/run.yaml`
4. **Clean slate**: Remove databases and try again
5. **Simplify**: Start with minimal configuration and add providers incrementally

---

## Quick Reference Commands

```bash
# Clean start
rm -rf ~/.llama/distributions/distribution-myenv-ollama/*.db
./experiments/ollama-setup/run-ollama-stack.sh

# Check what's running
ps aux | grep llama
lsof -i :8321

# View logs with timestamps
./experiments/ollama-setup/run-ollama-stack.sh 2>&1 | ts

# Test configuration without starting server
python -c "
from llama_stack.core.configure import parse_and_maybe_upgrade_config
from pathlib import Path
config = parse_and_maybe_upgrade_config(Path('experiments/ollama-setup/ollama-stack-run.yaml'))
print('✅ Configuration is valid!')
"
```

