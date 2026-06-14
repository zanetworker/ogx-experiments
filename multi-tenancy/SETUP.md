# OGX Multi-Tenancy: Cluster Setup Guide

Step-by-step reproduction of the multi-tenancy validation performed on a RHOAI 3.5 EA2 cluster (OCP 4.20).

## Prerequisites

- OpenShift 4.20+ with RHOAI 3.5 EA2 installed
- `OGXServer` CRD available (`oc api-resources | grep ogxservers`)
- OGX operator running (`oc get pods -n redhat-ods-applications | grep ogx-k8s-operator`)
- An inference backend for chat (vLLM, MaaS, or OpenAI)
- An embedding model accessible via OpenAI-compatible API (bge-m3, text-embedding-3-small)

## What We Learned the Hard Way

Three things that are not obvious from the documentation and cost hours to discover:

### 1. `auth:` must go under `server:`, not at the top level

Every OGX distro config (starter, rh-dev, RHOAI) puts `auth:` at the top level of the YAML. But `StackConfig` expects it under `server.auth`. Pydantic silently ignores the top-level key. The server starts with no authentication and no error message.

```yaml
# WRONG (silently ignored, no auth enforced)
auth:
  provider_config:
    type: oauth2_token

# CORRECT
server:
  auth:
    provider_config:
      type: oauth2_token
```

### 2. Embedding models from proxies must be explicitly registered

The `remote::openai` provider classifies every unknown model as `llm`. If your embedding model (bge-m3, nomic-embed, e5-mistral) is served through MaaS, LiteLLM, or any OpenAI-compatible proxy, it will be misclassified and the server will crash at startup with "Available embedding models: []".

Fix: register the model explicitly in `registered_resources.models` with `model_type: embedding`:

```yaml
registered_resources:
  models:
    - model_id: bge-m3
      provider_id: maas-bge
      model_type: embedding
      metadata:
        embedding_dimension: 1024
```

### 3. JWKS endpoint needs auth on OpenShift

The Kubernetes OIDC JWKS endpoint (`/openid/v1/jwks`) requires authentication. The external API server URL (`https://api.cluster.../openid/v1/jwks`) returns 403 from inside the pod. Use the internal service URL with a SA token:

```yaml
server:
  auth:
    provider_config:
      jwks:
        uri: https://kubernetes.default.svc/openid/v1/jwks
        token: ${env.JWKS_TOKEN:=}
```

Then set `JWKS_TOKEN` as an env var on the deployment with a long-lived SA token.

## Understanding Models: registered_resources vs providers

OGX has two ways a model can appear in `/v1/models`. Understanding the difference is critical for multi-tenancy with proxies.

### Provider-listed models (dynamic)

When OGX starts, each inference provider calls its backend's `/v1/models` endpoint and lists whatever models it finds. These are "dynamic" models. The provider decides the `model_type` based on its own logic.

For the `remote::openai` provider, that logic is: check a hardcoded dict of known OpenAI embedding models. If the model ID is in the dict, type is `embedding`. Otherwise, type is `llm`.

```
Provider: maas-bge (remote::openai)
  └─ calls GET https://maas.../bge-m3/v1/models
  └─ gets back: [{id: "bge-m3"}]
  └─ checks hardcoded dict: "bge-m3" not found
  └─ classifies as: model_type=llm  ← WRONG
```

This works for OpenAI's own models but breaks for any third-party embedding model served through an OpenAI-compatible proxy.

### Config-registered models (static)

Models declared in `registered_resources.models` are registered at startup before providers list their dynamic models. You control the `model_type` explicitly:

```yaml
registered_resources:
  models:
    - model_id: bge-m3
      provider_id: maas-bge
      model_type: embedding          # YOU declare the type
      metadata:
        embedding_dimension: 1024    # YOU declare the dimensions
```

When both exist (same model ID from config AND from provider), the config-registered version takes precedence. This is how you override the provider's incorrect classification.

### When to use which

| Scenario | Use |
|----------|-----|
| Provider natively knows your models (local vLLM, OpenAI) | Provider-listed (automatic) |
| Embedding model behind a proxy (MaaS, LiteLLM, Azure) | `registered_resources.models` with `model_type: embedding` |
| Model not in any provider's listing | `registered_resources.models` (explicit registration) |
| Override model metadata (dimensions, type) | `registered_resources.models` (takes precedence) |

## Step 1: Create the OGXServer Config

Create a ConfigMap with the full config. Key sections annotated:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ogx-mt-demo-config
  namespace: redhat-ods-applications
  labels:
    ogx.io/watch: "true"    # Required for operator to detect changes
data:
  config.yaml: |
    version: 2
    distro_name: starter
    apis:
    - files
    - inference
    - interactions
    - messages
    - responses
    - tool_runtime
    - vector_io

    providers:
      inference:
      # Chat model via MaaS
      - provider_id: maas-llama
        provider_type: remote::openai
        config:
          api_key: <your-maas-api-key>
          base_url: https://maas.apps.<cluster-domain>/prelude-maas/llama-4-scout-17b-16e-w4a16/v1
      # Embedding model via MaaS
      - provider_id: maas-bge
        provider_type: remote::openai
        config:
          api_key: <your-maas-api-key>
          base_url: https://maas.apps.<cluster-domain>/prelude-maas/bge-m3/v1

      vector_io:
      - provider_id: sqlite-vec
        provider_type: inline::sqlite-vec
        config:
          db_path: ${env.SQLITE_STORE_DIR:=~/.ogx/distributions/starter}/sqlite_vec.db
          persistence:
            namespace: vector_io::sqlite_vec
            backend: kv_default

      files:
      - provider_id: builtin-files
        provider_type: inline::localfs
        config:
          storage_dir: ${env.FILES_STORAGE_DIR:=~/.ogx/distributions/starter/files}
          metadata_store:
            table_name: files_metadata
            backend: sql_default

      responses:
      - provider_id: builtin
        provider_type: inline::builtin
        config:
          persistence:
            responses:
              table_name: responses
              backend: sql_default

      tool_runtime:
      - provider_id: builtin-file-search
        provider_type: inline::file-search
        config: {}

    # Register bge-m3 explicitly as embedding type
    registered_resources:
      models:
      - model_id: bge-m3
        provider_id: maas-bge
        model_type: embedding
        metadata:
          embedding_dimension: 1024

    # Auth MUST be under server:, not at top level
    server:
      port: 8321
      auth:
        provider_config:
          type: ${env.AUTH_ISSUER:+oauth2_token}
          audience: ${env.AUTH_AUDIENCE:=ogx}
          issuer: ${env.AUTH_ISSUER:=}
          jwks:
            uri: https://kubernetes.default.svc/openid/v1/jwks
            token: ${env.JWKS_TOKEN:=}
          verify_tls: ${env.AUTH_VERIFY_TLS:=true}
        access_policy:
        - permit:
            actions: [read]
          when: resource is unowned
          description: "All users can read system resources"
        - permit:
            actions: [create]
          description: "Authenticated users can create resources"
        - permit:
            actions: [read, update, delete]
          when: user is owner
          description: "Owners can manage their own resources"

    vector_stores:
      default_provider_id: sqlite-vec
      default_embedding_model:
        provider_id: maas-bge
        model_id: bge-m3

    storage:
      backends:
        kv_default:
          type: kv_sqlite
          db_path: ${env.SQLITE_STORE_DIR:=~/.ogx/distributions/starter}/kvstore.db
        sql_default:
          type: sql_sqlite
          db_path: ${env.SQLITE_STORE_DIR:=~/.ogx/distributions/starter}/sql_store.db
      stores:
        metadata:
          namespace: registry
          backend: kv_default
```

## Step 2: Create the OGXServer CR

```bash
# Get cluster OIDC config
AUTH_ISSUER=$(oc get --raw /.well-known/openid-configuration | jq .issuer -r)

# Get a long-lived SA token for JWKS access
SA_NAME="ogx-mt-demo-sa"  # The operator creates this SA
JWKS_TOKEN=$(oc create token $SA_NAME -n redhat-ods-applications --duration=86400s)

# Create the OGXServer
cat << EOF | oc apply -f -
apiVersion: ogx.io/v1beta1
kind: OGXServer
metadata:
  name: ogx-mt-demo
  namespace: redhat-ods-applications
spec:
  distribution:
    name: rh-dev
  overrideConfig:
    name: ogx-mt-demo-config
    key: config.yaml
  network:
    externalAccess:
      enabled: true
  workload:
    overrides:
      env:
      - name: AUTH_ISSUER
        value: "$AUTH_ISSUER"
      - name: AUTH_JWKS_URI
        value: "https://kubernetes.default.svc/openid/v1/jwks"
      - name: AUTH_AUDIENCE
        value: "ogx"
      - name: AUTH_VERIFY_TLS
        value: "false"
      - name: JWKS_TOKEN
        value: "$JWKS_TOKEN"
EOF

# Wait for Ready
oc get ogxserver ogx-mt-demo -n redhat-ods-applications -w
```

## Step 3: Create a Route

The operator creates an Ingress but OpenShift may not auto-create a Route. Create one manually:

```bash
oc expose svc ogx-mt-demo-service -n redhat-ods-applications \
  --name=ogx-mt-demo --port=8321

OGX_URL=http://$(oc get route ogx-mt-demo -n redhat-ods-applications -o jsonpath='{.spec.host}')
echo "OGX URL: $OGX_URL"
```

## Step 4: Create Tenant Namespaces and Service Accounts

```bash
oc new-project tenant-a
oc new-project tenant-b

oc create serviceaccount ogx-user -n tenant-a
oc create serviceaccount ogx-user -n tenant-b

TOKEN_A=$(oc create token ogx-user -n tenant-a --audience ogx --duration=3600s)
TOKEN_B=$(oc create token ogx-user -n tenant-b --audience ogx --duration=3600s)
```

## Step 5: Validate

### Auth enforcement

```bash
# Unauthenticated: should return 401
curl -s -o /dev/null -w "HTTP %{http_code}" "$OGX_URL/v1/models"
# Expected: HTTP 401

# Authenticated: should return 200
curl -s -o /dev/null -w "HTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN_A" "$OGX_URL/v1/models"
# Expected: HTTP 200
```

### Models (shared, both tenants see the same)

```bash
curl -sf -H "Authorization: Bearer $TOKEN_A" "$OGX_URL/v1/models" \
  | python3 -c "import sys,json; [print(m['id']) for m in json.load(sys.stdin)['data']]"
```

### Response isolation

```bash
MODEL="maas-llama/llama-4-scout-17b-16e-w4a16"

# Tenant A creates a response
RESP_A=$(curl -sf -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  "$OGX_URL/v1/responses" \
  -d "{\"model\":\"$MODEL\",\"input\":\"Say hello\",\"store\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Tenant A response: $RESP_A"

# Tenant B creates a response
RESP_B=$(curl -sf -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json" \
  "$OGX_URL/v1/responses" \
  -d "{\"model\":\"$MODEL\",\"input\":\"Explain AI\",\"store\":true}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Tenant B response: $RESP_B"

# Tenant A lists responses: should see ONLY their own
curl -sf -H "Authorization: Bearer $TOKEN_A" "$OGX_URL/v1/responses" \
  | python3 -c "import sys,json; [print(r['id']) for r in json.load(sys.stdin)['data']]"

# Tenant B lists responses: should see ONLY their own
curl -sf -H "Authorization: Bearer $TOKEN_B" "$OGX_URL/v1/responses" \
  | python3 -c "import sys,json; [print(r['id']) for r in json.load(sys.stdin)['data']]"

# Cross-tenant access: should return 404
curl -s -o /dev/null -w "HTTP %{http_code}" \
  -H "Authorization: Bearer $TOKEN_A" "$OGX_URL/v1/responses/$RESP_B"
# Expected: HTTP 404

curl -s -o /dev/null -w "HTTP %{http_code}" \
  -X DELETE -H "Authorization: Bearer $TOKEN_B" "$OGX_URL/v1/responses/$RESP_A"
# Expected: HTTP 404
```

## Tested Versions

| Component | Version | Notes |
|-----------|---------|-------|
| OpenShift | 4.20.24 | Kubernetes v1.33.12 |
| RHOAI | 3.5.0-ea.2 | CSV: `rhods-operator.3.5.0-ea.2` |
| OGX Operator | 0.10.0 | Image: `rhoai/odh-llama-stack-k8s-operator-rhel9` |
| OGX Server | 1.0.2+rhaiv.0 | Image: `rhoai/odh-ogx-core-rhel9` |
| OGXServer CRD | `ogx.io/v1beta1` | Replaced `LlamaStackDistribution` (`llamastack.io/v1alpha1`) |
| Distribution | `rh-dev` | Only available distribution in 3.5 EA2 |
| Keycloak Operator | 26.0.17-opr.1 | Red Hat Build of Keycloak (RHBK) |
| Chat Model | llama-4-scout-17b-16e-w4a16 | Served via MaaS on separate GPU cluster |
| Embedding Model | bge-m3 (1024 dims) | Served via MaaS on separate GPU cluster |
| Auth Provider | OAuth2 JWKS | Kubernetes OIDC as the identity provider |
| Storage | SQLite (kv + sql) | In-pod ephemeral storage (starter config default) |

## Validated Results (2026-06-13)

```
============================================================
OGX MULTI-TENANCY VALIDATION
============================================================

1. Auth enforcement:
   Unauthenticated → HTTP 401 PASS

2. Shared resources (models):
   Tenant A: 5 models   PASS
   Tenant B: 5 models   PASS
   Same models: PASS

3. Response isolation:
   Tenant A created: resp_52ac1bb5-...   HTTP 200
   Tenant B created: resp_623e5534-...   HTTP 200

   Tenant A lists → 1 response
   Tenant B lists → 1 response
   A sees own: PASS
   A sees B's: PASS (isolated)
   B sees own: PASS
   B sees A's: PASS (isolated)

   A reads B's response → HTTP 404 PASS
   B deletes A's response → HTTP 404 PASS
============================================================
```

## Cluster Topology

| Role | Instance Type | Count | Notes |
|------|-------------|-------|-------|
| Masters | m6a.2xlarge | 3 | 8 vCPU, 32 GB RAM. m6a.xlarge (16 GB) is too small for long-lived clusters. |
| Workers | m6a.4xlarge | 3 | 16 vCPU, 64 GB RAM. Runs RHOAI pods, OGX server, notebooks. |
| GPU | g5.2xlarge | 1 | 8 vCPU, 32 GB RAM, 1x NVIDIA A10G. Added via `make gpu`. |

## Known Issues

1. **JWKS token expiry**: The `JWKS_TOKEN` env var is a static SA token with a fixed duration (86400s = 24h). It needs to be refreshed daily. For production, use projected SA volume tokens or configure Keycloak instead.

2. **Route not auto-created**: The operator creates a Kubernetes Ingress without a hostname, which OpenShift doesn't auto-convert to a Route. Manual route creation is required.

3. **Starter config has unused providers**: The starter distribution config includes providers for services not in the RHOAI image (markitdown, together, fireworks, cerebras). These must be removed via `overrideConfig` or they cause `ModuleNotFoundError` at startup.
