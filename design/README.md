# SubhForge v0.2 Design Documents

This directory uses a **single-normative-home** rule:

> **Every rule has exactly one authoritative home. Other documents reference that rule; they do not redefine it.**

Current pre-code sequencing and status are tracked in [V0.2-PRE-CODE-CHECKLIST.md](V0.2-PRE-CODE-CHECKLIST.md).

## Authority Map

| Document | Owns |
|---|---|
| [V0.2-PRE-CODE-CHECKLIST.md](V0.2-PRE-CODE-CHECKLIST.md) | Pre-code work sequence, current item, completion evidence, blocking status, and exit gates; it references but does not redefine normative architecture/workflow/qualification rules |
| `V0.2-ARCHITECTURE.md` | Structural architecture, authority planes, logical agents, requirement/traceability architecture, tooling/model/skill/MCP/context boundaries, implementation dependency order, non-goals |
| `V0.2-WORKFLOW-CONTRACTS.md` | Lifecycle semantics, readiness/grooming, work-plan behavior, verification/evidence semantics, escalation, reconciliation, status/resume, project-version upgrade behavior |
| `V0.2-ARCHITECTURE-REVIEW.md` | AR backlog, case evidence, POC results, human decisions, review history, cross-reference ledger |
| `V0.2-ARCHITECTURE-REVIEW-TOOLING.md` | **Temporary** one-time Architecture Fitness Review execution tooling: `/arch-*` agents/capabilities, durable AR state contract, review workflow, model routing, safety/removal rules |
| `V0.2-IMPLEMENTATION-TOOLING.md` | v0.2 implementation handoff: Architecture Review deliverables, v0.1.1 Existing Authority Admission requirement, and the `/spec → /implement → /verify → /review` execution flow |
| `V0.2-QUALIFICATION.md` | Validation strategy, fixtures, scenario pass criteria, dogfood, adversarial qualification, RC/stable-release evidence |
| `SUBHFORGE-DELIVERY-TIMELINE.md` | Dates, milestones, schedule checkpoints only |

## Shared Decision Status Vocabulary

| Status | Meaning |
|---|---|
| **ACCEPTED** | Agreed direction/contract. Reopen only through explicit review with evidence/rationale. |
| **REVIEW** | Must be validated before architecture/implementation freeze. |
| **DEFERRED** | Deliberately outside current scope unless evidence reopens it. |
| **NON-GOAL** | Explicitly rejected scope for v0.2. |

These status meanings apply across the v0.2 design documents and ledgers.

---
## Review Promotion Rule

During Architecture Fitness Review:

1. the AR case and evidence live in `V0.2-ARCHITECTURE-REVIEW.md`;
2. temporary review execution follows `V0.2-ARCHITECTURE-REVIEW-TOOLING.md`;
3. Subhadeep makes the consequential decision;
4. the accepted result is promoted to its **single owning document**: Architecture/Workflow for product-delivery semantics, Qualification for proof/release obligations, or Timeline for schedule-only decisions;
5. other documents keep only cross-references/evidence, never a second normative copy.

The Review document therefore preserves **why** a decision was made; it does not become a second copy of the final rule.

## Stable Section IDs

Section numbers inherited from the former consolidated plan are intentionally retained even when they are non-contiguous (for example §10.1, §19, §29A, §31A).

They act as stable design references, similar to durable FR/NFR IDs. Renumbering solely for cosmetic continuity would create unnecessary reference churn.

## Split Audit Rule

The migration manifest in `V0.2-ARCHITECTURE-REVIEW.md` is non-normative. It exists only to prove where material from the former monolithic plan moved.

A former rule may disappear only when it is either:

- moved to a named normative home; or
- explicitly listed as superseded.
