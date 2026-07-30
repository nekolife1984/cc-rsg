---
template_name: api-service
template_version: 0.1.0
last_updated: 2026-05-01
description: API service spec template. For microservices and public APIs that expose REST/GraphQL/gRPC.
---

# API service spec template

This template defines the chapter outline for the spec of a service whose endpoints are called by other systems.

Designed for API services, microservices, and public APIs over REST, GraphQL, gRPC, WebSocket, etc.

---

## Chapter outline

### Chapter 1: Overview

<!-- meta: purpose and scope of the API as a whole. -->

#### 1.1 API purpose
- The value the API provides
- Intended consumers (internal systems / partners / public)
- Position in the business

#### 1.2 Main use cases
- 3-5 representative scenarios

#### 1.3 Service composition diagram
- API Gateway / Load Balancer / Backend structure
- Dependencies on related services

---
---

### Chapter 2: Feature specifications

<!-- meta: consolidated feature-level view of the system. Maps features to screens, routes, and data. -->

#### 2.1 Feature catalogue table

| Feature ID | Feature name | Category | Related items (screens/endpoints/jobs/APIs) | Auth required | Summary | Confidence |
|------------|-------------|----------|-------------------------------------------|-------------|---------|-----------|
| F-001 | (feature) | (category) | (related items) | yes/no | 1-line summary | 🟢/🟡/🔴 |
| F-002 | (feature) | (category) | (related items) | yes/no | 1-line summary | 🟢/🟡/🔴 |
| ... | ... | ... | ... | ... | ... | ... |

The catalogue table exhaustively lists every feature. Confidence labels:
- 🟢 **VERIFIED**: Feature purpose confirmed by reading the actual code (screen, controller, or service file).
- 🟡 **INFERRED**: Feature mechanically grouped from endpoint path prefix or class naming convention.
- 🔴 **ASSUMED**: Feature inferred from use-case description; code evidence is indirect.

#### 2.2 Per-feature processing definitions

For each feature listed above, describe the processing flow structured as below. Generate at minimum the top-5 features by complexity or business criticality; list the remainder in the catalogue table only.

##### F-001: {Feature name}

**Overview**
- Business value this feature provides
- Which user / system role uses it

**Trigger**
- User action / system event / external call that initiates this feature

**Pre-conditions**
- Conditions that must hold before execution

**Main flow**
1. Step 1 [REF: src/path:line]
2. Step 2 [REF: src/path:line]
3. ...

**Alternative flows**
- Alt-1: When [condition] → [behaviour] [REF: src/path:line]

**Error handling**
- Error type → system behaviour [REF: src/path:line]

**Post-conditions**
- State of the system after successful execution

**Related business rules**
- → Ch? (Domain rules section) cross-reference

**Related chapters**
- → Ch? (Screen details / Routes / Data model) cross-reference

**Confidence**: 🟢/🟡/🔴

---



### Chapter 3: Architecture overview

<!-- meta: technology choices and overall structure. -->

#### 3.1 Technology stack
- Language / framework (Spring Boot / Express / FastAPI / .NET, etc.)
- API style (REST / GraphQL / gRPC / WebSocket)
- API spec format (OpenAPI / GraphQL SDL / .proto)

#### 3.2 Internal architecture
- Layering (Controller / Service / Repository, etc.)
- Data stores (RDB / NoSQL / Cache)
- Messaging infrastructure

#### 3.3 Deployment topology
- Runtime (Kubernetes / ECS / Lambda, etc.)
- Scaling strategy

---

### Chapter 4: Class / Module Design

<!-- meta: internal structure — classes, modules, and their relationships. -->

#### 4.1 Module overview

| Module / package | Responsibility | Key classes | Dependencies |
|:----------------|:-------------|:-----------|:------------|
| ... | ... | ... | ... |

#### 4.2 Class catalogue

| Class | Kind | Module | Responsibility | Depends on | Source |
|:------|:----|:-------|:-------------|:----------|:-------|
| ... | ... | ... | ... | ... | [REF: ...] |

#### 4.3 Class diagram (Mermaid)
Include a `classDiagram` for key subsystems. Split per module if >15 classes (see SKILL.md Split rule).

#### 4.4 Module dependency diagram (Mermaid)
Show the direction of dependencies between top-level modules using `graph TD` or `flowchart TD`.

---

### Chapter 5: Endpoint catalogue

<!-- meta: inventory of all endpoints. The pillar of verification. -->

#### 4.1 Endpoint catalogue
| Endpoint ID | Method | Path | Summary | Auth | Version |
|---------------|---------|------|------|------|----------|
| EP-001 | GET | /v1/users/{id} | Get user | required | v1 |
| EP-002 | POST | /v1/users | Create user | required | v1 |
| ... | ... | ... | ... | ... | ... |

#### 4.2 Grouping by resource
- Organise endpoints by resource
- Relationships between resources

---

### Chapter 6: Request / response specifications

<!-- meta: per-endpoint details. If they can be generated from OpenAPI, reference only is acceptable. -->

For each endpoint, describe:

#### {Endpoint name}

##### Overview
- Purpose
- Use scenario

##### Request
- HTTP method + path
- Path parameters
- Query parameters
- Headers (required / optional)
- Request body (schema + example)

##### Response
- Success (2xx)
  - Status code
  - Response body (schema + example)
  - Response headers
- Error (4xx, 5xx)
  - Expected error codes
  - Error response body

##### Side effects
- Database updates
- Calls to external systems
- Events published

##### Idempotency
- Whether the endpoint is idempotent
- Idempotency-key mechanism (if supported)

---

### Chapter 7: Data Model

<!-- meta: persistent data structures and entity relationships. -->

#### 7.1 Data stores

| Store | Type | Purpose | Connection config | ORM / client |
|:------|:----|:-------|:----------------|:------------|
| Main DB | PostgreSQL | Primary persistence | config/database.yml | ActiveRecord |
| Cache | Redis | Session / rate-limit store | config/cache.yml | RedisClient |
| ... | ... | ... | ... | ... |

#### 7.2 Entity definitions

Per entity (one table per row):

| Entity | Table / collection | Key fields | Relations | Corresponding model | Source |
|:-------|:-----------------|:----------|:---------|:------------------|:-------|
| User | users | id, name, email, role | 1:N→Issue | User model | app/models/user.rb |
| Issue | issues | id, title, status, user_id | N:1→User | Issue model | app/models/issue.rb |
| ... | ... | ... | ... | ... | ... |

Full field definitions per entity (expand in the chapter body):

| Field | Type | Required | Default | Index | FK | Business meaning |
|:------|:----|:--------:|:-------|:----:|:--|:----------------|
| id | bigint | ✅ | auto | PK | - | Primary key |
| name | string | ✅ | - | unique | - | Display name |
| email | string | ✅ | - | unique | - | Login identifier |
| role | enum | ✅ | 'user' | - | - | 'user' / 'admin' |
| ... | ... | ... | ... | ... | ... | ... |

#### 7.3 Key domain rules
- Invariants (e.g. "issue status cannot transition from closed to open")
- State transitions (Mermaid stateDiagram-v2)
- Business rules (e.g. "withdrawn users are excluded from search results")

---

### Chapter 8: Error codes / error responses

<!-- meta: full error-code list and semantics. -->

#### 8.1 Common error-response
```json
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "The specified user was not found",
    "details": {},
    "trace_id": "..."
  }
}
```

#### 8.2 Error-code list
| Code | HTTP status | Category | Meaning | Consumer action |
|-------|--------------|---------|------|----------|
| USER_NOT_FOUND | 404 | client error | User does not exist | Check the ID |
| RATE_LIMIT_EXCEEDED | 429 | client error | Rate-limited | Retry |
| INTERNAL_ERROR | 500 | server error | Internal failure | Contact support |
| ... | ... | ... | ... | ... |

#### 8.3 HTTP status-code policy
- When to use 200 vs 201 vs 204
- When to use 400 vs 401 vs 403 vs 404 vs 409 vs 422
- When to use 500 vs 502 vs 503 vs 504

---

### Chapter 9: External interfaces

<!-- meta: all system boundaries — external APIs, databases, queues, file transfers. -->

#### 9.1 External interface inventory

| IF-ID | Name | Type | Protocol | Direction | Consumer / provider | Failure behaviour |
|:------|:-----|:----|:---------|:--------:|:------------------|:-----------------|
| IF-001 | Payment API | REST API | HTTPS | Outbound | Payment gateway | Retry 3x, notify |
| IF-002 | Main DB | Database | PostgreSQL | Bidirectional | Primary RDS | Pool reconnect |
| ... | ... | ... | ... | ... | ... | ... |

#### 9.2 External API integrations

##### 9.2.1 Integration partners

| Partner | Protocol | Purpose | Authentication | Timeout | Behaviour on failure |
|---------|----------|------|--------------|:-------|-------------------|
| ... | ... | ... | ... | ... | ... |

##### 9.2.2 Details per integration
- Authentication method (API key, OAuth, etc.)
- Request / response example
- Timeout / retry policy
- Idempotency (or lack thereof)
- Fallback behaviour on failure

#### 9.3 Database connections

| Database | Type | Host / connection | Auth | Pool | TLS | Usage |
|:---------|:-----|:-----------------|:----|:----:|:---|:------|
| Main DB | PostgreSQL | db.example.com:5432 | SCRAM-SHA-256 | max: 10 | required | Primary persistence |

#### 9.4 Message queues / event streams

| Queue / topic | Type | Broker | Direction | Routing | Retry / DLQ | Consumers |
|:-------------|:----|:------|:--------:|:--------|:-----------|:----------|
| ... | ... | ... | ... | ... | ... | ... |

#### 9.5 File transfers

| Transfer | Source | Destination | Protocol | Schedule | File pattern | Encryption |
|:---------|:-------|:-----------|:---------|:--------|:------------|:----------|
| ... | ... | ... | ... | ... | ... | ... |

---

### Chapter 10: Authentication

<!-- meta: authentication-method details. -->

#### 10.1 Authentication method
- API key / OAuth 2.0 / JWT / mTLS / Basic auth
- Reason for the choice

#### 10.2 Authentication flow
- Token-acquisition steps
- Token lifetime
- Refresh procedure

#### 10.3 Authorisation
- Scopes / permissions
- Role-based access control (RBAC)

#### 10.4 Credential management
- Where keys / secrets are stored
- Rotation procedure

---

### Chapter 11: Rate limiting / quotas

<!-- meta: usage caps and behaviour. -->

#### 11.1 Rate-limit policy
| Tier | Limit | Unit | Scope |
|------|-------|---------|---------|
| Free plan | 100 req/min | per minute | per API key |
| Paid plan | 10000 req/min | per minute | per API key |
| ... | ... | ... | ... |

#### 11.2 Behaviour on exceeding the limit
- HTTP status (429 Too Many Requests)
- Retry-After header
- When the limit resets

#### 11.3 Quotas
- Monthly / daily total-call ceilings
- Behaviour when exceeded

---

### Chapter 12: Versioning

<!-- meta: API evolution and compatibility. -->

#### 12.1 Versioning strategy
- URL-path style (/v1/, /v2/)
- Header style
- Media-type style

#### 12.2 Supported versions
| Version | Released | Sunset planned | Status |
|----------|----------|---------------|------|
| v1 | 2024-01 | 2026-12 | active |
| v2 | 2026-03 | - | active (recommended) |

#### 12.3 Breaking-change policy
- What counts as a breaking change
- Advance-notice period
- Migration-guide commitment

#### 12.4 Backward compatibility
- Change patterns that preserve compatibility
- Deprecation process

---

### Chapter 13: SLA / performance requirements

<!-- meta: the quality the service provides. -->

#### 13.1 Availability targets
- Availability SLA (e.g. 99.9%)
- Measurement method
- How planned downtime is announced

#### 13.2 Performance targets
| Metric | Target | Measurement |
|------|-------|---------|
| Mean response time | < 200ms | p50 |
| 95th percentile response time | < 500ms | p95 |
| Peak throughput | 10000 RPS | over 1-minute windows |

#### 13.3 Incident response
- Incident classification
- Communication flow
- Status page

---

### Chapter 14: Operations settings

<!-- meta: deployment / monitoring / logging. -->

#### 14.1 Environment variables / configuration values
| Variable | Required | Default | Purpose |
|-------|------|----------|------|
| DB_HOST | required | - | Database connection target |
| ... | ... | ... | ... |

#### 14.2 Deployment procedure
- Build / deploy pipeline
- Canary releases (if used)
- Rollback procedure

#### 14.3 Monitoring
- Monitored metrics
- Alert conditions
- Dashboards

#### 14.4 Logging

| Log type | Output | Format | Level | Retention | Source config |
|:---------|:-------|:------|:-----|:---------|:-------------|
| Access log | stdout | JSON (structured) | info | 90 days | config/logging.rb:10 |
| Application log | stdout | JSON (structured) | debug~error | 90 days | config/logging.rb:25 |
| Error log | stderr | JSON (structured) | warn~fatal | 1 year | config/logging.rb:40 |

Log level definitions:
| Level | Meaning | Output |
|:------|:--------|:-------|
| DEBUG | Detailed diagnostic info (dev only) | Dev environment |
| INFO | Normal operation messages | Always |
| WARN | Warning conditions | Always |
| ERROR | Recoverable errors | Always |
| FATAL | Unrecoverable errors | Always |

---

### Chapter 15: Known constraints and unresolved items

<!-- meta: spec credibility safeguard. -->

#### 15.1 Known technical constraints
- Request-body size cap
- Concurrent-connection cap
- Known bugs / workarounds

#### 15.2 Unresolved items
- Place the `abandoned` entries from the Question Bank here

---

## Customisation guidance

### GraphQL
- Restructure Chapter 3 into "Schema", "Query", "Mutation", "Subscription".
- Change Chapter 4 to per-resolver descriptions.

### gRPC
- Restructure Chapter 3 into "Service" and "RPC Method".
- Change Chapter 4 to centre on `.proto` message definitions.

### WebSocket
- Restructure Chapter 3 around "message types".
- Change Chapter 4 to centre on client / server message flow.

### Public API (for external developers)
- Add "Quick start" and "SDK support" chapters.
- Add a "Changelog" chapter.

Customisation is finalised in dialogue with the user after Phase 1 template selection.
