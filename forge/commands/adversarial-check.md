---
description: Fresh-context adversarial challenge for high-risk architecture, specification, migration, security, or contract decisions
agent: planner
model: openai/gpt-5.6-sol
---

# Adversarial Check Workflow

Challenge a high-risk artifact before relying on it.

This command is not a replacement for `/verify` or `/review`.
It does not become the decision authority.

Load the global `adversarial-check` skill.

## Optional User Adversary Model Selection

Because this command exists specifically to run an adversarial review, a model phrase in this command selects the **adversary model**.

Examples:

```text
Use GPT.
Use Terra.
Use Luna.
Use Claude.
Use Haiku.
Use Opus.
Use DeepSeek.
```

Aliases resolve as:

- GPT / OpenAI / Sol → GPT-5.6 Sol
- Terra → GPT-5.6 Terra
- Luna → GPT-5.6 Luna
- Claude / Sonnet → Claude Sonnet 5
- Haiku → Claude Haiku 4.5
- Opus → Claude Opus 5
- DeepSeek → DeepSeek V4.1 Flash

If the user explicitly selects a model, delegate the fresh-context challenge to `adversary-flex` using Kilo's explicit per-task model override.

If no model is selected, use the default DeepSeek `adversary`.

The top-level planner only extracts the artifact/contract and reconciles the result. It must not reinterpret the requested adversary model as its own workflow-model selection.

If the requested adversary model is unavailable, stop clearly rather than silently substituting another model.

## How the User Should Invoke This Command

The user should identify the artifact or decision they want challenged and, when useful, the risk they are particularly concerned about.

The user does not need to construct the artifact/contract extraction manually; the planner should derive it from the repository.

Example — normal/default adversary:

```text
/adversarial-check

Review the authentication and authorization design in the current architecture.

Focus especially on:
- privilege escalation
- tenant isolation
- token/session failure modes
- operational recovery

Use the normal adversarial path.
```

Example — concurrency/data-integrity decision:

```text
/adversarial-check

Challenge the DynamoDB idempotency and concurrency design in ADR-007 and the related architecture section.

Try to find any sequence of concurrent requests, retries, or duplicate events that can violate the stated uniqueness/data-integrity guarantees.
```

Example — user-directed Opus:

```text
/adversarial-check

Use Opus directly for this review.

Review the production cross-account IAM and event-ingestion architecture in ADR-011 and the current architecture document.

I want a premium fresh-context challenge focused on trust boundaries, confused-deputy risks, privilege escalation, failure recovery, and assumptions that could create a large production blast radius.
```

The last example is an explicit user authorization for that specific Opus adversarial invocation. Do not require a prior DeepSeek pass or an additional justification.

## Stage 1 — Select the Reviewable Claim

Identify the smallest artifact that carries the high-risk decision:

- architecture decision or ADR
- specification behavior/invariant
- migration/cutover plan
- IAM/security policy design
- concurrency/idempotency design
- public API/event contract
- recovery strategy
- other high-blast-radius decision

State why the decision is material.

## Stage 2 — Extract Artifact + Contract

Prepare only:

### Artifact

The smallest relevant text/diff/design.

### Contract

The requirements, invariants, acceptance criteria, ADR constraints, or guarantees it must satisfy.

Do not include the author's preferred conclusion or reasoning narrative in the adversary input.

## Stage 3 — Select Adversarial Model

### Explicit user selection

When the user explicitly selects an adversary model:

1. map the user's alias to the exact supported model
2. delegate to `adversary-flex` with that explicit per-task model override
3. treat the user's request as authorization for that specific model invocation
4. do not run the default DeepSeek adversary first
5. do not add another adversary unless the user asks

### Default

When the user does not select a model:

- delegate to the default `adversary` subagent (DeepSeek Flash)
- treat DeepSeek as the cost-controlled fresh-context adversary

In every case, the adversary must try to find ways the artifact can fail its contract rather than validate the author's confidence.

## Stage 4 — Reconcile Findings

For every material finding classify it as exactly one:

- `CONTRACT_MISREAD`
- `ACTIONABLE`
- `ACCEPTED_TRADEOFF`
- `UNSUPPORTED_NOISE`

Re-read the artifact before accepting the adversary's claim.

For `ACTIONABLE` findings, propose or apply the correction only within the current stage's authority.

For `ACCEPTED_TRADEOFF`, document the consequence and why it is accepted.

## Stage 5 — Decide Whether Agent-Proposed Claude Escalation Is Justified

This stage applies only when Stage 3 used the default DeepSeek path.

After the owning adversarial-check orchestrator reconciles the DeepSeek findings:

### Sonnet escalation

Consider `adversary-sonnet` when a material design uncertainty remains and an independent model-family opinion would materially improve confidence.

Examples:

- security/trust-boundary reasoning
- concurrency or consistency assumptions
- public contract compatibility
- migration/cutover design
- a material disagreement between the default adversary and the Sol planner

Before an agent-proposed Sonnet call:

1. explain why a paid cross-model review is useful
2. ask for explicit user approval
3. after approval, delegate to `adversary-sonnet`
4. provide artifact + contract + unresolved material findings only

### Opus escalation

Consider `adversary-opus` only when at least one of these is true:

- the decision is unusually high-risk and hard to reverse
- failure could cause serious security, authorization, data-loss, corruption, or recovery impact
- the decision establishes a public/external contract that is very expensive to change
- the design contains distributed-concurrency, ordering, idempotency, or consistency guarantees that remain non-obvious
- the default adversary surfaced conflicting/material findings that Sonnet cannot confidently reconcile
- the architecture has major irreversible lock-in or recurring-cost consequences

If none apply, do not use Opus.

If Opus escalation is justified:

1. explain why DeepSeek + Sol, and any already-used Sonnet review, are insufficient for this decision
2. ask for explicit user approval
3. only after approval, delegate to `adversary-opus`
4. provide artifact + contract + only unresolved material findings
5. reconcile the Opus result; do not treat it as automatic authority

The approval/justification sequence is not required when the user explicitly selected Sonnet or Opus in Stage 3.

## Stage 6 — Bounded Recheck

When the default DeepSeek path was used and no Opus escalation occurred, one additional DeepSeek adversarial pass may be run only when the artifact changed materially.

When a user-directed adversary path was used, do not add a DeepSeek pass automatically.

Do not exceed two default adversarial cycles automatically.

An approved Claude escalation replaces further automatic adversarial cycling for that decision unless the user explicitly requests another model.

If substantive unresolved findings remain after the bounded process, escalate to the owning workflow/human rather than grinding.

## Output

Return a concise reconciliation report.

Finish with:

`ADVERSARIAL_CLEAR`

when no unresolved material finding remains.

Finish with:

`ADVERSARIAL_FINDINGS`

when a material finding still requires a decision or correction.

These statuses are advisory risk signals, not implementation completion or merge verdicts.
