---
name: sqlite-production
description: SQLite production guidance for embedded/local databases, transactions, WAL, locking, concurrency, foreign keys, indexes, migrations, backups, and query performance. Use only when the approved persistence technology is SQLite.
metadata:
  source_type: official-doc-grounded
  vendor: SQLite
---

# SQLite Production Engineering

## Authority

Use SQLite only when approved by project architecture. Do not silently replace PostgreSQL, a managed database, or another persistence technology with SQLite.

## Correctness

- Enable and verify foreign-key enforcement when the application depends on it.
- Use explicit transactions for multi-statement changes that must be atomic.
- Use parameterized queries for values.
- Define uniqueness and other invariants in the schema.
- Treat type affinity and dynamic typing deliberately; do not assume PostgreSQL-style strict typing unless using an approved STRICT table design.

## Concurrency

- SQLite supports many readers but write concurrency is constrained by its file-based locking model.
- Consider WAL mode for suitable local/server-side workloads, but understand checkpointing and filesystem constraints.
- Keep write transactions short.
- Configure a bounded busy timeout/retry policy when transient lock contention is expected.
- Never put an SQLite database on a network filesystem unless current SQLite guidance and the target filesystem guarantees make it safe.

## Performance

- Create indexes from actual query patterns.
- Use `EXPLAIN QUERY PLAN` when investigating query behavior.
- Avoid unnecessary indexes because each adds write and file-size cost.
- Batch related writes in transactions.
- Be explicit about pagination and ordering.

## Migrations and backup

- Version schema migrations and make them reproducible.
- Test migrations against realistic data sizes.
- Prefer SQLite's supported backup mechanisms rather than copying a live database file blindly.
- Plan corruption/recovery and backup verification when the data is important.

## Suitability check

Escalate to architecture when requirements include high concurrent write throughput, multi-node writers, advanced server-side access control, large operational teams needing managed HA, or other capabilities SQLite is not designed to provide.

Verify PRAGMA behavior, WAL details, limits, and version-specific features against current sqlite.org documentation.
