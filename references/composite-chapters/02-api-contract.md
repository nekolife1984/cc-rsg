# API Contract (composite chapter)

> Composite common chapter: used by Client-Server and 3-Tier patterns.
> Defined here so the agent can inject it when generating a composite spec.

## Purpose

Document the full Client↔Server API contract — every endpoint / operation, request/response schemas, authentication, and versioning strategy.

Place this chapter after System architecture and before per-tier detail chapters. It serves as the single source of truth for the communication boundary.

## What to include

### 1. API overview

| Aspect | Description |
|--------|-------------|
| Protocol | HTTP/REST, GraphQL, gRPC, WebSocket |
| Base URL | Production / staging / dev |
| Data format | JSON, Protobuf, MessagePack |
| API style | RPC-style, resource-oriented, query-language |

### 2. Endpoint / Operation catalogue

Exhaustive list of all Client↔Server operations. For each:

```
[Method] [Path] — [Short description]

Request:
  Headers:
    - Authorization: Bearer <token>
    - Content-Type: application/json
  Body:
    {
      "field": "type (description)"
    }

Response 200:
  Body:
    {
      "field": "type (description)"
    }

Errors:
  - 400 Bad Request: validation error
  - 401 Unauthorized: missing/invalid token
  - 404 Not Found: resource does not exist
  - 500 Internal Server Error
```

#### Catalogue table (minimal form)

| Method | Path | Auth required | Request body | Response | Description |
|--------|------|---------------|-------------|----------|-------------|
| GET | `/api/v1/users` | yes | — | `User[]` | List all users |
| POST | `/api/v1/users` | yes | `CreateUser` | `User` | Create a user |
| PUT | `/api/v1/users/{id}` | yes | `UpdateUser` | `User` | Update a user |
| DELETE | `/api/v1/users/{id}` | yes | — | — | Delete a user |

### 3. Authentication and authorisation

| Mechanism | Description |
|-----------|-------------|
| Auth scheme | JWT / OAuth 2.0 / API Key / Session cookie |
| Token lifecycle | Issuance, refresh, revocation, expiry |
| Roles / scopes | RBAC, permission scopes, claim structure |
| Implementation | Client side: token storage, refresh interceptor; Server side: middleware / guard |

### 4. Versioning strategy

| Strategy | Description |
|----------|-------------|
| Version placement | URL path (`/v1/`), header (`Accept: version=1`), query param |
| Deprecation policy | Sunset header, migration window, grace period |
| Backward compatibility | Additive-only changes, field deprecation markers |

### 5. Error contract

| Error code | HTTP status | Meaning | Recovery |
|------------|-------------|---------|----------|
| `INVALID_INPUT` | 400 | Request validation failed | Fix request body |
| `UNAUTHORIZED` | 401 | Missing / invalid credentials | Re-authenticate |
| `FORBIDDEN` | 403 | Insufficient permissions | Request access |
| `NOT_FOUND` | 404 | Resource does not exist | Check identifier |
| `RATE_LIMITED` | 429 | Too many requests | Wait and retry |
| `INTERNAL_ERROR` | 500 | Server error | Retry or contact support |

### 6. Rate limiting and quotas

| Policy | Description |
|--------|-------------|
| Limit | 1000 requests per minute per API key |
| Reset | Rolling window / fixed window |
| Headers | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` |
| Quota tiers | Free: 1000/day, Pro: 10000/day, Enterprise: custom |

### 7. WebSocket / real-time (if applicable)

| Aspect | Description |
|--------|-------------|
| Endpoint | `wss://api.example.com/ws` |
| Events | Event type catalogue with payload schemas |
| Reconnection | Backoff strategy, state recovery |
| Authentication | Token in first message or query param |

## Generation guidelines

- Start from actual OpenAPI / Swagger / GraphQL schema files during Phase 3 investigation.
- If an OpenAPI spec exists, extract the endpoint catalogue programmatically and mark it 🟢 VERIFIED.
- If no schema file exists, infer from route definitions and mark it 🟡 INFERRED.
- For Client-Server patterns, the API contract is the **primary boundary document** — accuracy here is critical.
- For 3-Tier patterns, include only the external-facing API (Presentation ↔ Application). Internal Application ↔ Data tier communication belongs in Data flow chapter.
- Include only contracts the **client calls**. Internal service-to-service APIs belong in the Server architecture section.
