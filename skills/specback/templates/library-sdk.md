---
template_name: library-sdk
template_version: 0.1.0
last_updated: 2026-05-01
description: Library / SDK spec template. For reusable code packages distributed via npm/pip/composer/gem/NuGet, etc.
---

# Library / SDK spec template

This template defines the chapter outline for the spec of a reusable code asset (library / SDK) consumed by other applications.

Designed for packages distributed via npm / pip / composer / gem / NuGet / Maven Central, etc., as well as internal common libraries.

---

## Chapter outline

### Chapter 1: Overview

<!-- meta: purpose and scope of the library. -->

#### 1.1 Library purpose
- The problem this library solves
- Intended consumers
- Differentiation from competing or alternative libraries

#### 1.2 Main features
- 3-5 main features
- Summary of each feature

#### 1.3 License / package information
- License type
- Package name / distribution channel
- Current version

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



### Chapter 3: Installation

<!-- meta: steps to start using the library. -->

#### 3.1 Per-package-manager commands
```bash
# npm
npm install <package-name>

# yarn
yarn add <package-name>

# pip
pip install <package-name>

# composer
composer require <vendor/package-name>

# gem
gem install <package-name>

# NuGet
dotnet add package <PackageName>
```

#### 3.2 Runtime requirements
- Supported language versions
- Supported operating systems
- Required surrounding tools

#### 3.3 Optional dependencies
- Anything extra needed at install time
- Per-feature additional dependencies

---

### Chapter 4: Public API catalogue

<!-- meta: inventory of all public APIs. The pillar of verification. -->

#### 4.1 API catalogue
| API name | Kind | Signature | Summary | Stability |
|------|-----|----------|------|-------|
| `connect()` | function | `connect(config: Config) → Client` | Create a client | stable |
| `Client.query()` | method | `query(sql: string) → Result` | Run a query | stable |
| `parse()` | function | `parse(input: string) → AST` | Parse input | beta |
| ... | ... | ... | ... | ... |

#### 4.2 Module structure
- Module structure inside the package
- Main exports

#### 4.3 Stability levels
- stable: backward compatibility is guaranteed
- beta: may have breaking changes within a major version
- experimental: may change in any version
- deprecated: scheduled for removal

---

### Chapter 5: Usage examples (quick start)

<!-- meta: "read this and start using it" samples. -->

#### 5.1 Minimal example
```javascript
import { connect } from 'mylib';

const client = connect({ host: 'localhost' });
const result = client.query('SELECT 1');
console.log(result);
```

#### 5.2 Examples per major use case
- Use case 1: ...
  ```javascript
  // sample code
  ```
- Use case 2: ...
  ```javascript
  // sample code
  ```

#### 5.3 Advanced usage
- Using custom options
- Error handling
- Asynchronous-processing patterns

---

### Chapter 6: Configuration options

<!-- meta: exhaustive list of all options. -->

#### 6.1 Global configuration
| Option | Type | Default | Description |
|----------|----|----------|------|
| `host` | string | `localhost` | Target host |
| `timeout` | number | `5000` | Timeout (ms) |
| `retries` | number | `3` | Retry count |
| ... | ... | ... | ... |

#### 6.2 Per-feature options
- Detailed options per feature
- Combinability

#### 6.3 Configuration via environment variables
- List of available environment variables
- Precedence order (code > env vars > defaults)

---

### Chapter 7: Compatibility

<!-- meta: supported runtimes and dependencies. -->

#### 7.1 Supported language versions
| Language / runtime | Supported versions | Support status |
|----------------|--------------|------------|
| Node.js | 18 LTS, 20 LTS | active |
| Node.js | 16 | maintenance only |
| ... | ... | ... |

#### 7.2 Dependencies
| Library | Version | Purpose | Required / optional |
|----------|----------|------|----------|
| lodash | ^4.17.0 | utility | required |
| ... | ... | ... | ... |

#### 7.3 Peer dependencies
- Peer-dependency libraries
- Version ranges required of the consuming project

#### 7.4 Compatibility matrix
- Verified status for major combinations
- Known incompatible combinations

---

### Chapter 8: Extension points / plugin system

<!-- meta: how consumers extend the library. -->

#### 8.1 List of extension points
- Hooks / callbacks
- Middleware
- Custom providers

#### 8.2 Plugin API
- Plugin-definition interface
- Plugin lifecycle
- Inter-plugin dependencies

#### 8.3 Existing plugins
- Official plugins
- Notable third-party plugins

---

### Chapter 9: Migration guide

<!-- meta: migration steps from past versions. -->

#### 9.1 Migration from v1.x to v2.x

##### Breaking changes
- Removed APIs
- Signature changes
- Default-value changes

##### Migration steps
- Step-by-step procedure
- Automated migration tool (if any)

##### Code examples
```javascript
// Before (v1.x)
client.connect({ url: 'localhost' });

// After (v2.x)
client.connect({ host: 'localhost' });
```

#### 9.2 Migration from v0.x to v1.x
- (Same shape as above)

---

### Chapter 10: Internal structure (optional)

<!-- meta: internal architecture of the library. For contributors. -->

#### 10.1 Directory structure
- Main directories and their responsibilities

#### 10.2 Major classes / modules

| Class | Kind | Module | Responsibility | Depends on | Source |
|:------|:----|:-------|:-------------|:----------|:-------|
| ... | ... | ... | ... | ... | [REF: ...] |

- Class diagram (Mermaid `classDiagram`) for key subsystems. Split per module if >15 classes (see SKILL.md Split rule).
- Module dependency diagram (`graph TD`) for top-level module relationships.

#### 10.3 Build and test
- Build commands
- Test commands
- Release process

---

### Chapter 11: Known constraints and unresolved items

<!-- meta: spec credibility safeguard. -->

#### 11.1 Known constraints
- Performance ceilings
- Known bugs / workarounds
- Per-platform differences

#### 11.2 Unresolved items
- Place the `abandoned` entries from the Question Bank here

---

## Customisation guidance

### Library also ships a CLI tool
- Add a "CLI command list" section to Chapter 3.
- Add a "CLI usage example" section to Chapter 4.

### TypeScript type definitions matter
- Add a "TypeScript type definitions" section to Chapter 3.
- Document generics and conditional types.

### Multi-package (monorepo)
- Split Chapter 3 per package.
- Describe inter-package dependencies in a separate chapter.

### Brand-new library (no migration guide needed)
- Omit Chapter 8, or use it to describe "future migration policy" only.

Customisation is finalised in dialogue with the user after Phase 1 template selection.
