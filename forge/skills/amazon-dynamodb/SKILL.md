---
name: amazon-dynamodb
description: DynamoDB production guidance for access-pattern-led single/multi-table design, partition/sort keys, GSIs, conditional writes, transactions, consistency, pagination, TTL, Streams, concurrency, hot partitions, and capacity/cost.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: AWS
---

# Amazon DynamoDB

## Model from access patterns

Before creating a table or index, write the important reads/writes:
- lookup keys
- query partition and sort conditions
- ordering/range requirements
- expected cardinality and item size
- consistency requirement
- write concurrency
- retention/TTL
- event/stream consumers

Design PK/SK and GSIs from those access patterns. Do not use scans as a substitute for data modeling.

## Keys and indexes

- Distribute high-volume writes across partition-key values.
- Use sort-key prefixes/ranges deliberately for hierarchy and queryability.
- Add a GSI only for a real access pattern.
- Remember GSIs add storage/write cost and are eventually consistent.
- Avoid sparse/hot index keys unless the access pattern and volume make them safe.

## Correctness and concurrency

- Prefer conditional writes for optimistic concurrency, uniqueness, and state transitions.
- Use transactions only when atomicity across multiple items is genuinely required.
- Design idempotency for retried writes and asynchronous consumers.
- Distinguish eventually consistent and strongly consistent reads from actual business requirements.
- Do not implement check-then-write uniqueness without a condition/transaction that makes it atomic.

## Queries

- Use `Query` with keys whenever possible.
- Paginate using `LastEvaluatedKey`; do not assume one response contains all matching items.
- Remember filter expressions are applied after read capacity has been consumed.
- Project attributes when it materially reduces payload, but do not overcomplicate ordinary queries.

## Streams and TTL

- Treat Streams as at-least-once event sources and make consumers idempotent.
- TTL expiry is asynchronous; never depend on exact deletion time for authorization or correctness.
- Consider downstream effects when TTL deletions or stream records matter.

## Capacity, reliability, and cost

- Monitor throttling, consumed capacity, latency, item size, hot keys, and GSI behavior.
- Choose on-demand/provisioned/autoscaling from workload and cost evidence.
- Batch operations still have limits and partial/unprocessed results that must be handled.
- Verify current service quotas, item/index limits, global-table behavior, SDK semantics, and pricing against AWS docs.
