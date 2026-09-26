---
description: Create or refine a production-grade PRD with explicit readiness and blocking decisions
agent: planner
model: openai/gpt-5.6-sol
---

# Product Requirements Workflow

## Optional User Model Selection

The user may choose the model for this workflow in natural language.

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
- Opus → Claude Opus 5.5
- DeepSeek → DeepSeek V4.1 Flash

If the requested model differs from the current planner model, route the substantive work through the model-selectable planning worker using the explicit per-task model override.

The user's model choice changes only the model. It does not change this workflow's role, authority, permissions, acceptance criteria, or safety rules.

If the requested model is unavailable, stop clearly rather than silently substituting another model.


Create or refine the production PRD for the requested product or feature.

Do not design the implementation architecture yet.
Do not implement application code.

## Stage 1 — Load Product Context

Read only the information needed to understand:

- any relevant user-confirmed discovery brief under `docs/discovery/`
- the problem
- target users
- goals
- non-goals
- business constraints
- technical constraints explicitly imposed by the user or existing system
- security/compliance requirements
- cost expectations
- deployment or operational constraints
- existing product behavior when modifying an existing system

Do not invent requirements merely to make the PRD look complete.

When a relevant discovery brief exists:

- treat confirmed decisions as product context
- preserve its terminology where practical
- do not re-ask resolved questions unless new evidence conflicts with them
- carry explicit non-goals and unresolved questions forward

## Stage 2 — Identify Ambiguities

Classify unanswered questions as either:

### Blocking Questions

Questions that prevent the PRD from being safely approved or would materially change:

- product scope
- user behavior
- contractual/API behavior
- security or compliance requirements
- data ownership
- critical business rules
- cost boundaries

### Non-Blocking Assumptions

Questions that can safely be represented as explicit assumptions without preventing architecture work.

Do not hide uncertainty.

## Stage 3 — Produce the PRD

Include, where applicable:

### Document Metadata

- document ID
- title
- version
- status
- owner
- related documents

### Problem Statement

Explain the problem being solved and why it matters.

### Goals

State measurable intended outcomes.

### Non-Goals

Explicitly identify what is outside scope.

### Users and Actors

Identify:

- user types
- system actors
- operators/admins
- external systems

### User Journeys

Describe the important end-to-end user journeys.

### Functional Requirements

Give requirements stable identifiers such as:

`FR-1`, `FR-2`, ...

Requirements must be:

- testable
- unambiguous
- scoped
- implementation-neutral unless technology is an explicit constraint

### Validation and Error Behavior

Where relevant define:

- validation rules
- user-visible errors
- conflict behavior
- idempotency requirements
- retry expectations

### Security and Privacy Requirements

Where relevant define:

- authentication
- authorization
- secrets
- sensitive data
- privacy
- audit requirements
- abuse prevention

### Reliability Requirements

Where relevant define:

- availability
- failure behavior
- RTO/RPO
- consistency expectations
- recovery requirements

### Performance Requirements

Where relevant define measurable:

- latency
- throughput
- payload limits
- scale assumptions

### Observability Requirements

Where relevant define:

- logging
- metrics
- tracing
- alerting
- auditability

### Cost Constraints

Where relevant define:

- fixed-cost limits
- expected usage envelope
- scale assumptions
- prohibited expensive infrastructure where explicitly required

### Acceptance Criteria

Give acceptance criteria stable identifiers such as:

`AC-1`, `AC-2`, ...

Acceptance criteria must be independently verifiable.

### Assumptions

List every non-blocking assumption.

### Open Questions

Separate:

- blocking questions
- non-blocking questions

## Stage 4 — Readiness Gate

Return `PRD_READY` only when:

- the problem is clear
- scope is clear
- goals and non-goals are clear
- critical functional requirements are testable
- material security/reliability/cost constraints are captured
- acceptance criteria are present
- no unresolved blocking product decision remains

Return `PRD_BLOCKED` when a missing decision prevents safe architecture work.

If blocked, report:

### Blocking Decision

State the unresolved decision.

### Why It Blocks Architecture

Explain the impact.

### Required Input

Ask for only the minimum clarification required.

## Blocked Output Contract

Whenever this workflow cannot safely continue, the blocked response must contain these fields:

### Blocking issue

State exactly what is missing, conflicting, unsafe, or unresolved.

### Owner

Use exactly one of:

- `PRODUCT`
- `ARCHITECTURE`
- `PROJECT_INIT`
- `SPECIFICATION`
- `REPOSITORY`
- `USER_APPROVAL`

Choose the owner that must resolve the blocker.

### Why it blocks

Explain why this stage cannot safely continue without the decision or correction.

### Required action

State the minimum action, clarification, or correction required to unblock the workflow.

### Next command

State the exact next workflow command to run after the blocker is resolved.

Use only one of:

- `/grill`
- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`

If a user clarification or repository cleanup must happen first, say so in `Required action`, then name the command to rerun in `Next command`.

The final line must be the workflow's blocked status token and nothing may appear after it.

## Storage

Store approved PRDs under:

`docs/prd/`

Do not create architecture or application code.

## Output Status

If the PRD is ready for architecture, finish with exactly:

`PRD_READY`

If a blocking decision remains, use the Blocked Output Contract.

For a simple PRD blocker, the usual owner is `PRODUCT` and the next command is `/prd`.

When the blocker consists of multiple coupled product decisions, unclear priorities, or a large ambiguous idea, prefer `/grill` to resolve the decision frontier before rerunning `/prd`.

Finish with exactly:

`PRD_BLOCKED`

Do not output anything after the final status token.
