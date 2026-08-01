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

## Initial set of 7

The skill ships with the following 7 templates by default. The user may also bring their own template (by specifying a path).

1. **Web application spec** (`templates/web-app.md`)
2. **Batch-system spec** (`templates/batch-system.md`)
3. **API service spec** (`templates/api-service.md`)
4. **Library / SDK spec** (`templates/library-sdk.md`)
5. **CLI tool spec** (`templates/cli-tool.md`)
6. **Mobile app spec** (`templates/mobile-app.md`)
7. **Desktop app spec** (`templates/desktop-app.md`)

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

## 5. CLI tool spec

### Target
- Terminal-based tools consumed via command line.
- Python (Typer/Click/argparse), Node.js (commander/yargs), Go (cobra/urfave/cli), Rust (clap).
- Tools installed via pip / npm / brew / cargo install, with subcommands, flags, and stdout/stderr output.

### Chapter outline
- Overview / tool purpose
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Module architecture (overview)
- Installation
- Command catalogue (subcommands, arguments, exit codes)
- Usage examples (CRUD workflows, pipe integration, error recovery)
- Configuration (file paths, environment variables)
- Output format (stdout, stderr, JSON mode, exit code semantics)
- Internal structure (optional)
- System design
- Known constraints and unresolved items

### Selection criteria
- CLI entry point in manifest: `[project.scripts]` / `console_scripts` (Python), `"bin"` (Node.js), `[[bin]]` (Rust), `package main` + `main()` (Go).
- Argument-parsing library present: typer/click/argparse (Python), commander/yargs (Node.js), cobra/urfave/cli (Go), clap (Rust).
- No web framework import (Flask / Django / Express / FastAPI / Spring).
- No persistent server process (`app.run`, `server.listen`, `uvicorn.run`).

---

## 6. Mobile app spec

### Target
- iOS / Android / cross-platform mobile applications.
- Swift/SwiftUI (iOS), Kotlin/Jetpack Compose (Android), Flutter (Dart), React Native (TypeScript/JavaScript).
- Screen navigation, lifecycle management, platform API integration, and store deployment.

### Chapter outline
- Overview / app purpose and target platform
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Module architecture (Presentation / Domain / Data layers)
- Screen list and transitions (navigation graph, deep links)
- State management (global vs local state, persistence across lifecycle)
- Data persistence and offline-first (local DB, cache strategy, conflict resolution)
- Platform API integration (camera, GPS, biometrics, push, sensors)
- Push notifications (APNs / FCM, payload structure, tap handling)
- Networking and sync (API layer, cache interceptor, background sync, WebSocket)
- Build and deployment (code signing, provisioning, store deployment, CI/CD)
- Design decisions
- Known constraints and unresolved items

### Selection criteria
- iOS project files: `.xcodeproj`, `.xcworkspace`, `Info.plist`, `@main`, `AppDelegate`.
- Android project files: `build.gradle.kts`, `AndroidManifest.xml`, `MainActivity`.
- Flutter: `pubspec.yaml` with `flutter:` section, `main.dart`.
- React Native: `package.json` with `react-native` dependency, `index.js`/`App.tsx`.
- Kotlin Multiplatform: `build.gradle.kts` with `kotlin { android() ios() }`.
- No web framework as the primary interface (mobile is the main artifact).

---

## 7. Desktop app spec

### Target
- Desktop applications with windowed UI, running on Windows / macOS / Linux.
- Electron, Tauri, Qt (C++/Python), WinForms, WPF, macOS SwiftUI.
- Windows, menus, system tray, keyboard shortcuts, and native OS integration.

### Chapter outline
- Overview / app purpose and target platforms
- Feature specifications ← added (see references/outline-tables.md Feature grouping patterns)
- Module architecture (process model, layer composition)
- Window management and menus (window catalogue, menu bar, context menus, dock/tray)
- UI component catalogue (custom controls, theming system, dialog catalogue)
- Platform integration (filesystem, native dialogs, clipboard, drag & drop, OS services)
- State management and persistence (settings, session state, storage backends)
- Auto-update and installer (installer format, code signing, update flow)
- Networking (API communication, local server, LAN discovery, offline behaviour)
- Keyboard shortcuts and accessibility (global shortcuts, screen reader, focus management)
- Build and deployment (packaging, distribution channels, versioning)
- Design decisions
- Known constraints and unresolved items

### Selection criteria
- Electron: `package.json` with `electron` dependency, `electron-builder`/`electron-forge` config.
- Tauri: `tauri.conf.json`, `Cargo.toml` with `tauri` dependency, `src-tauri/` directory.
- Qt (C++): `.pro` file or `CMakeLists.txt` with `find_package(Qt*)`, `QApplication`.
- Qt (Python): `PyQt`/`PySide` import, `.ui` files.
- WinForms / WPF: `.csproj` with `UseWindowsForms`/`UseWPF`, `Form`/`Window` inheritance.
- macOS SwiftUI: `@main struct App: App`, `WindowGroup`, `Info.plist`.
- No web server as the primary interface (desktop is the main artifact).

## Decision tree (template recommendation logic)

Based on the Phase 1 reconnaissance, the agent follows this procedure to recommend a template:

```
1. Does the package manifest define main/module/bin?
   YES → Is there application-startup code?
            NO  → Recommend Library / SDK spec
            YES → Continue

1b. Does the project define a CLI entry point?
    YES → Is there argument-parsing code (typer/click/argparse/commander/cobra/clap)?
             YES → Is the primary interface terminal (no web server, no HTML rendering)?
                      YES → Recommend CLI tool spec
                      NO  → Continue (composite: CLI + web/API)
             NO  → Continue

1c. Does the project target mobile platforms?
    YES → Are there iOS/Android/Flutter/React Native project files?
             YES → Is the primary artifact a mobile app (no web server)?
                      YES → Recommend Mobile app spec
                      NO  → Recommend composite (mobile + API)
             NO  → Continue

1d. Does the project target desktop platforms?
    YES → Are there Electron / Tauri / Qt / WinForms / WPF / SwiftUI project files?
             YES → Is the primary artifact a desktop app (windowed UI, no web server)?
                      YES → Recommend Desktop app spec
                      NO  → Continue
             NO  → Continue

2. Do routing definitions exist?
   YES → Is there HTML rendering (views/templates)?
            YES → Recommend Web application spec
            NO  → Recommend API service spec

3. Are scheduler configuration / batch scripts the main subject?
   YES → Recommend Batch-system spec

4. None of the above / composite type
   → Present multiple candidates and ask the user.
   → Example: "Includes both web app and CLI tool; recommend a merged custom outline."
```

---

## Handling composite projects

Real projects often do not fit into a single template. Handle them as follows.

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
- Blockchain / smart-contract spec
- Game-design spec

Requests are received via GitHub Issues.
