---
name: adversarial-check
description: Fresh-context adversarial challenge for non-trivial, high-risk, or hard-to-reverse decisions. Use to surface hidden assumptions and contract violations before the artifact is treated as settled.
metadata:
  source_type: community-grounded-adaptation
  source: Addy Osmani
---

# Adversarial Check

A confident artifact is not automatically a correct artifact.

Use this skill selectively for decisions where a hidden assumption would be expensive to discover later.

## Trigger examples

- auth/security/IAM
- concurrency/idempotency/ordering
- destructive migration
- data integrity/recovery
- public contracts
- financial/irreversible behavior
- high-lock-in architecture

Do not use it for mechanical or obviously low-risk changes.

## Extract

Give the fresh reviewer:

### Artifact

The smallest reviewable decision/diff/text.

### Contract

The requirements and invariants it must satisfy.

Do not provide the author's claimed conclusion or reasoning narrative.

## Adversarial prompt posture

Find what is wrong or unsafe.

Look for:

- unstated assumptions
- edge cases
- hidden coupling/shared state
- contract violations
- security boundary failures
- failure/recovery gaps
- compatibility breaks
- untestable guarantees

Do not invent defects merely to be adversarial.

## Reconcile

The orchestrator, not the adversary, decides how to classify findings:

- contract/context misread
- valid actionable issue
- valid accepted trade-off
- unsupported/noise

A fresh reviewer can lack context. Re-read the artifact before accepting a finding.

## Bound the loop

If the artifact changes materially, run at most one additional fresh pass automatically.

Two substantive unresolved cycles mean the artifact needs human/architecture escalation, not more review churn.
