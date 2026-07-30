---
template_name: batch-system
template_version: 0.1.0
last_updated: 2026-05-01
description: Batch-system spec template. For scheduled jobs, data pipelines, COBOL batch jobs, and similar.
---

# Batch-system spec template

This template defines the chapter outline for the spec of a scheduled or event-driven background-processing system.

Designed for COBOL + JCL, cron / systemd timers, Spring Batch, Apache Airflow, Celery, Sidekiq, AWS Batch, AWS Lambda scheduled runs, ETL data pipelines, etc.

---

## Chapter outline

### Chapter 1: Overview

<!-- meta: business purpose of the batch system as a whole. -->

#### 1.1 Business purpose
- The business problem this batch system solves
- Position in the business cycle (monthly, weekly, daily, real-time)

#### 1.2 Major job groups
- Major job categories (aggregation, transfer, integrity check, etc.)
- Representative jobs per category

#### 1.3 Related systems
- Sources of input data
- Consumers of output data

---

### Chapter 2: Architecture overview

<!-- meta: structure of the batch execution platform. -->

#### 2.1 Technology stack
- Language / framework
- Scheduler (cron / Airflow / Spring Batch / JCL, etc.)
- Job runtime (on-prem / cloud / container)

#### 2.2 Job execution model
- One-shot / chained / DAG-driven
- Parallelism
- Resource allocation

#### 2.3 Input/output data stores
- Database / file storage / message queue
- Data formats (CSV, JSON, XML, fixed-length, Parquet, etc.)

---

### Chapter 3: Class / Module Design

<!-- meta: internal structure — classes, modules, and their relationships. -->

#### 3.1 Module overview

| Module / package | Responsibility | Key classes | Dependencies |
|:----------------|:-------------|:-----------|:------------|
| ... | ... | ... | ... |

#### 3.2 Class catalogue

| Class | Kind | Module | Responsibility | Depends on | Source |
|:------|:----|:-------|:-------------|:----------|:-------|
| ... | ... | ... | ... | ... | [REF: ...] |

#### 3.3 Class diagram (Mermaid)
Include a `classDiagram` for key subsystems. Split per module if >15 classes (see SKILL.md Split rule).

#### 3.4 Module dependency diagram (Mermaid)
Show the direction of dependencies between top-level modules using `graph TD` or `flowchart TD`.

---

### Chapter 4: Job catalogue

<!-- meta: inventory of all jobs. The pillar of verification. -->

#### 3.1 Job catalogue
| Job ID | Job name | Kind | Frequency | Expected runtime | Primary data |
|---------|---------|------|---------|------------|------------|
| JOB-001 | Daily sales aggregation | aggregation | daily 02:00 | 30 min | sales |
| JOB-002 | User deactivation | integrity | monthly (1st) | 2 hours | users |
| ... | ... | ... | ... | ... | ... |

#### 3.2 Per-job details
For each job, describe:
- Business purpose
- Input data source
- Processing
- Output destination
- Execution user / privileges
- Execution host / container image
- Resource requirements (CPU / memory / disk)

---

### Chapter 5: Triggers and schedule

<!-- meta: when and on what trigger each job runs. -->

#### 5.1 Schedule definitions
| Job ID | Schedule expression | Timezone | Business days only |
|---------|----------------|-----------|------------|
| JOB-001 | `0 2 * * *` (cron) | Asia/Tokyo | yes |
| ... | ... | ... | ... |

#### 5.2 Event triggers
- File-arrival triggers
- Message-arrival triggers
- Upstream-job completion triggers

#### 5.3 Business-calendar handling
- Business-day / non-business-day handling
- Special handling at month start / end
- Holiday-calendar source

---

### Chapter 6: Data flow

<!-- meta: input → transform → output. Make data movement traceable. -->

#### 6.1 Data-flow diagram
- Data flow across major jobs (Mermaid notation, etc.)
- Path from data sources to final outputs

#### 6.2 Per-job data I/O
For each job:
- Input data
  - Source (table / file / API)
  - Expected count / size
  - Extraction conditions
- Processing
  - Main logic
  - Aggregation unit
  - Exceptional-data handling
- Output data
  - Destination
  - Format
  - Hand-off to downstream jobs

#### 6.3 Intermediate-data management
- Work tables / temporary files
- Retention period / cleanup policy

---

### Chapter 7: Data Model

<!-- meta: persistent data structures referenced by batch jobs. -->

#### 7.1 Referenced database tables

| Table | Database | Purpose | Read/Write | Key columns | REF |
|:------|:---------|:-------|:---------:|:----------|:----|
| orders | Main DB | Order records | Read | id, status, amount | [REF: ...] |
| users | Main DB | Customer master | Read | id, name, email | [REF: ...] |
| sales_summary | DW | Aggregated sales | Write | date, total, count | [REF: ...] |
| ... | ... | ... | ... | ... | ... |

#### 7.2 File record layouts

For batch jobs that process files (CSV, fixed-length, etc.):

| File | Format | Encoding | Delimiter | Record length | Header line |
|:-----|:------|:--------|:---------|:------------:|:----------:|
| input/sales_*.csv | CSV | UTF-8 | comma | variable | Yes |
| output/daily_report.txt | fixed-length | Shift_JIS | - | 200 bytes | No |
| ... | ... | ... | ... | ... | ... |

Per-file field definitions (expand in chapter body):

| # | Field name | Start | Length | Type | Required | Description |
|:-:|:----------|:----:|:-----:|:----|:--------:|:-----------|
| 1 | date | 1 | 10 | date(YYYY-MM-DD) | ✅ | Sales date |
| 2 | item_code | 11 | 20 | string | ✅ | Item master code |
| 3 | quantity | 31 | 6 | integer | ✅ | Units sold |
| ... | ... | ... | ... | ... | ... | ... |

#### 7.3 Domain rules
- Record-level validation rules
- Data integrity constraints
- State transitions for entities tracked across job runs

---

### Chapter 8: Error handling and retry policy

<!-- meta: behaviour on failure, including idempotency. -->

#### 8.1 Error classification
| Error kind | Example | Retryable? | Response |
|----------|----|-----------|------|
| Input-data anomaly | malformed format | not retryable | log anomaly separately, continue downstream |
| Transient system failure | DB connection failure | retry up to 3 times | alert on final failure |
| Data-integrity anomaly | duplicate key | not retryable | fail the entire job |
| ... | ... | ... | ... |

#### 8.2 Retry specification
- Retry interval (fixed / exponential backoff)
- Maximum retry count
- Logic that decides whether an error is retryable

#### 8.3 Idempotency
- Idempotency guarantees per job
- Whether the same input may be processed multiple times
- Presence of a checkpoint mechanism

#### 8.4 Error notifications
- Notification channels (email / Slack / PagerDuty)
- Notification levels (WARN / ERROR / CRITICAL)
- Notification body templates

---

### Chapter 9: Recovery procedures

<!-- meta: incident runbook. Detailed enough that an operator can act on it. -->

#### 9.1 Recovery per failure scenario
| Scenario | Blast radius | Recovery steps | Expected recovery time |
|---------|---------|---------|------------|
| Job-execution failure | single job | check input → manual re-run | 30 min |
| Data corruption | propagates downstream | restore from backup → re-run | 4 hours |
| ... | ... | ... | ... |

#### 9.2 Partial re-run
- Whether the job can resume from the interruption point
- How to use the checkpoint mechanism

#### 9.3 Undo operations
- How to cancel the result of an already-executed job
- Data-correction commands

#### 9.4 RTO / RPO
- Expected Recovery Time Objective
- Expected Recovery Point Objective

---

### Chapter 10: Operations calendar and dependencies

<!-- meta: temporal dependencies between jobs. -->

#### 10.1 Job-dependency graph
- DAG diagram (Mermaid notation, etc.)
- Dependency conditions (on success / on failure / on completion)

#### 10.2 Execution timeline
- One day's job schedule visualised on a timeline
- Identification of peak time windows

#### 10.3 Monthly / yearly cycles
- Day-of-month for monthly batches
- Fiscal-year rollover processing
- End-of-period processing

---

### Chapter 11: Monitoring / alerts

<!-- meta: what the operators look at. -->

#### 11.1 Monitoring items
| Target | Method | Threshold | Action |
|---------|---------|---------|------|
| Job success/failure | log parsing | immediate on failure | alert |
| Job duration | metrics | expected duration + 20% | warning |
| Record count | aggregation query | past mean ± 30% | warning |
| ... | ... | ... | ... |

#### 11.2 Log specification

| Log type | Output | Format | Level | Retention | Source config |
|:---------|:-------|:------|:-----|:---------|:-------------|
| Job execution log | stdout | JSON (structured) | info~error | 90 days | config/logger.rb:15 |
| Job scheduler log | scheduler.log | plain text | info~warn | 30 days | config/scheduler.rb:8 |
| Error log | stderr | JSON (structured) | warn~fatal | 1 year | config/logger.rb:30 |
| Audit trail | audit.log | CSV | info | 3 years | lib/audit.rb:5 |

Log level definitions:
| Level | Meaning | Output |
|:------|:--------|:-------|
| DEBUG | Detailed diagnostic info (dev only) | Dev environment |
| INFO | Normal operation messages | Always |
| WARN | Warning conditions | Always |
| ERROR | Recoverable errors | Always |
| FATAL | Unrecoverable errors | Always |

#### 11.3 Dashboards
- Links to primary dashboards
- Displayed items

---

### Chapter 12: External interfaces

<!-- meta: external systems, file transfers, and databases the batch jobs interact with. -->

#### 12.1 External interface inventory

| IF-ID | Name | Type | Protocol | Direction | Purpose |
|:------|:-----|:----|:---------|:--------:|:--------|
| BIF-001 | Sales DB | Database | PostgreSQL | Read | Source data for aggregation |
| BIF-002 | Report server | File transfer | SFTP | Upload | Deliver output files |
| BIF-003 | Notification API | REST API | HTTPS | Outbound | Alert on job failure |
| ... | ... | ... | ... | ... | ... |

#### 12.2 Details per interface
- Connection / authentication method
- Schedule / trigger
- Data format and volume
- Failure behaviour

---

### Chapter 13: Known constraints and unresolved items

<!-- meta: spec credibility safeguard. -->

#### 12.1 Known technical constraints
- Maximum concurrency
- Maximum data volume that can be processed
- Known performance issues

#### 12.2 Unresolved items
- Place the `abandoned` entries from the Question Bank here

---

## Customisation guidance

### COBOL + JCL
- Add a "JCL step details" section to Chapter 3.
- Add a "COPYBOOK specification" section to Chapter 5.

### Apache Airflow
- Rewrite Chapter 8 around "DAG definitions".
- Explicitly state the SLA of each DAG in Chapter 9.

### Data pipeline (ETL)
- Restructure Chapter 5 into three sections: Extract / Transform / Load.
- Add a separate chapter for schema-change management.

### Primarily event-driven
- Rewrite Chapter 4 around "event definitions".
- Replace the dependency graph in Chapter 8 with an event-flow diagram.

Customisation is finalised in dialogue with the user after Phase 1 template selection.
