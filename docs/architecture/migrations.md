# Database Migrations Strategy

This document defines how database schema changes are managed in eQueue.

The goal is a simple, transparent migration system suitable for a learning-focused project.

---

## Approach

eQueue uses **ordered SQL migrations** applied sequentially.

- Migrations are plain SQL files
- Files are numbered and immutable once applied
- PostgreSQL is the single source of truth

No ORM-based migration tool is used.

---

## Directory Structure

```text
db/
  migrations/
    001_create_jobs_table.sql
    002_add_indexes.sql
    003_add_puzzle_tables.sql
````

---

## Migration Tracking

A dedicated table tracks applied migrations:

```sql
schema_migrations (
  version     text primary key,
  applied_at  timestamptz not null
)
```

* Each migration file name (e.g. `001_create_jobs_table.sql`) is stored as `version`
* A migration is applied **only if not already present** in this table

---

## Application Rules

* Migrations are applied in filename order
* Each migration runs inside a transaction
* If a migration fails, it is rolled back and not recorded
* Applied migrations are never modified; new changes require new files

---

## Non-Goals

* No automatic schema diffing
* No rollback migrations
* No branching or environment-specific migrations

Schema evolution is explicit and forward-only.

---

## Rationale

This approach:

* keeps schema changes readable and reviewable
* avoids tool-specific abstractions
* mirrors common production patterns (Flyway-style)

It is sufficient for coordinating schema evolution during early development.
