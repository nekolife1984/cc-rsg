# Data Flow (cross-tier) — composite chapter

> Composite common chapter: used primarily by the 3-Tier pattern.
> Defined here so the agent can inject it when generating a composite spec.

## Purpose

Describe how data flows across tiers — from user input, through the client, to the server, and into persistence, and back. This chapter documents the end-to-end data path, caching strategy, and sync/async communication boundaries.

Place this chapter after Application tier and before Data tier details. It bridges the gap between tiers and clarifies data consistency guarantees.

## What to include

### 1. End-to-end data flow diagram

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Presentation  │     │  Application  │     │    Data      │
│    Tier       │     │    Tier       │     │    Tier      │
│               │     │               │     │              │
│ User Input ──→│ HTTP│◄─ Process ───→│ SQL │◄─ Read/Write │
│   (form,      │────→│   validation  │────→│   CRUD       │
│    gesture)   │     │   business    │     │   queries    │
│               │←────│   logic       │←────│              │
│ UI Update ◄──│ JSON│─── Response ──→│     │              │
│   (render)    │     │               │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

### 2. Request flow (read path)

| Step | Layer | Action | Data | Cache? |
|------|-------|--------|------|--------|
| 1 | Client | User navigates to screen | Screen ID, params | — |
| 2 | Client | Check local cache | Cache key | 🟢 Cache hit → render cached data |
| 3 | Client | API request | `GET /api/v1/items` | — |
| 4 | Server | Auth validation | Token | — |
| 5 | Server | Business logic | Parse params, apply rules | — |
| 6 | Server | Data access | SQL query | 🟡 Query cache check |
| 7 | Data | Execute query | SQL | — |
| 8 | Data | Return result | Row set | — |
| 9 | Server | Transform response | JSON | — |
| 10 | Server | Update cache | Cache entry | 🟢 Set cache |
| 11 | Client | Receive response | JSON | — |
| 12 | Client | Update local cache | Cache key | 🟢 Set local cache |
| 13 | Client | Render UI | Screen | — |

### 3. Write flow (command path)

| Step | Layer | Action | Consistency guarantee |
|------|-------|--------|---------------------|
| 1 | Client | User submits data | — |
| 2 | Client | Client-side validation | — |
| 3 | Client | POST request | — |
| 4 | Server | Input validation | — |
| 5 | Server | Business rule check | — |
| 6 | Server | Write to database | 🟢 Strong consistency (DB commit) |
| 7 | Server | Invalidate cache | 🟢 Cache invalidation |
| 8 | Server | Return success response | — |
| 9 | Client | Update local state | 🟢 Optimistic or confirmed |
| 10 | Client | Show success to user | — |

### 4. Caching strategy

| Cache layer | Where | What | TTL | Invalidation |
|-------------|-------|------|-----|--------------|
| Browser / App cache | Client | Static assets, API responses | 5 min | On mutation |
| In-memory cache | Client | User session, preferences | Session | On logout |
| CDN | Edge | Static assets, public content | 1 hour | Cache purge |
| Application cache | Server | Query results, computed data | 10 min | On write |
| Database query cache | Server | Frequent SQL queries | 5 min | On table mutation |

### 5. Sync vs. async communication

| Operation | Mode | Protocol | Rationale |
|-----------|------|----------|-----------|
| Data reads | 🟢 Sync | HTTP REST | User-visible, needs immediate response |
| Data writes | 🟢 Sync | HTTP REST | User expects confirmation |
| Email sending | 🟡 Async | Message queue | Non-blocking, retryable |
| Report generation | 🟡 Async | Job queue | Long-running, result via notification |
| Real-time updates | 🟡 Async | WebSocket | Push-based, state synchronisation |
| Batch processing | 🟡 Async | Cron / scheduler | Scheduled, no user interaction |

### 6. Data consistency model

| Scope | Guarantee | Mechanism |
|-------|-----------|-----------|
| Single DB transaction | 🟢 ACID | Database transactions |
| Client optimistic update | 🟡 Eventual | Client assumes success, reverts on error |
| Cache → DB | 🟡 Eventual | Write-through with TTL |
| Cross-service | 🟡 Eventual | Eventual consistency via message bus |
| User-facing | 🟢 Strong | Read-your-writes (session stickiness) |

### 7. Offline / degraded mode (if applicable)

| Scenario | Behaviour | Data available |
|----------|-----------|----------------|
| No network | Read from local cache, queue writes | Cached data only |
| Server unavailable | Show error with retry option | Local data |
| Sync conflict | Last-write-wins / manual merge | Both versions |

## Generation guidelines

- Trace actual code paths during Phase 3 investigation. Do not invent data flows — verify with `read_file` on handler code.
- For **3-Tier** patterns, this chapter is essential — the data path is what ties the tiers together.
- For **Client-Server** patterns, this chapter is optional — include only if there are multi-hop data paths (e.g. client → server → external → server → client).
- Mark each flow step with a 🟢/🟡/🔴 confidence label based on whether the actual code was read.
- Use Mermaid sequence diagrams for complex multi-step flows that are hard to follow in text.
- Include the **data volume and frequency** for each major flow path if available from code or configuration.
