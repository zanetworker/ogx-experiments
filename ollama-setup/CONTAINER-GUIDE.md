# Running Llama Stack in Containers (Docker/Podman)

This guide shows how to build and run your Llama Stack configuration in a container using Docker or Podman.

## 🎯 Two Approaches

### Approach 1: Use Your Custom Config File (Recommended)
Build a container with your custom `ollama-stack-run.yaml` configuration.

### Approach 2: Use a Pre-built Distribution
Build using one of the standard distributions (e.g., `starter`, `ollama`).

---

## 📦 Approach 1: Custom Config Container

This approach bundles your `ollama-stack-run.yaml` into the container.

### Step 1: Build the Container Image

From the repository root:

**With Docker:**
```bash
docker build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg RUN_CONFIG_PATH=/app/config/ollama-stack-run.yaml \
  --tag llama-stack:ollama-custom \
  --build-context config=experiments/ollama-setup
```

**With Podman:**
```bash
podman build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg RUN_CONFIG_PATH=/app/config/ollama-stack-run.yaml \
  --tag llama-stack:ollama-custom \
  --build-context config=experiments/ollama-setup
```

**Build Arguments Explained:**
- `DISTRO_NAME=starter` - Uses starter distribution dependencies
- `RUN_CONFIG_PATH=/app/config/ollama-stack-run.yaml` - Path to config inside container
- `--build-context config=experiments/ollama-setup` - Mounts your config directory during build

### Step 2: Run the Container

**With Docker:**
```bash
docker run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e BRAVE_SEARCH_API_KEY="${BRAVE_SEARCH_API_KEY}" \
  -e TAVILY_SEARCH_API_KEY="${TAVILY_SEARCH_API_KEY}" \
  llama-stack:ollama-custom \
  --port 8321
```

**With Podman:**
```bash
podman run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.containers.internal:11434 \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e BRAVE_SEARCH_API_KEY="${BRAVE_SEARCH_API_KEY}" \
  -e TAVILY_SEARCH_API_KEY="${TAVILY_SEARCH_API_KEY}" \
  llama-stack:ollama-custom \
  --port 8321
```

**Important Differences:**
- Docker uses `host.docker.internal` to access host services
- Podman < 4.7.0 uses `host.containers.internal`
- Podman >= 4.7.0 supports `host.docker.internal`

---

## 📦 Approach 2: Standard Distribution Container

Build using a standard distribution without custom config.

### Step 1: Build the Container Image

**With Docker:**
```bash
docker build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --tag llama-stack:starter
```

**With Podman:**
```bash
podman build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --tag llama-stack:starter
```

### Step 2: Run with Mounted Config

**With Docker:**
```bash
docker run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -v $(pwd)/experiments/ollama-setup/ollama-stack-run.yaml:/app/config.yaml \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  llama-stack:starter \
  /app/config.yaml --port 8321
```

**With Podman:**
```bash
podman run -d \
  --name llama-stack-ollama \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -v $(pwd)/experiments/ollama-setup/ollama-stack-run.yaml:/app/config.yaml \
  -e OLLAMA_URL=http://host.containers.internal:11434 \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  llama-stack:starter \
  /app/config.yaml --port 8321
```

---

## 🔧 Build Arguments Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `DISTRO_NAME` | `starter` | Distribution name (determines dependencies) |
| `RUN_CONFIG_PATH` | - | Path to config file inside container |
| `INSTALL_MODE` | `pypi` | Installation mode: `pypi`, `editable`, `test-pypi` |
| `BASE_IMAGE` | `python:3.12-slim` | Base container image |
| `PYPI_VERSION` | - | Specific llama-stack version to install |

### Example: Build with Specific Version

```bash
docker build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg PYPI_VERSION=0.1.0 \
  --tag llama-stack:starter-v0.1.0
```

---

## 🌐 Networking: Accessing Ollama from Container

### Option 1: Use Host Network (Linux only)

**Docker:**
```bash
docker run -d \
  --network host \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://localhost:11434 \
  llama-stack:ollama-custom
```

**Podman:**
```bash
podman run -d \
  --network host \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://localhost:11434 \
  llama-stack:ollama-custom
```

### Option 2: Use Host Gateway (Cross-platform)

**Docker (macOS/Windows/Linux):**
```bash
docker run -d \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  llama-stack:ollama-custom
```

**Podman:**
```bash
podman run -d \
  -p 8321:8321 \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL=http://host.containers.internal:11434 \
  llama-stack:ollama-custom
```

### Option 3: Run Ollama in Container Too

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

---

## 🛠️ Container Management

### Check Container Status

**Docker:**
```bash
docker ps -a | grep llama-stack
docker logs llama-stack-ollama
docker logs -f llama-stack-ollama  # Follow logs
```

**Podman:**
```bash
podman ps -a | grep llama-stack
podman logs llama-stack-ollama
podman logs -f llama-stack-ollama  # Follow logs
```

### Stop and Remove Container

**Docker:**
```bash
docker stop llama-stack-ollama
docker rm llama-stack-ollama
```

**Podman:**
```bash
podman stop llama-stack-ollama
podman rm llama-stack-ollama
```

### Restart Container

**Docker:**
```bash
docker restart llama-stack-ollama
```

**Podman:**
```bash
podman restart llama-stack-ollama
```

### Execute Commands in Running Container

**Docker:**
```bash
docker exec -it llama-stack-ollama bash
docker exec llama-stack-ollama llama stack list-providers
```

**Podman:**
```bash
podman exec -it llama-stack-ollama bash
podman exec llama-stack-ollama llama stack list-providers
```

---

## 🧪 Testing the Container

### Health Check

```bash
curl http://localhost:8321/health
```

### List Models

```bash
curl http://localhost:8321/models/list
```

### Test Inference

```bash
curl -X POST http://localhost:8321/inference/chat_completion \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "meta-llama/Llama-3.2-3B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 📝 Complete Example Script

Create a script `run-container.sh`:

```bash
#!/bin/bash
# Run Llama Stack in container with Ollama

# Configuration
CONTAINER_TOOL="${CONTAINER_TOOL:-docker}"  # or podman
IMAGE_NAME="llama-stack:ollama-custom"
CONTAINER_NAME="llama-stack-ollama"
PORT=8321

# Detect host gateway based on container tool
if [ "$CONTAINER_TOOL" = "podman" ]; then
    HOST_GATEWAY="host.containers.internal"
else
    HOST_GATEWAY="host.docker.internal"
fi

# Build the image
echo "Building container image..."
$CONTAINER_TOOL build . \
  -f containers/Containerfile \
  --build-arg DISTRO_NAME=starter \
  --build-arg RUN_CONFIG_PATH=/app/config/ollama-stack-run.yaml \
  --tag "$IMAGE_NAME" \
  --build-context config=experiments/ollama-setup

# Stop and remove existing container
echo "Cleaning up existing container..."
$CONTAINER_TOOL stop "$CONTAINER_NAME" 2>/dev/null || true
$CONTAINER_TOOL rm "$CONTAINER_NAME" 2>/dev/null || true

# Run the container
echo "Starting container..."
$CONTAINER_TOOL run -d \
  --name "$CONTAINER_NAME" \
  -p $PORT:$PORT \
  -v ~/.llama:/root/.llama \
  -e OLLAMA_URL="http://$HOST_GATEWAY:11434" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
  -e BRAVE_SEARCH_API_KEY="${BRAVE_SEARCH_API_KEY}" \
  -e TAVILY_SEARCH_API_KEY="${TAVILY_SEARCH_API_KEY}" \
  "$IMAGE_NAME" \
  --port $PORT

# Wait for container to be ready
echo "Waiting for container to start..."
for i in {1..30}; do
    if curl -s http://localhost:$PORT/health 2>/dev/null | grep -q "OK"; then
        echo "✅ Container started successfully!"
        echo "URL: http://localhost:$PORT"
        exit 0
    fi
    sleep 1
done

echo "❌ Container failed to start"
echo "Logs:"
$CONTAINER_TOOL logs "$CONTAINER_NAME"
exit 1
```

Make it executable and run:
```bash
chmod +x run-container.sh
./run-container.sh
```

---

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs
docker logs llama-stack-ollama

# Check if port is already in use
lsof -i :8321
```

### Can't connect to Ollama
```bash
# Test from inside container
docker exec llama-stack-ollama curl http://host.docker.internal:11434/api/tags

# Verify Ollama is running on host
curl http://localhost:11434/api/tags
```

### Permission issues with volumes
```bash
# Fix permissions on .llama directory
chmod -R 755 ~/.llama
```

---

## 📊 Comparison: Direct vs Container

| Aspect | Direct Run | Container |
|--------|-----------|-----------|
| **Setup** | Virtual environment | Container image |
| **Isolation** | Process-level | Full OS-level |
| **Portability** | Platform-dependent | Cross-platform |
| **Updates** | `pip install -U` | Rebuild image |
| **Debugging** | Direct access | Via exec/logs |
| **Performance** | Native | Near-native |

---

## 🎯 Recommendations

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

**Next Steps:**
- See [README.md](README.md) for direct run instructions
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- See [MIGRATION-GUIDE.md](MIGRATION-GUIDE.md) for configuration details

