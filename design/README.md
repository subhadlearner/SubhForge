# SubhForge v0.2 Design Documents

This directory uses a **single-normative-home** rule:

> **Every rule has exactly one authoritative home. Other documents reference that rule; they do not redefine it.**

## Authority Map

| Document | Owns |
|---|---|
| `V0.2-ARCHITECTURE.md` | Structural architecture, authority planes, logical agents, requirement/traceability architecture, tooling/model/skill/MCP/context boundaries, implementation dependency order, non-goals |
| `V0.2-WORKFLOW-CONTRACTS.md` | Lifecycle semantics, readiness/grooming, work-plan behavior, verification/evidence semantics, escalation, reconciliation, status/resume, project-version upgrade behavior |
| `V0.2-ARCHITECTURE-REVIEW.md` | AR backlog, case evidence, POC results, human decisions, review history, cross-reference ledger |
| `V0.2-ARCHITECTURE-REVIEW-TOOLING.md` | **Temporary** one-time Architecture Fitness Review execution tooling: `/arch-*` agents/capabilities, durable AR state contract, review workflow, model routing, safety/removal rules |
| `V0.2-QUALIFICATION.md` | Validation strategy, fixtures, scenario pass criteria, dogfood, adversarial qualification, RC/stable-release evidence |
| `SUBHFORGE-DELIVERY-TIMELINE.md` | Dates, milestones, schedule checkpoints only |

## Review Promotion Rule

During Architecture Fitness Review:

1. the AR case and evidence live in `V0.2-ARCHITECTURE-REVIEW.md`;
2. temporary review execution follows `V0.2-ARCHITECTURE-REVIEW-TOOLING.md`;
3. Subhadeep makes the consequential decision;
4. the accepted normative result is promoted to its owning Architecture or Workflow document;
5. Qualification is updated only when proof obligations/scenario expectations change;
6. Timeline is updated only when dates/checkpoints change.

The Review document therefore preserves **why** a decision was made; it does not become a second copy of the final rule.

## Stable Section IDs

Section numbers inherited from the former consolidated plan are intentionally retained even when they are non-contiguous (for example §10.1, §19, §29A, §31A).

They act as stable design references, similar to durable FR/NFR IDs. Renumbering solely for cosmetic continuity would create unnecessary reference churn.

## Split Audit Rule

The migration manifest in `V0.2-ARCHITECTURE-REVIEW.md` is non-normative. It exists only to prove where material from the former monolithic plan moved.

A former rule may disappear only when it is either:

- moved to a named normative home; or
- explicitly listed as superseded.
