---
description: Design the production architecture and lock the technology baseline
agent: planner
model: openai/gpt-5.6-sol
---

# Production Architecture Workflow

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

### Workflow Model and Adversary Model Are Separate

In this command, a plain request such as `use Claude`, `use Terra`, or `use GPT` selects the model that **authors and owns the architecture workflow**.

It does not select the adversary.

Unless the user separately specifies an adversary, high-risk architecture decisions use the default DeepSeek adversary.

To override only the adversary, the user must use explicit wording such as:

```text
For adversarial review use Opus.
Use Sonnet as the adversary.
Adversary: GPT.
```

If both are supplied, honor both independently.

Example:

```text
/architect ... Use Claude.
For adversarial review use Opus.
```

means Claude Sonnet authors the architecture, Opus challenges the selected high-risk artifact, and Claude Sonnet remains the owning model that reconciles the findings.


Design the production architecture for the approved PRD.

The architecture stage owns major technology decisions.

Do not implement application code.

The output must provide enough approved technical detail for `/project-init`,
`/spec`, and `/implement` to proceed without inventing the technology stack.

## Stage 1 — Load Architecture Context

Read:

- the approved PRD
- relevant existing architecture when modifying an existing system
- relevant existing ADRs
- project-level constraints from `AGENTS.md` when available

Do not inspect unrelated implementation details unless required to understand an existing system.

## Stage 2 — Identify Constraints

Extract and classify relevant constraints.

Include, where applicable:

- functional constraints
- scale/workload
- reliability
- availability
- performance
- security
- privacy/compliance
- data residency
- observability
- deployment
- operational burden
- team capabilities
- cloud/provider constraints
- cost limits
- existing technology constraints
- compatibility requirements

Do not invent constraints that are absent from the PRD.

Clearly distinguish:

- explicit requirements
- architecture assumptions
- unresolved decisions

## Stage 3 — Evaluate Architecture Options

When meaningful, identify at least two viable architecture approaches.

Compare them on:

- simplicity
- reliability
- security
- scalability
- maintainability
- operational burden
- implementation complexity
- deployment complexity
- estimated cloud cost
- fixed monthly cost
- variable cost behavior
- vendor/service dependencies
- fit with stated project constraints

Do not manufacture alternatives when only one approach is realistically viable.

Select the architecture that best satisfies the approved requirements and constraints.

Document the reasons for significant decisions.

## Stage 4 — Establish the Technology Baseline

The architecture must explicitly decide the technology baseline required for implementation.

Do not leave implementation agents to choose these later.

For a new project, determine and document, where applicable:

### Application Stack

- programming language
- language version
- runtime and version
- application framework
- framework version or major version policy
- API style
- serialization approach
- dependency injection approach when relevant
- package/dependency manager

### Persistence Stack

- database/storage technology
- data-access library or SDK strategy
- schema/model strategy
- migration strategy when applicable
- consistency model where relevant

### Cloud Runtime

- cloud provider
- region
- compute/runtime service
- CPU architecture where relevant
- deployment packaging model
- networking model
- secrets/configuration storage

### Infrastructure as Code

- IaC technology
- IaC language when applicable
- deployment organization
- environment strategy

### Testing Stack

Explicitly select, where applicable:

- unit-test framework
- mocking/test-double framework
- integration-test framework/approach
- E2E-test framework/approach
- contract-test approach
- local cloud-service emulation strategy, if any

### Code Quality and Security Tooling

Explicitly select, where applicable:

- formatter
- linter
- compiler/static analysis
- type checking
- code-quality analyzers
- dependency vulnerability scanning
- secret scanning
- SAST/static security analysis
- IaC security scanning
- container/image scanning
- package provenance/supply-chain controls
- framework-appropriate security testing

### Local Development

Determine:

- required SDK/runtime versions
- package manager
- local execution approach
- environment/configuration approach
- whether Docker is required
- whether cloud credentials are required for local development

### CI/CD Baseline

Determine:

- CI provider
- build strategy
- test gates
- security gates
- IaC validation
- artifact packaging
- deployment approach
- production approval model

Do not choose tools merely to fill every category.

Use `Not Applicable` when a category genuinely does not apply.

## Stage 5 — Technology Decision Rules

Technology choices must be justified by project requirements.

Prefer:

- mature supported technology
- minimal operational burden
- minimal fixed cloud cost
- strong ecosystem support
- straightforward local development
- production-safe defaults
- technologies appropriate to the expected scale

Avoid:

- unnecessary frameworks
- unnecessary infrastructure
- speculative scalability
- multiple languages without a strong reason
- redundant tools
- technologies requiring always-on infrastructure when requirements do not justify it

When the PRD constrains a technology, respect that constraint unless it creates a material technical contradiction.

## Stage 6 — Technology Completeness Gate

Before finalizing the architecture, verify that `/project-init` could determine the implementation stack without guessing.

At minimum, a greenfield application architecture must establish:

- application language
- language/runtime version
- application framework or explicit frameworkless approach
- package manager
- cloud/runtime platform
- database/storage technology
- IaC technology
- unit-test framework
- integration-test approach
- formatting/lint/static-analysis approach
- CI/CD approach

If one of these decisions is genuinely unresolved and required for implementation:

do not silently omit it.

Report:

`ARCHITECTURE_BLOCKED`

Explain:

- the unresolved decision
- viable choices
- relevant trade-offs
- why implementation cannot safely choose it later
- what input is required to resolve it

Do not delegate major technology selection to `/project-init` or `/implement`.

## Stage 7 — Architecture Design

Produce the production architecture.

Include:

### Architecture Overview

Describe:

- system topology
- major boundaries
- responsibility separation
- critical request/data paths

### Major Components

For every major component identify:

- responsibility
- technology/service
- key configuration
- dependencies
- relevant scale or reliability considerations

### Data Model

Where applicable define:

- entities/resources
- keys/indexes
- major access patterns
- consistency requirements
- retention/TTL
- migration considerations

### Data Flow

Describe important flows such as:

- writes
- reads
- authentication
- authorization
- asynchronous flows
- failure flows

### Security Model

Cover, where relevant:

- authentication
- authorization
- secrets
- encryption and key management
- network boundaries
- least privilege
- input validation and output encoding
- sensitive data/logging/privacy
- supply-chain controls
- abuse/throttling/resource exhaustion
- security logging/alerting
- error/exception handling and information disclosure
- applicable OWASP Top 10:2025 risks
- deeper OWASP ASVS-style technical controls for web/API systems where appropriate

The architecture must explicitly decide which security verification capabilities are required for this project and which executable tools/checks will provide evidence.

Do not claim "OWASP compliant" merely because a scanner is selected.

### Observability

Define:

- logs
- metrics
- traces
- alarms
- dashboards
- retention
- correlation/request IDs
- cost controls

### Deployment Strategy

Define:

- environments
- IaC
- CI/CD
- release strategy
- rollback
- configuration
- secrets
- migrations
- production approval

### Failure Modes

Identify material failures and define:

- detection
- behavior
- mitigation
- recovery

### Recovery Strategy

Define:

- backup/recovery
- RTO/RPO where required
- restore process
- deployment rollback
- infrastructure reconstruction

### Cost Characteristics

Estimate:

- fixed recurring cost
- important usage-based cost
- primary cost drivers
- cost risks
- optimization levers

Use assumptions explicitly.

Do not imply precision where pricing depends on uncertain traffic.

## Stage 8 — ADRs

Create ADRs for significant technology and architecture decisions.

Typical ADR candidates include:

- application language/runtime
- application framework when materially consequential
- compute model
- ingress/API model
- persistence technology
- authentication strategy
- asynchronous messaging strategy
- IaC technology
- deployment approach
- observability strategy

Do not create an ADR for trivial implementation details.

Store architecture documentation under:

`docs/architecture/`

Store ADRs under:

`docs/adr/`

## Stage 9 — Technology Baseline Summary

Every architecture document must contain a dedicated section named:

`Technology Baseline`

Use a table similar to:

| Area | Decision | Version / Policy | Rationale |
| --- | --- | --- | --- |
| Application Language | | | |
| Runtime | | | |
| Framework | | | |
| Package Manager | | | |
| Database / Storage | | | |
| Data Access | | | |
| Cloud | | | |
| Region | | | |
| Compute | | | |
| IaC | | | |
| IaC Language | | | |
| Unit Testing | | | |
| Integration Testing | | | |
| E2E Testing | | | |
| Formatting | | | |
| Lint / Static Analysis | | | |
| Security / Dependency Scan | | | |
| CI/CD | | | |

Use `Not Applicable` where appropriate.

Do not leave required cells blank.

## Stage 10 — Project Initialization Handoff

Finish with a section named:

`Project Initialization Handoff`

Provide the exact approved values `/project-init` should place into `AGENTS.md`.

Include:

- runtime
- language
- framework
- database
- cloud
- region
- IaC
- package manager
- unit-test framework
- integration-test approach
- E2E-test approach
- linting
- formatting
- type/static analysis
- dependency/security scanning
- secret scanning
- SAST/IaC/container security checks when applicable
- dependency restore command pattern
- build command pattern
- test command pattern

These values must come from architecture decisions.

`/project-init` must not have to choose them.

## Risk-Triggered Adversarial Gate

Before declaring `ARCHITECTURE_READY`, determine whether the draft contains a high-risk or hard-to-reverse decision.

Trigger the adversarial gate for decisions involving, where applicable:

- authentication/authorization or IAM trust
- destructive migrations or data-loss risk
- concurrency, idempotency, ordering, or distributed consistency
- sensitive/public API or event-contract compatibility
- security-sensitive networking
- financial or irreversible business behavior
- backup/recovery guarantees
- high-lock-in infrastructure or major irreversible cost commitments

For triggered decisions:

1. extract the smallest decision artifact and the requirements/invariants it must satisfy
2. determine whether the user separately selected an adversary model
3. if the user selected an adversary, delegate to `adversary-flex` with the explicit per-task model override that corresponds to that adversary choice
4. otherwise delegate to the default `adversary` subagent (DeepSeek Flash)
5. do not send the decision author's rationale or preferred conclusion
6. the **owning architecture workflow model** reconciles every material finding as contract/context misread, actionable defect, accepted trade-off, or unsupported/noise
7. when the owning workflow model is running through `planning-worker`, invoke it with `MODE: RECONCILE_ONLY`; supply only the existing architecture path, affected ADR path(s), adversarial findings, and relevant contract/invariants
8. in reconciliation, do not restart Stages 1–10, re-read all upstream context, regenerate the architecture, or recreate unaffected ADRs
9. revise only the architecture/ADR sections required by valid findings
10. when using the default path, run at most one additional DeepSeek adversarial cycle, and only if the targeted reconciliation materially changed the challenged decision; when using a user-directed adversary, do not add another adversary automatically

A plain workflow-model request such as `use Claude` or `use Terra` must never be interpreted as an adversary override.

### Reconciliation Cost and Scope Guardrail

Adversarial reconciliation is a **delta review**, not a second architecture run.

Expected reconciliation activity is normally limited to:

- read the challenged architecture section
- read only affected ADR(s)
- inspect adversarial findings
- make targeted edits if required
- report the disposition of each finding

Do not reload the whole repository, all discovery/PRD context, all skills, or all architecture files merely because an adversarial pass completed.

Broaden context only when a specific finding cannot be resolved from the challenged artifact and its contract.

### Claude adversarial escalation paths

#### User-directed adversary

The user may explicitly select any supported connected model as the adversary for the architecture or a named architecture decision.

When explicitly requested:

- invoke `adversary-flex` with that exact model override
- treat the request as approval for that specific invocation
- skip the default DeepSeek pass unless the user asks for both
- do not require the owning workflow model to justify the user's adversary choice

This is separate from the workflow-model selection.

#### Agent-proposed Sonnet escalation

After a default DeepSeek pass, the owning architecture workflow may propose Sonnet when material uncertainty remains and cross-model diversity is likely to improve the decision.

Before invoking Sonnet on the agent's initiative:

1. explain the unresolved material uncertainty
2. ask for explicit user approval
3. after approval, send the smallest artifact + contract + unresolved findings
4. reconcile Sonnet as evidence, not authority

#### Agent-proposed rare critical Opus escalation

When the user did not request Opus, consider `adversary-opus` after the default DeepSeek adversarial pass only if the decision is both material and unusually critical, such as:

- broad authentication/authorization or cross-account IAM trust
- destructive/irreversible migration or serious data-loss/corruption risk
- distributed consistency/concurrency/idempotency guarantees with high blast radius
- public/external contracts that are extremely expensive to reverse
- recovery/restore decisions with material RTO/RPO consequences
- security-sensitive infrastructure/networking with significant production blast radius
- major irreversible platform lock-in or recurring-cost exposure
- materially conflicting findings that remain unresolved after the owning workflow reconciles the DeepSeek pass

Do not invoke paid Claude models automatically when the user has not requested them.

For an agent-proposed escalation:

1. explain why premium escalation is justified
2. ask for explicit user approval
3. after approval, send artifact + contract + only unresolved material DeepSeek findings
4. reconcile the Opus result as additional evidence, not authority

For a user-directed Sonnet or Opus review, approval/justification is already satisfied by the user's explicit request.

If a proposed paid Claude escalation is not justified or not approved, continue with the bounded DeepSeek + owning-workflow process.

Do not invoke the adversary for ordinary low-risk choices merely to add ceremony.

If a substantive high-risk finding remains unresolved after two cycles, do not declare the architecture ready. Resolve it in architecture, obtain the required user decision, or use the existing Opus escalation policy when appropriate.

## Stage 11 — Architecture Completeness Check

Before finishing, confirm:

- PRD constraints are covered
- the major architecture is decided
- the technology baseline is complete
- implementation agents will not need to choose the stack
- architecture and ADRs agree
- cost assumptions are documented
- security model is defined
- reliability/recovery is defined
- test tooling is defined
- CI/CD approach is defined
- unresolved decisions are clearly identified
- every triggered high-risk decision has either completed adversarial reconciliation or is explicitly blocking readiness

Do not claim architecture is implementation-ready when required technology decisions remain unresolved.

## Architecture Authority Escalation to Opus

This is distinct from adversarial review.

Use the `architect` Opus subagent only if a material architecture decision cannot be responsibly settled by the owning architecture workflow model and:

- is unusually high-risk
- has major irreversible consequences
- has unresolved security or data-integrity implications
- has multiple viable alternatives with no defensible conclusion
- remains unresolved after normal architecture analysis

Do not invoke Opus merely because an architecture contains many components.

Ask for approval before delegating to the Opus architect.

When escalation is not required, the selected owning architecture workflow model remains the architecture authority.

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

## Output Status

If architecture is sufficiently complete for project initialization, finish with exactly:

`ARCHITECTURE_READY`

If a required technology or architecture decision remains unresolved, use the Blocked Output Contract.

Routing rules:

- use owner `PRODUCT` and next command `/prd` when the architecture is blocked by an unclear or conflicting product requirement
- use owner `ARCHITECTURE` and next command `/architect` when the blocker is a technical architecture decision
- use owner `USER_APPROVAL` and next command `/architect` when an approved Opus escalation or another explicit user decision is required

Finish with exactly:

`ARCHITECTURE_BLOCKED`

Do not output anything after the final status token.
