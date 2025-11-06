# RFE: JWT Authentication Passthrough to MCP Servers and Tools

**Status:** Draft  
**Priority:** High  
**Component:** Llama Stack - Responses API, MCP Integration  
**Related:** PR #3388 (JWT forwarding to vLLM)  
**Date:** 2025-11-02

---

## Problem Statement

### Current Situation

Llama Stack currently supports JWT authentication passthrough to model inference backends (vLLM) via PR #3388, enabling per-user authorization at the model layer. However, **JWT authentication is NOT forwarded to MCP (Model Context Protocol) servers when tools are invoked** through the Responses API.

This creates a critical security and compliance gap:

1. **No User Context in Tool Execution**: MCP tools execute without knowledge of which user triggered the request
2. **No Access Control Enforcement**: MCP servers cannot enforce per-user data access policies or RBAC
3. **Audit Trail Gaps**: Cannot track which user accessed what data through tool calls
4. **Compliance Violations**: Fails to meet regulatory requirements (GDPR, HIPAA, SOC2) for user attribution and data access control
5. **Security Risk**: Users can potentially access data they shouldn't have permission to see through tool calls

### Example Scenario

```
User Alice (JWT: eyJhbGc...Alice...) asks: "Fetch my sales reports"
User Bob   (JWT: eyJhbGc...Bob...)   asks: "Fetch my sales reports"

Current Flow (BROKEN):
├─ Alice → Llama Stack → VLLM (✅ receives Alice's JWT)
│                      └─ MCP Tool "fetch_reports" (❌ NO JWT)
│                          └─ Returns ALL reports (Alice + Bob + Everyone)
│                              └─ ❌ Alice sees Bob's data
│
└─ Bob   → Llama Stack → VLLM (✅ receives Bob's JWT)
                       └─ MCP Tool "fetch_reports" (❌ NO JWT)
                           └─ Returns ALL reports (Alice + Bob + Everyone)
                               └─ ❌ Bob sees Alice's data
```

### Impact

**Security:**
- Data leakage across user boundaries
- Unauthorized access to sensitive information
- No defense against privilege escalation

**Compliance:**
- Cannot demonstrate user-level access control
- Audit logs incomplete (missing user attribution for tool calls)
- Fails regulatory requirements for data access tracking

**Enterprise Adoption:**
- Blocks deployment in regulated industries (healthcare, finance, government)
- Cannot meet enterprise security requirements
- Limits multi-tenant use cases

---

## Overview

### Proposed Solution

Extend the JWT authentication passthrough mechanism (implemented in PR #3388 for vLLM) to **MCP servers and tool invocations** in the Responses API.

### Architecture

```
┌─────────────┐
│   User      │ Authenticates to OpenShift/IdP
└──────┬──────┘
       │ Gets JWT (e.g., "eyJhbGc...")
       ▼
┌─────────────────────────────────────────────────────────┐
│  Client Application                                     │
│  - Holds user JWT                                       │
└──────┬──────────────────────────────────────────────────┘
       │ HTTP Request with JWT
       │ Authorization: Bearer <JWT>
       ▼
┌─────────────────────────────────────────────────────────┐
│  Llama Stack Server                                     │
│  1. Receives request with JWT                           │
│  2. Validates JWT (signature, expiry, issuer)           │
│  3. Extracts user identity/permissions                  │
│  4. Forwards JWT to backends:                           │
│     ├─→ VLLM (✅ WORKS - PR #3388)                      │
│     └─→ MCP Servers (❌ PROPOSED - THIS RFE)            │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────────────┐
       │                                                 │
       ▼                                                 ▼
┌─────────────────────┐                   ┌─────────────────────┐
│  VLLM Backend       │                   │  MCP Server         │
│  ✅ Receives JWT    │                   │  ✅ Receives JWT    │
│  ✅ Validates token │                   │  ✅ Validates token │
│  ✅ Enforces authz  │                   │  ✅ Enforces RBAC   │
└─────────────────────┘                   └─────────────────────┘
```

### Key Components

1. **Llama Stack Responses API**: Extract and propagate user JWT to MCP clients
2. **MCP Client Integration**: Pass authentication headers when connecting to MCP servers
3. **MCP Tool Invocation**: Include JWT in tool execution requests
4. **MCP Server Implementation**: Validate JWT and enforce per-tool authorization

---

## Technical Design

### 1. Request Flow Changes

#### Current Flow (Without JWT Passthrough)

```python
# In Llama Stack Responses API handler
async def handle_responses_create(request):
    # Extract user query and tools
    tools = request.tools
    
    # Connect to MCP server
    for tool in tools:
        if tool.type == "mcp":
            # ❌ NO JWT passed here
            async with sse_client(tool.server_url) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    available_tools = await session.list_tools()
                    
                    # Execute tool
                    result = await session.call_tool(
                        name=# RFE: JWT Authentication Passthrough to MCP Servers and Tools

**Status:** Draft  
**Priority:** High  
**Component:** Llama Stack - Responses API, MCP Integration  
**Related:** PR #3388 (JWT forwarding to vLLM)  
**Date:** 2025-11-02

---

## Problem Statement

### Current Situation

Llama Stack currently supports JWT authentication passthrough to model inference backends (vLLM) via PR #3388, enabling per-user authorization at the model layer. However, **JWT authentication is NOT forwarded to MCP (Model Context Protocol) servers when tools are invoked** through the Responses API.

This creates a critical security and compliance gap:

1. **No User Context in Tool Execution**: MCP tools execute without knowledge of which user triggered the request
2. **No Access Control Enforcement**: MCP servers cannot enforce per-user data access policies or RBAC
3. **Audit Trail Gaps**: Cannot track which user accessed what data through tool calls
4. **Compliance Violations**: Fails to meet regulatory requirements (GDPR, HIPAA, SOC2) for user attribution and data access control
5. **Security Risk**: Users can potentially access data they shouldn't have permission to see through tool calls

### Example Scenario

```
User Alice (JWT: eyJhbGc...Alice...) asks: "Fetch my sales reports"
User Bob   (JWT: eyJhbGc...Bob...)   asks: "Fetch my sales reports"

Current Flow (BROKEN):
├─ Alice → Llama Stack → VLLM (✅ receives Alice's JWT)
│                      └─ MCP Tool "fetch_reports" (❌ NO JWT)
│                          └─ Returns ALL reports (Alice + Bob + Everyone)
│                              └─ ❌ Alice sees Bob's data
│
└─ Bob   → Llama Stack → VLLM (✅ receives Bob's JWT)
                       └─ MCP Tool "fetch_reports" (❌ NO JWT)
                           └─ Returns ALL reports (Alice + Bob + Everyone)
                               └─ ❌ Bob sees Alice's data
```

### Impact

**Security:**
- Data leakage across user boundaries
- Unauthorized access to sensitive information
- No defense against privilege escalation

**Compliance:**
- Cannot demonstrate user-level access control
- Audit logs incomplete (missing user attribution for tool calls)
- Fails regulatory requirements for data access tracking

**Enterprise Adoption:**
- Blocks deployment in regulated industries (healthcare, finance, government)
- Cannot meet enterprise security requirements
- Limits multi-tenant use cases

---

## Overview

### Proposed Solution

Extend the JWT authentication passthrough mechanism (implemented in PR #3388 for vLLM) to **MCP servers and tool invocations** in the Responses API.

### Architecture

```
┌─────────────┐
│   User      │ Authenticates to OpenShift/IdP
└──────┬──────┘
       │ Gets JWT (e.g., "eyJhbGc...")
       ▼
┌─────────────────────────────────────────────────────────┐
│  Client Application                                     │
│  - Holds user JWT                                       │
└──────┬──────────────────────────────────────────────────┘
       │ HTTP Request with JWT
       │ Authorization: Bearer <JWT>
       ▼
┌─────────────────────────────────────────────────────────┐
│  Llama Stack Server                                     │
│  1. Receives request with JWT                           │
│  2. Validates JWT (signature, expiry, issuer)           │
│  3. Extracts user identity/permissions                  │
│  4. Forwards JWT to backends:                           │
│     ├─→ VLLM (✅ WORKS - PR #3388)                      │
│     └─→ MCP Servers (❌ PROPOSED - THIS RFE)            │
└──────┬──────────────────────────────────────────────────┘
       │
       ├─────────────────────────────────────────────────┐
       │                                                 │
       ▼                                                 ▼
┌─────────────────────┐                   ┌─────────────────────┐
│  VLLM Backend       │                   │  MCP Server         │
│  ✅ Receives JWT    │                   │  ✅ Receives JWT    │
│  ✅ Validates token │                   │  ✅ Validates token │
│  ✅ Enforces authz  │                   │  ✅ Enforces RBAC   │
└─────────────────────┘                   └─────────────────────┘
```

### Key Components

1. **Llama Stack Responses API**: Extract and propagate user JWT to MCP clients
2. **MCP Client Integration**: Pass authentication headers when connecting to MCP servers
3. **MCP Tool Invocation**: Include JWT in tool execution requests
4. **MCP Server Implementation**: Validate JWT and enforce per-tool authorization

---

## Technical Design

### 1. Request Flow Changes

#### Current Flow (Without JWT Passthrough)

```python
# In Llama Stack Responses API handler
async def handle_responses_create(request):
    # Extract user query and tools
    tools = request.tools
    
    # Connect to MCP server
    for tool in tools:
        if tool.type == "mcp":
            # ❌ NO JWT passed here
            async with sse_client(tool.server_url) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    available_tools = await session.list_tools()
                    
                    # Execute tool
                    result = await session.call_tool(
                        name="fetch",
                        arguments={"url": "..."}
                    )  # ❌ NO JWT passed here
```

#### Proposed Flow (With JWT Passthrough)

```python
# In Llama Stack Responses API handler
async def handle_responses_create(request):
    # Extract user JWT from request
    user_jwt = request.headers.get("Authorization")
    
    # Extract user query and tools
    tools = request.tools
    
    # Connect to MCP server WITH JWT
    for tool in tools:
        if tool.type == "mcp":
            # ✅ Pass JWT in headers
            headers = {"Authorization": user_jwt}
            
            async with sse_client(tool.server_url, headers=headers) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    available_tools = await session.list_tools()
                    
                    # Execute tool WITH JWT
                    result = await session.call_tool(
                        name="fetch",
                        arguments={"url": "..."},
                        headers={"Authorization": user_jwt}  # ✅ JWT included
                    )
```

### 2. MCP Server Changes

MCP servers must be updated to:

1. **Accept authentication headers** in SSE/HTTP requests
2. **Validate JWT tokens** (signature, expiry, issuer, audience)
3. **Extract user identity** from validated token
4. **Enforce per-tool authorization** based on user permissions

```python
# Example MCP server tool with JWT validation
from mcp.server import Server
import jwt

mcp_server = Server("my-mcp-server")

@mcp_server.call_tool()
async def fetch_document(arguments: dict, context) -> str:
    """Fetch document with per-user access control"""
    
    # Extract JWT from request context
    auth_header = context.headers.get("Authorization")
    if not auth_header:
        raise PermissionError("Authentication required")
    
    # Validate JWT
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer="https://openshift.example.com",
            audience="mcp-tools"
        )
    except jwt.InvalidTokenError as e:
        raise PermissionError(f"Invalid token: {e}")
    
    # Extract user identity
    user_id = payload.get("sub")
    user_roles = payload.get("roles", [])
    
    # Enforce access control
    doc_id = arguments.get("document_id")
    if not can_access_document(user_id, user_roles, doc_id):
        raise PermissionError(f"User {user_id} cannot access document {doc_id}")
    
    # Fetch and return document
    return get_document(doc_id)
```

### 3. Configuration

#### Llama Stack Configuration

```yaml
# run.yaml
providers:
  inference:
    - provider_id: vllm
      provider_type: remote::vllm
      config:
        url: ${env.VLLM_URL}
        api_token: ${env.VLLM_API_TOKEN}  # Static token (optional)
        # Dynamic tokens via X-LlamaStack-Provider-Data (PR #3388)

authentication:
  enabled: true
  jwt_validation:
    issuer: "https://openshift.example.com"
    audience: "llama-stack"
    public_key_url: "https://openshift.example.com/.well-known/jwks.json"
  
  # NEW: MCP JWT forwarding configuration
  mcp_jwt_forwarding:
    enabled: true
    forward_to_all_servers: true  # Or specify per-server
    header_name: "Authorization"  # Default
```

#### MCP Server Configuration

```yaml
# mcp_server_config.yaml
authentication:
  enabled: true
  jwt_validation:
    issuer: "https://openshift.example.com"
    audience: "mcp-tools"
    public_key_url: "https://openshift.example.com/.well-known/jwks.json"
    algorithms: ["RS256"]

authorization:
  mode: "rbac"  # or "policy", "custom"
  policy_file: "/etc/mcp/policies.yaml"
  
  # Per-tool authorization rules
  tools:
    fetch_document:
      required_roles: ["document-reader"]
      required_scopes: ["read:documents"]
    
    update_document:
      required_roles: ["document-writer"]
      required_scopes: ["write:documents"]
```

---

## Success Criteria

### Functional Requirements

- [ ] **FR1**: Llama Stack Responses API extracts JWT from incoming `Authorization` header
- [ ] **FR2**: JWT is forwarded to MCP servers during connection initialization (`list_tools`)
- [ ] **FR3**: JWT is forwarded to MCP servers during tool invocation (`call_tool`)
- [ ] **FR4**: MCP servers can access JWT from request context
- [ ] **FR5**: MCP servers can validate JWT (signature, expiry, issuer, audience)
- [ ] **FR6**: MCP servers can extract user identity and permissions from JWT
- [ ] **FR7**: MCP servers can enforce per-tool RBAC based on user permissions
- [ ] **FR8**: Configuration option to enable/disable JWT forwarding per MCP server
- [ ] **FR9**: Backward compatibility: MCP servers without auth continue to work

### Non-Functional Requirements

- [ ] **NFR1**: JWT forwarding adds < 10ms latency to tool invocations
- [ ] **NFR2**: JWT validation failures return clear error messages to clients
- [ ] **NFR3**: Audit logs include user identity for all tool invocations
- [ ] **NFR4**: Documentation includes setup guide for JWT-enabled MCP servers
- [ ] **NFR5**: Example MCP server implementation with JWT validation provided

### Security Requirements

- [ ] **SR1**: JWTs are transmitted securely (HTTPS/TLS required for production)
- [ ] **SR2**: JWT validation includes signature verification, expiry check, issuer validation
- [ ] **SR3**: Invalid/expired JWTs result in tool execution failure (fail-closed)
- [ ] **SR4**: MCP servers can configure trusted issuers and audiences
- [ ] **SR5**: No JWT leakage in logs or error messages

### Testing Requirements

- [ ] **TR1**: Unit tests for JWT extraction in Responses API
- [ ] **TR2**: Integration tests for JWT forwarding to MCP servers
- [ ] **TR3**: End-to-end tests with real JWT validation
- [ ] **TR4**: Security tests for invalid/expired/malformed JWTs
- [ ] **TR5**: Performance tests for JWT forwarding overhead
- [ ] **TR6**: Multi-user tests verifying access control enforcement

---

## Implementation Phases

### Phase 1: Core JWT Forwarding (MVP)
- Implement JWT extraction in Responses API
- Forward JWT to MCP servers in connection and tool calls
- Update MCP client library to support authentication headers
- Basic documentation and examples

### Phase 2: MCP Server Support
- Reference implementation of JWT validation in MCP server
- Example RBAC enforcement patterns
- Configuration schema for MCP server authentication

### Phase 3: Advanced Features
- Per-server JWT forwarding configuration
- Token refresh/rotation support
- Integration with enterprise identity providers (Keycloak, Okta, Azure AD)
- Comprehensive audit logging

---

## Dependencies

- **PR #3388**: JWT forwarding to vLLM (provides pattern to follow)
- **MCP Protocol Specification**: May need updates to support authentication headers
- **llama-stack-client**: MCP client library updates
- **OpenShift/Identity Provider**: JWT issuer and validation infrastructure

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to MCP protocol | High | Maintain backward compatibility; make auth optional |
| Performance overhead from JWT validation | Medium | Cache validated tokens; use efficient JWT libraries |
| Complex configuration for users | Medium | Provide sensible defaults; comprehensive documentation |
| MCP server implementations lag behind | Medium | Provide reference implementation and migration guide |

---

## References

- **PR #3388**: [Add dynamic authentication token forwarding support for vLLM](https://github.com/meta-llama/llama-stack/pull/3388)
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- **JWT RFC**: [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- **OpenID Connect**: [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

---

## Appendix: Example Use Cases

### Use Case 1: Multi-Tenant RAG System

**Scenario**: Multiple customers use the same Llama Stack deployment for document retrieval.

**Requirement**: Each customer should only access their own documents.

**Solution**:
```python
# MCP tool: fetch_documents
# - Receives user JWT
# - Validates user identity
# - Filters documents by customer_id from JWT
# - Returns only authorized documents
```

### Use Case 2: Healthcare Data Access

**Scenario**: Doctors query patient records through AI assistant.

**Requirement**: HIPAA compliance requires user attribution and access control.

**Solution**:
```python
# MCP tool: get_patient_record
# - Validates doctor's JWT
# - Checks doctor has treating relationship with patient
# - Logs access for audit trail
# - Returns patient data only if authorized
```

### Use Case 3: Financial Services

**Scenario**: Analysts query market data and customer portfolios.

**Requirement**: SOC2 compliance requires role-based access control.

**Solution**:
```python
# MCP tool: query_portfolio
# - Validates analyst's JWT
# - Checks analyst's role and permissions
# - Enforces data access policies
# - Returns portfolio data based on authorization level
```

"fetch",
                        arguments={"url": "..."}
                    )  # ❌ NO JWT passed here
```

#### Proposed Flow (With JWT Passthrough)

```python
# In Llama Stack Responses API handler
async def handle_responses_create(request):
    # Extract user JWT from request
    user_jwt = request.headers.get("Authorization")
    
    # Extract user query and tools
    tools = request.tools
    
    # Connect to MCP server WITH JWT
    for tool in tools:
        if tool.type == "mcp":
            # ✅ Pass JWT in headers
            headers = {"Authorization": user_jwt}
            
            async with sse_client(tool.server_url, headers=headers) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    available_tools = await session.list_tools()
                    
                    # Execute tool WITH JWT
                    result = await session.call_tool(
                        name="fetch",
                        arguments={"url": "..."},
                        headers={"Authorization": user_jwt}  # ✅ JWT included
                    )
```

### 2. MCP Server Changes

MCP servers must be updated to:

1. **Accept authentication headers** in SSE/HTTP requests
2. **Validate JWT tokens** (signature, expiry, issuer, audience)
3. **Extract user identity** from validated token
4. **Enforce per-tool authorization** based on user permissions

```python
# Example MCP server tool with JWT validation
from mcp.server import Server
import jwt

mcp_server = Server("my-mcp-server")

@mcp_server.call_tool()
async def fetch_document(arguments: dict, context) -> str:
    """Fetch document with per-user access control"""
    
    # Extract JWT from request context
    auth_header = context.headers.get("Authorization")
    if not auth_header:
        raise PermissionError("Authentication required")
    
    # Validate JWT
    token = auth_header.replace("Bearer ", "")
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            issuer="https://openshift.example.com",
            audience="mcp-tools"
        )
    except jwt.InvalidTokenError as e:
        raise PermissionError(f"Invalid token: {e}")
    
    # Extract user identity
    user_id = payload.get("sub")
    user_roles = payload.get("roles", [])
    
    # Enforce access control
    doc_id = arguments.get("document_id")
    if not can_access_document(user_id, user_roles, doc_id):
        raise PermissionError(f"User {user_id} cannot access document {doc_id}")
    
    # Fetch and return document
    return get_document(doc_id)
```

### 3. Configuration

#### Llama Stack Configuration

```yaml
# run.yaml
providers:
  inference:
    - provider_id: vllm
      provider_type: remote::vllm
      config:
        url: ${env.VLLM_URL}
        api_token: ${env.VLLM_API_TOKEN}  # Static token (optional)
        # Dynamic tokens via X-LlamaStack-Provider-Data (PR #3388)

authentication:
  enabled: true
  jwt_validation:
    issuer: "https://openshift.example.com"
    audience: "llama-stack"
    public_key_url: "https://openshift.example.com/.well-known/jwks.json"
  
  # NEW: MCP JWT forwarding configuration
  mcp_jwt_forwarding:
    enabled: true
    forward_to_all_servers: true  # Or specify per-server
    header_name: "Authorization"  # Default
```

#### MCP Server Configuration

```yaml
# mcp_server_config.yaml
authentication:
  enabled: true
  jwt_validation:
    issuer: "https://openshift.example.com"
    audience: "mcp-tools"
    public_key_url: "https://openshift.example.com/.well-known/jwks.json"
    algorithms: ["RS256"]

authorization:
  mode: "rbac"  # or "policy", "custom"
  policy_file: "/etc/mcp/policies.yaml"
  
  # Per-tool authorization rules
  tools:
    fetch_document:
      required_roles: ["document-reader"]
      required_scopes: ["read:documents"]
    
    update_document:
      required_roles: ["document-writer"]
      required_scopes: ["write:documents"]
```

---

## Success Criteria

### Functional Requirements

- [ ] **FR1**: Llama Stack Responses API extracts JWT from incoming `Authorization` header
- [ ] **FR2**: JWT is forwarded to MCP servers during connection initialization (`list_tools`)
- [ ] **FR3**: JWT is forwarded to MCP servers during tool invocation (`call_tool`)
- [ ] **FR4**: MCP servers can access JWT from request context
- [ ] **FR5**: MCP servers can validate JWT (signature, expiry, issuer, audience)
- [ ] **FR6**: MCP servers can extract user identity and permissions from JWT
- [ ] **FR7**: MCP servers can enforce per-tool RBAC based on user permissions
- [ ] **FR8**: Configuration option to enable/disable JWT forwarding per MCP server
- [ ] **FR9**: Backward compatibility: MCP servers without auth continue to work

### Non-Functional Requirements

- [ ] **NFR1**: JWT forwarding adds < 10ms latency to tool invocations
- [ ] **NFR2**: JWT validation failures return clear error messages to clients
- [ ] **NFR3**: Audit logs include user identity for all tool invocations
- [ ] **NFR4**: Documentation includes setup guide for JWT-enabled MCP servers
- [ ] **NFR5**: Example MCP server implementation with JWT validation provided

### Security Requirements

- [ ] **SR1**: JWTs are transmitted securely (HTTPS/TLS required for production)
- [ ] **SR2**: JWT validation includes signature verification, expiry check, issuer validation
- [ ] **SR3**: Invalid/expired JWTs result in tool execution failure (fail-closed)
- [ ] **SR4**: MCP servers can configure trusted issuers and audiences
- [ ] **SR5**: No JWT leakage in logs or error messages

### Testing Requirements

- [ ] **TR1**: Unit tests for JWT extraction in Responses API
- [ ] **TR2**: Integration tests for JWT forwarding to MCP servers
- [ ] **TR3**: End-to-end tests with real JWT validation
- [ ] **TR4**: Security tests for invalid/expired/malformed JWTs
- [ ] **TR5**: Performance tests for JWT forwarding overhead
- [ ] **TR6**: Multi-user tests verifying access control enforcement

---

## Implementation Phases

### Phase 1: Core JWT Forwarding (MVP)
- Implement JWT extraction in Responses API
- Forward JWT to MCP servers in connection and tool calls
- Update MCP client library to support authentication headers
- Basic documentation and examples

### Phase 2: MCP Server Support
- Reference implementation of JWT validation in MCP server
- Example RBAC enforcement patterns
- Configuration schema for MCP server authentication

### Phase 3: Advanced Features
- Per-server JWT forwarding configuration
- Token refresh/rotation support
- Integration with enterprise identity providers (Keycloak, Okta, Azure AD)
- Comprehensive audit logging

---

## Dependencies

- **PR #3388**: JWT forwarding to vLLM (provides pattern to follow)
- **MCP Protocol Specification**: May need updates to support authentication headers
- **llama-stack-client**: MCP client library updates
- **OpenShift/Identity Provider**: JWT issuer and validation infrastructure

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes to MCP protocol | High | Maintain backward compatibility; make auth optional |
| Performance overhead from JWT validation | Medium | Cache validated tokens; use efficient JWT libraries |
| Complex configuration for users | Medium | Provide sensible defaults; comprehensive documentation |
| MCP server implementations lag behind | Medium | Provide reference implementation and migration guide |

---

## References

- **PR #3388**: [Add dynamic authentication token forwarding support for vLLM](https://github.com/meta-llama/llama-stack/pull/3388)
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- **JWT RFC**: [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519)
- **OpenID Connect**: [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)

---

## Appendix: Example Use Cases

### Use Case 1: Multi-Tenant RAG System

**Scenario**: Multiple customers use the same Llama Stack deployment for document retrieval.

**Requirement**: Each customer should only access their own documents.

**Solution**:
```python
# MCP tool: fetch_documents
# - Receives user JWT
# - Validates user identity
# - Filters documents by customer_id from JWT
# - Returns only authorized documents
```

### Use Case 2: Healthcare Data Access

**Scenario**: Doctors query patient records through AI assistant.

**Requirement**: HIPAA compliance requires user attribution and access control.

**Solution**:
```python
# MCP tool: get_patient_record
# - Validates doctor's JWT
# - Checks doctor has treating relationship with patient
# - Logs access for audit trail
# - Returns patient data only if authorized
```

### Use Case 3: Financial Services

**Scenario**: Analysts query market data and customer portfolios.

**Requirement**: SOC2 compliance requires role-based access control.

**Solution**:
```python
# MCP tool: query_portfolio
# - Validates analyst's JWT
# - Checks analyst's role and permissions
# - Enforces data access policies
# - Returns portfolio data based on authorization level
```

