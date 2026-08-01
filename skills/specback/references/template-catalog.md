# Template Catalog Reference

Selection guide used in Phase 1 when presenting template candidates to the user. For each template, this document defines the intended target, chapter-outline summary, selection criteria, and the decision-tree logic.

---

## Chapter ordering principles

The template chapter order **is** the final document order. It is designed around the **reader's comprehension flow** — what a reader needs to know first in order to understand what comes later:

| Position | Chapter group | What it answers | Typical chapters |
|:--------:|---------------|-----------------|------------------|
| 1 | Overview | What system is this? | Overview |
| 2 | Capability view | What can it do? | Feature specifications |
| 3 | Structural overview | How is it built, at a glance? | Architecture overview / Module architecture |
| 4 | Detail chapters | How does each part work? | Screens, routes/endpoints, data model, job catalogue, API catalogue, configuration, ... |
| 5 | Design rationale | Why is it shaped this way? | System design (ADRs, module dependencies, cross-cutting concerns) |
| 6 | Boundaries | What can it not do? | Known constraints and unresolved items |

Rules:

1. **Structural overview goes early** — the Architecture / Module overview sits right after the capability view, so readers can orient themselves before reading details.
2. **Design rationale goes late** — System design sits after the detail chapters, right before Known constraints. It deepens understanding of things the reader has already seen; placed early it would create forward references.
3. **Presentation order ≠ generation order** — the template defines the presentation order; Phase 3 may generate chapters in any order (it dispatches them in parallel). Keeping generation order aligned with presentation order is the current convention, but it is not a requirement.
4. **Judge additions and reorderings against this flow** — when adding or moving a chapter, ask "where does the reader's comprehension flow require this?" rather than "where was the last edit?".
5. **Chapter count is template-specific** — there is no fixed chapter count; each template defines its own outline. Phase docs and scripts must never hardcode a count.

---

## Initial set of 4

The skill ships with the following 4 templates by default. The user may also bring their own template (by specifying a path).

1. **Web application spec** (`templates/web-app.md`)
2. **Batch-system spec** (`templates/batch-system.md`)
3. **API service spec** (`templates/api-service.md`)
4. **Library / SDK spec** (`templates/library-sdk.md`)

---

## 1. Web application spec

### Target
- Systems the user operates through screens.
- PHP (Laravel/Symfony/CakePHP), Python (Django/Flask), Ruby (Rails), Node.js (Next.js/Nuxt/Express), Java (Spring MVC), etc.
- Authentication, session management, and screen transitions are present.

### Chapter outline
- Overview / system purpose
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Architecture overview
- Screen list and transitions
- Routes / endpoint list
- Data model (ER diagram, entity definitions)
- Authentication and authorisation
- External-system integration
- Operations settings / deployment
- System design
- Known constraints and unresolved items

### Selection criteria
- Evidence of HTML rendering and a templating engine.
- Session-management code (`session`, `cookie`).
- Routing definitions present (`routes/`, `urls.py`, etc.).
- Existence of `views/`, `templates/`, `pages/` directories.

---

## 2. Batch-system spec

### Target
- Scheduled or event-driven background processing.
- COBOL + JCL, cron / systemd timers, Spring Batch, Apache Airflow, Celery, Sidekiq, AWS Batch / Lambda scheduled runs.
- Includes data pipelines (ETL).
### Chapter outline
- Overview / business purpose
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Architecture overview
- Job catalogue
- Triggers and schedule
- Data flow (input → processing → output)
- Error handling and retry policy
- Recovery procedures
- Operations calendar / dependency graph
- Monitoring / alerts
- System design
- Known constraints and unresolved items

### Selection criteria
- Presence of scheduler configuration (crontab, Quartz, Airflow DAG, JCL).
- Presence of job-execution scripts.
- No persistent UI or API, or only an admin one.
- Evidence of large-data processing (chunked processing, bulk operations).

---

## 3. API service spec

### Target
- Endpoints called by other systems.
- REST, GraphQL, gRPC, WebSocket.
- Microservices, public APIs, internal APIs.
### Chapter outline
- Overview / API purpose
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Architecture overview
- Endpoint catalogue
- Request / response specs (per endpoint)
- Error codes / error responses
- Authentication (API key, OAuth, JWT)
- Rate limiting / quotas
- Versioning
- SLA / performance requirements
- Operations settings
- System design
- Known constraints and unresolved items
### Selection criteria
- Presence of OpenAPI / Swagger / GraphQL schema.
- Routing definitions centred on endpoints (`/api/...`).
- No web UI (HTML rendering), or only as a secondary feature.
- Presence of API-Gateway configuration (Kong, AWS API Gateway, etc.).

---

## 4. Library / SDK spec

### Target
- Reusable code consumed by other applications.
- npm / pip / composer / gem / NuGet packages.
- Internal common libraries.

### Chapter outline
- Overview / library purpose
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Module architecture (overview) ← top-level structure, placed early for orientation (see Chapter ordering principles)
- Installation
- Public API catalogue
- Usage examples (quick start)
- Configuration options
- Compatibility (supported language versions, dependencies)
- Extension points / plugin system
- Migration guide (from older versions)
- Internal structure (optional)
- System design
- Known constraints and unresolved items

### Selection criteria
- Package manifest (`package.json` / `setup.py` / `composer.json`, etc.) defines `name`, `version`, `main` / `module`.
- Directory structure consistent with distribution (`dist/`, `lib/`, `src/`).
- No application-entry code (a main function, entry-point script), or only samples.

---

## Decision tree (template recommendation logic)

Based on the Phase 1 reconnaissance, the agent follows this procedure to recommend a template:

```
1. Does the package manifest define main/module/bin?
   YES → Is there application-startup code?
            NO  → Recommend Library / SDK spec
            YES → Continue

2. Do routing definitions exist?
   YES → Is there HTML rendering (views/templates)?
            YES → Recommend Web application spec
            NO  → Recommend API service spec

3. Are scheduler configuration / batch scripts the main subject?
   YES → Recommend Batch-system spec

4. None of the above / composite type
   → Present multiple candidates and ask the user.
   → Example: "Includes both web app and API; recommend a merged custom outline."
```

---

## Handling composite projects

Real projects often do not fit into a single template. Handle them as follows.

### Overview: composite detection

When Phase 1 reconnaissance detects characteristics of multiple templates (e.g. both screens and endpoints, or a desktop app with an API backend), the agent must:

1. Identify which template types are present (web-app, api-service, desktop-app, mobile-app, cli-tool, batch-system, library-sdk, infrastructure).
2. Determine the relationship: primary/secondary, equal-scale composite, or separate services.
3. Classify the composite architecture pattern (see below).
4. Apply the recommended approach — unified spec, separate specs with cross-references, or extended monorepo handling.

### When there is a primary / secondary relationship
- Pick the primary template and add a chapter from the secondary one.
- Example: web app primary, batch secondary → add a "background jobs" chapter to the web-app spec.

### Composite at equal scale
- Generate a custom template by merging the chapter outlines.
- Ask the user for the chapter-ordering preference.

### Monorepo with multiple services
- Recommend generating separate specs per service.
- Merge into a single spec only if the user explicitly wants one spec for the whole monorepo.

---

### Pattern 1: Client-Server (e.g. Desktop App + API Service, Mobile App + API Backend)

**Architecture:** Client side + Server side + Communication layer

**Recommended approach:** Unified spec for tighter coupling; separate specs with cross-references for loosely coupled teams.

#### Unified spec chapter ordering

| # | Chapter | Source template | Notes |
|---|---------|----------------|-------|
| 1 | Overview | Common (merged from both) | System purpose, intended users, scope |
| 2 | Feature specifications | Common (Client + Server features merged) | Feature catalogue covering both sides |
| 3 | **System architecture** | **Composite common chapter** | Client-Server topology, tier data flow, deployment diagram |
| 4 | **API contract** | **Composite common chapter** | Full API list, request/response schemas, auth methods, versioning |
| 5 | Client: UI / Screen list | desktop-app or mobile-app | Screen list, transitions, navigation |
| 6 | Client: Platform integration | desktop-app or mobile-app | OS integration, notifications, background tasks |
| 7 | Server: Endpoint catalogue | api-service | Full endpoint list with methods and paths |
| 8 | Server: Data model | api-service | ER diagram, entity definitions |
| 9 | Server: Auth | api-service | Authentication flows, token management |
| 10 | Client: State / Data persistence | desktop-app or mobile-app | Local storage, caching, sync strategy |
| 11 | Design decisions | Both (merged) | Architectural decisions for both sides |
| 12 | Known constraints | Common | Cross-cutting constraints |

#### Separate specs with cross-references

```markdown
Client spec:
  - "API contract details are in the Server spec Chapter 7 (Endpoint catalogue)"
  - REF: server/specs/07-endpoint-catalogue.md

Server spec:
  - "Screen transitions are in the Client spec Chapter 5 (Screen list)"
  - REF: client/specs/05-screen-list.md
```

#### Selection criteria
- Evidence of two distinct deployable units (e.g. separate `package.json`, `Dockerfile`, deployment configs).
- Client has UI code; Server has endpoint/routing code.
- A communication protocol boundary (HTTP, WebSocket, gRPC) is identifiable.

---

### Pattern 2: 3-Tier (Presentation + Application + Data)

**Architecture:** Presentation tier (UI) + Application tier (business logic / API) + Data tier (persistence / storage)

**Recommended approach:** Single unified spec (tier-spanning consistency is more important than separation).

#### Unified spec chapter ordering

| # | Chapter | Content | Notes |
|---|---------|---------|-------|
| 1 | Overview | Overall purpose, 3-tier responsibilities | |
| 2 | Feature specifications | Tier-spanning feature list | Features may span multiple tiers |
| 3 | **System architecture** | **Composite common chapter** | 3-tier topology diagram, tier interfaces, deployment configuration |
| 4 | Presentation tier: UI | Screen list, transitions (web-app / mobile-app / desktop-app) | |
| 5 | Application tier: API / Logic | Endpoint catalogue, business rules (api-service) | |
| 6 | **Data flow (cross-tier)** | **Composite common chapter** | Presentation → Application → Data flow, caching, sync/async |
| 7 | Data tier: Data model | ER diagram, entity definitions, schema | |
| 8 | Auth (cross-tier) | Consistent auth flow: token → session → DB | Covers auth across all tiers |
| 9 | Operations / Deployment | Deployment per tier, CI/CD, scaling | |
| 10 | Design decisions | Technology choices per tier, why 3 tiers | Including tier-separation rationale |
| 11 | Known constraints | Constraints per tier | |

#### Selection criteria
- Three clearly separated layers (UI code, business logic code, data access code) in the codebase structure.
- Each tier may correspond to a separate deployment unit or be logical layers within the same process.
- Separation of concerns is a deliberate architectural choice (not accidental).

---

### Pattern 3: Monorepo with shared library

Extends the base "Monorepo with multiple services" handling when services share a common library.

**Architecture:** Multiple services + shared library(s)

**Recommended approach:** Separate specs per service + one shared library spec. Cross-reference shared library spec from each service spec.

#### Additional guidelines

| Aspect | Action |
|--------|--------|
| Shared library spec | Generate a full Library / SDK spec for each shared library |
| Service-to-library dependency | List in each service spec's dependency section: "depends on `shared-lib` vX.Y.Z" |
| Version alignment | Document version pinning strategy (monorepo-sync, semver ranges, lockfile) |
| API contract | If the library exposes a public API, add an "API catalogue" chapter (from library-sdk template) |
| Cross-reference pattern | `REF: shared-lib/specs/04-api-catalogue.md` in service specs |

#### Spec document layout

```
project/
├── service-a/
│   └── specs/service-a-spec.md   ← api-service or web-app spec
├── service-b/
│   └── specs/service-b-spec.md   ← api-service or web-app spec
└── shared-lib/
    └── specs/shared-lib-spec.md  ← library-sdk spec
```

#### Selection criteria
- Multiple services sharing code under a common root (`packages/`, `lib/`, `common/` directories).
- Package manifest dependencies between service and library.
- Shared code is packaged as a distributable unit or internal module.

---

### Composite common chapters

The following chapters appear across multiple composite patterns. They are defined as independent reference templates in `references/composite-chapters/` and reused by the agent when generating composite specs.

| Chapter | Description | Reference file |
|---------|-------------|----------------|
| System architecture | Overall system topology, tier interfaces, deployment diagram, inter-component data flow | `references/composite-chapters/01-system-architecture.md` |
| API contract | Client↔Server full API list, request/response schemas, auth methods, versioning strategy | `references/composite-chapters/02-api-contract.md` |
| Data flow (cross-tier) | Tier-spanning data flow, caching strategy, sync vs. async communication, data consistency | `references/composite-chapters/03-data-flow.md` |

---

## When the user brings their own template

1. Get the path to the template file.
2. Parse the template and extract the chapter outline.
3. Check whether each chapter has a meta-comment describing what it covers.
   - When missing, the agent infers it from the chapter title and confirms with the user.
4. Use the extracted outline for Phase 2 skeleton generation.

---

## When the user adjusts the recommendation

After the user accepts the recommendation, accept chapter additions, removals, or renames.

```
Agent: "I recommend the Web application spec. The outline is:
- Overview
- Architecture
- Screen list
- Routes
- Data model
- Authentication and authorisation
- External integration
- Operations settings

Any chapters to add, remove, or rename?"

User: "Add a 'non-functional requirements' chapter. Place it before 'Operations settings'."

Agent: "Got it. Finalising with:
- Overview
- Architecture
- Screen list
- Routes
- Data model
- Authentication and authorisation
- External integration
- Non-functional requirements   ← added
- Operations settings"
```

---

## Template version management

Each template file starts with version information.

```yaml
---
template_name: web-app
template_version: 0.1.0
last_updated: 2026-05-01
---
```

The consuming project's `wbs.json` records the template version, guaranteeing reproducibility.

---

## Future templates

After OSS release, the following templates may be added in response to user requests:

- Data warehouse / DWH spec
- Machine-learning pipeline spec
- Infrastructure spec (IaC, Terraform, Kubernetes)
- Mobile app spec (iOS / Android / React Native / Flutter)
- Blockchain / smart-contract spec
- Game-design spec

Requests are received via GitHub Issues.
