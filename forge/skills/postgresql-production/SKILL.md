---
name: postgresql-production
description: PostgreSQL production guidance for schema design, constraints, indexes, transactions, concurrency, query plans, migrations, pooling, JSONB, pagination, and operational performance. Use when a project uses PostgreSQL.
metadata:
  source_type: official-doc-grounded
  vendor: PostgreSQL
---

# PostgreSQL Production Engineering

## Authority

Use the PostgreSQL version, migration tooling, ORM/driver, and consistency model approved by the project.

## Data model

- Encode invariants with appropriate types, `NOT NULL`, `CHECK`, `UNIQUE`, primary keys, and foreign keys rather than application checks alone.
- Choose keys deliberately; do not introduce surrogate IDs when a natural/business uniqueness constraint is still required.
- Normalize by default. Denormalize only for a measured read or operational need.
- Treat JSONB as a deliberate modeling choice, not an escape hatch from schema design.

## Transactions and concurrency

- Keep transactions short.
- Choose isolation level from the actual anomaly/consistency requirement.
- Understand that MVCC does not eliminate write conflicts or locking.
- Lock rows/tables only when needed and in a consistent order.
- Use atomic SQL, unique constraints, upserts, or explicit locks to prevent check-then-write races.
- Design retry behavior for serialization/deadlock failures at the transaction boundary, not inside arbitrary statements.

## Indexing and queries

- Create indexes from real access patterns and query predicates.
- Consider composite-column order, selectivity, sort requirements, and covering opportunities.
- Remember indexes increase write/storage/vacuum cost.
- Use `EXPLAIN (ANALYZE, BUFFERS)` on representative environments for performance investigations; do not infer performance from SQL appearance alone.
- Avoid N+1 query patterns.
- Prefer keyset/seek pagination for large or frequently changing datasets where offset pagination becomes expensive or unstable.

## Operations

- Use connection pooling and bounded application pool sizes.
- Do not treat maximum server connections as an application target.
- Plan schema migrations for lock duration, table size, backward compatibility, rollback/roll-forward, and multi-version deployments.
- Understand autovacuum/analyze behavior before changing defaults.
- Monitor slow queries, lock waits, deadlocks, connection pressure, cache behavior, replication lag, disk growth, and vacuum health as applicable.

## Safety

- Parameterize values; never construct SQL from untrusted input.
- Grant least privilege to application roles.
- Verify version-specific SQL, planner behavior, DDL locking, extension behavior, and operational limits in current PostgreSQL documentation.
