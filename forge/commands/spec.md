---
description: Decompose an approved architecture into independently implementable specifications
agent: planner
model: openai/gpt-5.6-sol
---

# Specification Workflow

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
- Opus → Claude Opus 5
- DeepSeek → DeepSeek V4.1 Flash

If the requested model differs from the current planner model, route the substantive work through the model-selectable planning worker using the explicit per-task model override.

The user's model choice changes only the model. It does not change this workflow's role, authority, permissions, acceptance criteria, or safety rules.

If the requested model is unavailable, stop clearly rather than silently substituting another model.

### Workflow Model and Adversary Model Are Separate

A plain request such as `use Claude`, `use Terra`, or `use GPT` selects the model that authors and owns the specification workflow.

It does not select the adversary.

Unless separately overridden, high-risk specifications use the default DeepSeek adversary.

To choose a different adversary, use explicit wording such as:

```text
For adversarial review use Opus.
Use Sonnet as the adversary.
Adversary: GPT.
```

The selected specification workflow model remains responsible for reconciling adversarial findings.


Create implementation specifications from the approved PRD and architecture.

Do not implement application code.

## Stage 1 — Preconditions

Read:

- approved PRD
- approved architecture
- relevant ADRs
- project-level `AGENTS.md`
- project initialization result when available

Proceed only when:

- PRD is approved
- architecture returned `ARCHITECTURE_READY`
- required technology baseline is established
- project initialization returned `PROJECT_INIT_READY`
- project-level `AGENTS.md` reflects the approved technology baseline

If any prerequisite is missing or blocked, do not continue.

Return:

`SPEC_BLOCKED`

and state the missing prerequisite.

## Stage 2 — Decompose the Work

Split the approved scope into independently implementable specifications.

Each specification should:

- deliver a coherent unit of value
- have clear acceptance criteria
- minimize unnecessary coupling
- avoid overlapping file ownership where practical
- be suitable for an isolated branch/worktree
- fit within the context budget

Target size:

- preferred: 30K–60K tokens
- warning: 60K–80K tokens
- hard ceiling: 100K tokens

If a specification would exceed the hard ceiling, split it.

### Greenfield Bootstrap and CI Ownership

For a greenfield project, determine whether the approved architecture requires repository/bootstrap work that does not yet exist, including where applicable:

- initial application/project scaffolding
- CI workflow implementation
- infrastructure-as-code bootstrap
- dependency/package configuration
- baseline quality gates
- baseline security/dependency scanning
- deployment pipeline scaffolding

If such work is required, create an explicit early implementation specification for it rather than assuming the repository or CI pipeline already exists.

Prefer a bootstrap specification such as:

`SPEC-000 — Project Bootstrap and CI`

when that naming fits the project.

The bootstrap specification must:

- implement only the architecture-approved tooling and CI/CD approach
- establish the build/test/quality/security gates required by later specifications
- avoid inventing a new technology stack
- avoid implementing unrelated product functionality
- define deterministic acceptance criteria for the bootstrap work

Later specifications that depend on CI, generated project structure, IaC foundations, or repository tooling must declare that bootstrap specification as a prerequisite.

Do not treat selecting a CI provider during `/architect` or documenting it during `/project-init` as equivalent to implementing the CI pipeline.

## Stage 3 — Define Dependencies

For every specification identify:

- prerequisite specs
- external dependencies
- shared contracts
- migration ordering
- deployment ordering where relevant

Avoid circular dependencies.

Mark specs that can safely run in parallel.

## Stage 4 — Specification Content

Each specification must include:

### Identity

- spec ID
- title
- objective

### Scope

- included behavior
- excluded behavior
- non-goals

### Dependencies

- prerequisite specs
- architecture/ADR references
- external dependencies

### Technology Constraints

Record only the approved stack relevant to this specification.

Do not independently choose a different technology.

### Interfaces

Where applicable define:

- APIs
- events
- queues/topics
- file formats
- commands
- integration contracts

### Data

Where applicable define:

- entities
- fields
- indexes
- migrations
- retention/TTL
- consistency expectations

### Behavior

Define normal behavior and important edge cases.

### Validation

Define input and business validation.

### Error Handling

Define expected failures and observable responses.

### Security

Define relevant:

- authentication
- authorization
- secrets
- sensitive data handling
- abuse controls
- applicable OWASP Top 10:2025 risks
- feature-specific security invariants and negative cases
- required executable security evidence
- any project-approved non-waivable security conditions

Do not claim broad OWASP or regulatory compliance. Define objective, testable security criteria.

### Observability

Define relevant:

- logs
- metrics
- traces
- alarms
- correlation IDs

### Performance and Reliability

Define relevant:

- latency
- throughput
- timeout
- retry
- idempotency
- concurrency
- recovery expectations

### Cost Constraints

Record implementation-relevant cost requirements.

### Acceptance Criteria

Every acceptance criterion must be objectively verifiable.

### Testing Requirements

Define the observable test seams before listing individual tests.

For each important behavior identify the highest stable public/contract boundary that can prove it, such as:

- HTTP/API boundary
- message/event handler contract
- domain/application service boundary
- persistence adapter contract
- CLI boundary
- browser/user journey

Then define applicable:

- unit tests
- integration tests
- contract tests
- E2E tests
- negative tests
- boundary tests
- security tests

State `TDD: APPLICABLE` when behavior can be developed safely in red → green vertical slices against stable seams.

State `TDD: NOT_APPLICABLE` with a short reason for work such as pure documentation, mechanical configuration, generated scaffolding, or cases where a meaningful failing behavioral test cannot precede implementation.

Do not require tests against private implementation details merely to increase coverage.

### Verification Requirements

Identify the deterministic checks expected from `/verify`, including applicable:

- build/test/static-analysis checks
- dependency vulnerability checks
- secret scanning
- SAST/IaC/container security checks
- feature-specific security tests
- acceptance-criteria evidence

State which security checks are required versus not applicable.

### Definition of Done

A specification is not complete until:

- implementation is complete
- required tests exist
- factual verification evidence exists under `docs/verification/`
- `/verify` returns `DONE` with `Delivery Gate: CLEAR`, or a separate valid human-authorized waiver establishes `CLEAR_WITH_EXCEPTION`
- `/review` passes with any active waiver visible to reviewers
- CI passes

A waiver does not change a `NOT_DONE` verification result to `DONE`.

## Stage 5 — Parallelism and Branch Safety

Identify whether specs can be implemented concurrently.

When parallel implementation is safe:

- avoid overlapping mutation scope where practical
- document shared dependencies
- recommend separate branches/worktrees

Do not force parallelism where it increases coordination risk.

## Risk-Triggered Adversarial Specification Check

Before returning `SPEC_READY`, adversarially check any specification whose correctness depends materially on:

- security/auth/IAM
- concurrency, ordering, idempotency, transactions, or consistency
- destructive migration or data retention
- irreversible external side effects
- public API/event compatibility
- financial logic
- recovery/rollback guarantees

For each triggered specification:

1. extract the behavior/contract, invariants, acceptance criteria, and relevant architecture constraints
2. determine whether the user separately selected an adversary model
3. if the user selected an adversary, delegate to `adversary-flex` with the explicit per-task model override for that model
4. otherwise delegate to the default `adversary` subagent (DeepSeek Flash)
5. the **owning specification workflow model** reconciles findings against the approved PRD/architecture
6. when the owning workflow model is running through `planning-worker`, invoke it with `MODE: RECONCILE_ONLY`; supply only the existing spec path, adversarial findings, relevant architecture/ADR references needed by those findings, and the challenged contract/invariants
7. do not restart specification decomposition, reload unrelated PRD/architecture material, or recreate unaffected specifications
8. correct only the specification sections required by valid findings
9. when using the default path, run at most one additional DeepSeek adversarial cycle, and only if targeted reconciliation materially changed the challenged behavior; when using a user-directed adversary, do not add another adversary automatically

A plain workflow-model request such as `use Claude` must never be interpreted as an adversary override.

### Reconciliation Cost and Scope Guardrail

Adversarial reconciliation is a focused delta pass.

Normally it should:

- read the challenged specification
- read only architecture/ADR material necessary to adjudicate the finding
- evaluate the findings
- make targeted edits
- report finding dispositions

It must not perform a second full `/spec` run.

After a default DeepSeek pass, the owning specification workflow may propose `adversary-sonnet` when material uncertainty remains and an independent model-family review would materially improve confidence.

Reserve agent-proposed `adversary-opus` for rare critical specifications whose residual risk remains unusually high—for example irreversible migration/data integrity, auth/IAM, public contracts, or distributed consistency with major blast radius.

Any agent-proposed Claude invocation requires explicit user approval. Pass only the artifact, contract, and unresolved material findings. Treat Claude results as evidence, not authority.

If a material issue actually belongs to product or architecture authority, return `SPEC_BLOCKED` and route upstream rather than silently solving it in the specification.

## Stage 6 — Traceability

Each spec should trace back to:

- PRD requirements
- acceptance criteria
- architecture decisions
- ADRs

Do not introduce new product requirements.

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

- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`

If a user clarification or repository cleanup must happen first, say so in `Required action`, then name the command to rerun in `Next command`.

The final line must be the workflow's blocked status token and nothing may appear after it.

## Storage

Store specifications under:

`docs/specs/`

Use stable IDs such as:

`SPEC-001`, `SPEC-002`, ...

## Output Status

If the specification set is complete and implementation-ready, finish with exactly:

`SPEC_READY`

If a prerequisite or material ambiguity prevents safe decomposition, use the Blocked Output Contract.

Routing rules:

- use owner `PRODUCT` and next command `/prd` when the blocker is a requirement or acceptance-criteria ambiguity
- use owner `ARCHITECTURE` and next command `/architect` when the blocker is an architecture/ADR decision
- use owner `PROJECT_INIT` and next command `/project-init` when project initialization is missing or incomplete
- use owner `SPECIFICATION` and next command `/spec` when the issue is local to decomposition and can be corrected without changing upstream decisions

Finish with exactly:

`SPEC_BLOCKED`

Do not output anything after the final status token.
