# Project Instructions

## Project Overview

Describe the purpose of this project here.

## Technology

The approved technology stack is determined during `/architect`.

`/project-init` records the approved stack here.

Implementation agents must not invent or silently replace the technology stack.

- Runtime:
- Language:
- Framework:
- Database:
- Cloud:
- Region:
- Infrastructure as Code:
- Package Manager:
- Unit Test Framework:
- Integration Test Framework:
- E2E Test Framework:
- Linting:
- Formatting:
- Type Checking / Static Analysis:
- Dependency Vulnerability Scanning:
- Secret Scanning:
- SAST / Static Security Analysis:
- IaC Security Scanning:
- Container / Image Scanning:
- Security / Dependency Scanning:

If a technology decision required for implementation is missing or materially ambiguous, implementation must stop rather than guess.

## Branch and Worktree Policy

Do not implement application changes directly on protected integration branches.

Protected branches include:

- `main`
- `master`
- `develop`
- `release`
- any repository-defined protected integration branch

Each specification should be implemented on a dedicated branch.

Preferred branch naming:

`spec/<spec-id>-<short-description>`

Example:

`spec/SPEC-001-create-short-url`

Before implementation begins:

- confirm the current branch
- confirm the working tree is clean enough to isolate the requested work
- do not mix unrelated uncommitted changes into the implementation
- create or switch to the dedicated specification branch

For parallel implementation:

- use a separate branch for each specification
- use a separate Git worktree for each concurrently mutating implementation
- do not allow multiple implementation agents to modify the same files concurrently

`/fix`, `/verify`, `/waive`, and `/review` must operate on the existing implementation branch.

They must not create a new branch for the same specification.

Do not automatically:

- merge into a protected branch
- rebase shared branches
- reset unrelated changes
- discard unrelated work
- force-push

Merge should happen through the normal PR/CI process.

## Build and Verification Commands

The commands below must reflect the actual project configuration.

`/project-init` is responsible for populating these when the technology stack is initialized.

Do not invent tools or commands simply because they are common for the language or framework.

### Dependency Restore / Install

Define the dependency restore/install command here.

### Build

Define the project build command here.

### Unit Tests

Define the unit-test command here.

### Integration Tests

Define the integration-test command here.

### E2E Tests

Define the E2E command here when applicable.

### Lint

Define the lint command here.

### Formatting Verification

Define the formatting verification command here when configured.

### Type Checking / Static Analysis

Define the applicable command here.

### Security Verification Commands

Define only architecture-approved executable commands here.

Where applicable include:

- dependency vulnerability scanning
- secret scanning
- SAST/static security analysis
- IaC security scanning
- container/image scanning
- framework-specific security checks
- feature-specific security tests

Do not invent tools during `/verify`.

### Infrastructure Validation

Define applicable IaC validation commands here.

## Architecture Constraints

- Follow approved architecture documents under `docs/architecture/`.
- Follow approved ADRs under `docs/adr/`.
- Do not introduce new infrastructure, persistence technology, frameworks, runtimes, or major abstractions without an approved architecture decision.
- Prefer the simplest production-grade solution that satisfies the requirements.
- Do not silently redesign the system during implementation.
- Do not silently change public contracts.
- Do not silently change consistency, reliability, security, or persistence guarantees.
- Architecture decisions take precedence over implementation convenience.

## Technology Decision Authority

Technology decisions are owned by the architecture stage.

The authority chain is:

1. `/grill` optionally clarifies product intent and coupled decisions before PRD work.
2. `/prd` defines requirements and constraints.
3. `/architect` selects and approves the technology stack.
4. `/project-init` records and operationalizes those decisions.
5. `/spec` decomposes the approved design.
6. `/implement` executes the approved specification.

`/diagnose` localizes difficult defects without redefining intended behavior.

`/adversarial-check` challenges high-risk artifacts but does not replace the authority of `/prd`, `/architect`, `/spec`, `/verify`, or `/review`.

`/smoke` is an auxiliary framework-validation command. It does not become a product lifecycle authority. It may orchestrate FAST/FULL validation against disposable fixtures while preserving the normal lifecycle commands, model routing, evidence rules, and blocked-state ownership.

`/project-init`, `/spec`, `/implement`, `/verify`, `/fix`, and `/review` must not independently replace the approved technology stack.

If a required technology decision is missing, return to architecture rather than guessing.

## Discovery

For large, ambiguous, or high-stakes product work, use `/grill` before `/prd`.

Discovery briefs are stored under:

`docs/discovery/`

A discovery brief should preserve confirmed product decisions, scope/non-goals, constraints, assumptions, and unresolved non-blocking questions without duplicating the full PRD.

The agent should research discoverable facts itself; product decisions and trade-offs remain human decisions.

## Project Initialization

Before implementation begins, `/project-init` must prepare the repository using the approved architecture and ADRs.

It is responsible for synchronizing the approved project configuration into:

- `AGENTS.md`
- `README.md`
- `.kilo/rules/`
- `.kilo/skills/`

It must also ensure the standard workflow artifact directories exist, including:

- `docs/discovery/`
- `docs/prd/`
- `docs/architecture/`
- `docs/adr/`
- `docs/specs/`
- `docs/diagnostics/`
- `docs/verification/`
- `docs/verification/waivers/`
- `docs/verification/smoke/`
- `docs/reviews/`
- `docs/workflow/`

`docs/verification/smoke/` is reserved for restartable `/smoke` run-state records such as `SMOKE-FULL-full-minimal-api-001.md`. Smoke-run records are workflow evidence, not implementation authority, and remain inside the Contract-v1 evidence exclusion set.

`/project-init` must also ensure `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md` exists and is synchronized verbatim with the global canonical Stable-v1 contract. If the canonical source is unavailable or exact synchronization cannot be established, project initialization must fail closed with `PROJECT_INIT_BLOCKED`.

`/project-init` must not implement application functionality.

It must stop with:

`PROJECT_INIT_BLOCKED`

if a required technology decision is missing or conflicting.

## Project Rules

Project-specific rules may be stored under:

`.kilo/rules/`

Rules should contain focused instructions that apply broadly to the repository.

Examples:

- framework conventions
- cloud conventions
- testing conventions
- security conventions
- observability conventions

Do not create rules that merely duplicate this file.

Prefer concise implementation constraints over tutorials.

## Skills

Project skills are stored under:

`.kilo/skills/`

Skills are a curated dependency layer.

Use skills only when they materially improve implementation quality.

Prefer skills in this order:

1. official/vendor-maintained skills
2. reputable and actively maintained community skills
3. adapted project-specific versions of reputable skills
4. custom project-specific skills when necessary

Potential sources include:

- official vendor repositories
- skills.sh
- reputable open-source Agent Skill collections

Third-party skills must be treated as untrusted until reviewed.

Do not silently install third-party skills.

Explicit user approval is required before installing third-party skills.

Before recommending or installing a skill, evaluate:

- source and maintainer reputation
- whether the source is official/vendor maintained
- maintenance activity
- relevance to the approved stack
- bundled scripts or executable resources
- unexpected shell behavior
- unexpected network behavior
- overlap with existing project instructions

Keep the installed skill set small and relevant.

Do not install broad skill collections unnecessarily.

Project-specific skills should be used for guidance that generic technology skills cannot know, such as:

- repository-specific conventions
- domain rules
- project-specific persistence patterns
- logging conventions
- retry/idempotency policies
- organization-specific API behavior
- approved infrastructure patterns

## Test-First and Adversarial Design

Specifications should identify stable observable test seams and explicitly state either:

- `TDD: APPLICABLE`
- `TDD: NOT_APPLICABLE` with a short reason

When TDD applies, implementation should work in thin red → green behavioral slices and avoid tests coupled to private implementation details.

High-risk design/specification decisions should receive fresh-context adversarial challenge when they involve areas such as:

- authentication/authorization or IAM
- concurrency, ordering, idempotency, or distributed consistency
- destructive migrations
- data integrity/recovery
- public API or event-contract compatibility
- financial/irreversible behavior
- security-sensitive infrastructure

Adversarial findings are evidence to reconcile, not authority. The owning lifecycle stage remains responsible for the decision.

Adversarial model routing is cost-controlled:

- default adversary: DeepSeek Flash
- enhanced paid cross-model adversary: Claude Sonnet, only when the user requests it or approves an agent-proposed material second opinion
- premium adversary: Claude Opus, only when the user requests it or approves a rare critical escalation
- a user-directed Sonnet or Opus request authorizes that specific invocation directly; it does not require a prior DeepSeek pass or GPT-5.6 Sol justification
- agent-proposed Sonnet or Opus invocations always require explicit user approval
- Claude output remains evidence; it does not replace the authority of the owning workflow stage

## User-Controlled Model Selection

For product-design workflows, the user may choose the model directly in the command prompt.

Examples:

```text
/grill I want to build a finance platform for Indian retail investors. Grill me. Use GPT.

/grill I want to build a finance platform for Indian retail investors. Grill me. Use Claude.

/architect Design the approved platform. Use Terra.

/spec Create the next implementation specifications. Use Haiku.
```

Recognized aliases:

| User phrase | Model |
| --- | --- |
| `use GPT`, `use OpenAI`, `use Sol` | GPT-5.6 Sol |
| `use Terra` | GPT-5.6 Terra |
| `use Luna` | GPT-5.6 Luna |
| `use Claude`, `use Sonnet` | Claude Sonnet 5 |
| `use Haiku` | Claude Haiku 4.5 |
| `use Opus` | Claude Opus 5 |
| `use DeepSeek` | DeepSeek V4.1 Flash |

The explicit model choice applies to that workflow invocation/session and does not alter the command's role, authority, permissions, acceptance criteria, or safety rules.

For `/architect` and `/spec`, keep **workflow model** and **adversary model** separate:

- plain phrases such as `use Claude`, `use Terra`, or `use GPT` select the workflow model that authors and owns the artifact
- the adversary remains DeepSeek by default
- to override the adversary, use explicit wording such as `for adversarial review use Opus`, `use Sonnet as adversary`, or `adversary: GPT`
- the selected workflow model remains responsible for reconciling adversarial findings

For the dedicated `/adversarial-check` command, a model phrase selects the adversary model because adversarial review is the command's sole purpose.

After an adversarial check, the owning architecture/specification workflow must perform a focused reconciliation pass, not restart the entire authoring workflow.

When reconciliation is delegated to the model-selectable planning worker, use `MODE: RECONCILE_ONLY` and provide only:

- the existing artifact path
- affected ADR/spec paths
- adversarial findings
- the relevant contract/invariants

Do not reload all discovery/PRD/repository context or regenerate unaffected artifacts unless a specific finding genuinely requires additional evidence.

If the requested connected-provider model is unavailable, the workflow must fail clearly and ask the user to select an available model. Never silently substitute.

The default routing below applies only when the user does not specify a model.

## Model Routing

The default model strategy is:

- GPT-5.6 Sol: `/grill`, `/prd`, `/architect`, `/spec`, adversarial reconciliation, and senior code review
- GPT-5.6 Luna: `/project-init`, `/smoke` orchestration, and lightweight Ask/documentation work
- DeepSeek Flash: `/implement`, `/verify`, `/fix`, `/diagnose`, default adversarial review, and pre-review
- Claude Haiku 4.5: optional lower-cost Claude-family choice for bounded work that fits its context window
- Claude Sonnet: optional paid independent model-family second opinion
- Claude Opus: optional premium rare-critical adversarial or architecture escalation
- GPT-5.6 Terra: optional balanced OpenAI choice between Sol and Luna when available in the connected OpenAI catalog

Claude is no longer a mandatory lifecycle dependency.

User-directed requests for Sonnet or Opus are valid model choices for a specific review. Agent-proposed Claude usage requires explicit approval.

## Smoke-Test Cost Policy

Framework smoke tests must avoid metered Claude usage by default.

Use GPT-5.6 Sol/Luna and DeepSeek to validate routing, orchestration, permissions, state transitions, TDD, diagnosis, verification, and review behavior.

Claude Sonnet, Haiku, and Opus remain available for real work and explicit user-selected paid review, but they should not be invoked during smoke testing merely to prove the capability exists.

Prefer static validation or non-Claude routing tests for Claude-capability checks.

## Context Quality

Do not starve a reasoning stage of relevant context to reduce cost.

Optimize for relevant context density:

- include every approved artifact and constraint materially needed for the current decision
- exclude unrelated history, stale artifacts, duplicate content, and unrelated source files
- prefer authoritative handoffs and targeted repository reads
- never omit a material requirement, invariant, ADR, or failure constraint because it increases token usage
- use large context when the decision genuinely requires it

## Specification Discipline

Implementation must be based on a specification under:

`docs/specs/`

Specifications should define, where applicable:

- objective
- scope
- non-goals
- dependencies
- architecture references
- interfaces
- data model
- behavior
- validation
- error handling
- security
- observability
- performance
- cost implications
- acceptance criteria
- testing requirements
- definition of done

Target specification size:

- preferred: 30K–60K tokens
- warning: 60K–80K tokens
- hard ceiling: 100K tokens

Split larger work into independently implementable specifications.

A specification must remain consistent with the approved architecture.

## Implementation Rules

- Implement only the approved specification.
- Reuse existing project conventions.
- Follow the technology stack recorded in this file.
- Follow relevant global/project skills, including TDD when marked applicable.
- Keep changes incremental and reversible.
- Do not invent requirements.
- Do not silently broaden scope.
- Do not weaken tests, assertions, quality thresholds, analyzers, or security gates merely to make implementation pass.
- Do not remove validation or error handling without explicit justification.
- Avoid unnecessary abstractions and dependencies.
- Prefer straightforward code over speculative extensibility.
- Do not introduce a new major dependency without approval.
- Do not change architecture merely to simplify implementation.

## Testing Requirements

Use the appropriate combination of:

- unit tests
- integration tests
- contract tests
- E2E tests
- negative tests
- boundary tests
- security tests

A specification is not complete until all required applicable tests pass.

Do not classify a missing required test as `NOT_APPLICABLE` merely because it has not yet been implemented.

## Verification Workflow

`/verify` provides deterministic evidence about the implementation and applies `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`. The canonical implementation-state manifest is authoritative and includes path, effective Git mode/type, and content/blob identity; the fingerprint is its compact checksum/identifier. The implementation may be uncommitted.

Verification must use the actual project commands defined in this file or repository configuration.

Do not invent verification tools merely because they are common for the technology stack.

The factual verification result is always:

`DONE`

or

`NOT_DONE`

Every non-trivial verification run must persist a new report under:

`docs/verification/`

Do not overwrite prior reports.

For evidence to establish `Delivery Gate: CLEAR`, the report must record:

- current branch
- verification base HEAD SHA
- evidence contract version: `implementation-state-evidence-v1`
- canonical implementation-state manifest
- implementation-state fingerprint
- freshness outcome: `MATCH`, `MISMATCH`, or `UNRECONSTRUCTABLE`

The manifest is canonicalized exactly under Contract v1 from all non-evidence tracked differences plus untracked, non-ignored paths relative to the verification base HEAD, including effective Git mode/type so executable-bit, symlink, and gitlink changes are identity-bearing.

The normative workflow evidence exclusion set is:

- `docs/verification/**`
- `docs/reviews/**`
- `docs/diagnostics/**`

No workflow stage may independently add exclusions.

Normal uncommitted implementation work is allowed. The delivery gate may be `CLEAR` only when pre/post canonical manifests are an exact `MATCH`. `MISMATCH` or `UNRECONSTRUCTABLE` fails closed and requires a fresh `/verify`.

If a verification command changes non-evidence contents, the factual verification result may still be `DONE`, but the delivery gate is `BLOCKED` until `/verify` is rerun against the new state.

`DONE` means:

- all required applicable verification checks passed
- every required acceptance criterion has deterministic passing evidence
- required security verification has no blocking failure or required uncovered gap
- no verification blocker remains

`NOT_DONE` means one or more required conditions are not satisfied.

A historical `NOT_DONE` result must never be manually rewritten to `DONE`.

If the failure should be repaired, use `/fix`.

If root cause is unclear/intermittent/flaky, use `/diagnose`.

If the human owner deliberately accepts the residual risk, use `/waive`. A valid waiver is stored under:

`docs/verification/waivers/`

and may establish:

`Delivery Gate: CLEAR_WITH_EXCEPTION`

The original verification remains `NOT_DONE`, and the failed check continues to run.

## Diagnostic Workflow

Use `/diagnose` for difficult runtime, integration, concurrency, performance, or intermittent failures where the root cause is not obvious.

The diagnostic flow is:

1. define the exact symptom and expected behavior
2. build a tight red-capable feedback loop
3. reproduce and minimize
4. generate falsifiable hypotheses
5. test one variable at a time
6. establish root cause from evidence
7. define a regression-test strategy
8. hand off to `/fix`

Store non-trivial diagnostic reports under:

`docs/diagnostics/`

The normal path is:

`/diagnose → DIAGNOSIS_READY → /fix → /verify`

Do not use diagnosis to redefine product behavior or architecture.

## Repair Workflow

Use `/fix` after any of the following:

- `/diagnose` returns `DIAGNOSIS_READY`
- `/verify` returns `NOT_DONE`
- pre-review returns `CHANGES_REQUIRED`
- senior review returns `REQUEST CHANGES`

The repair flow is:

1. inspect the latest verification or review blockers
2. determine the smallest correct repair
3. repair locally when consistent with the approved specification and architecture
4. use root-cause debugging when the cause is unclear or repeated attempts fail
5. run focused validation
6. return control to `/verify`

`/fix` must not decide completion.

Only `/verify` may return `DONE`.

The successful repair handoff is:

`RUN_VERIFY`

If repair requires an upstream product, architecture, project-init, or specification change, `/fix` must return `FIX_BLOCKED` and identify:

- blocking issue
- owner
- why it blocks
- required action
- exact next command

Do not silently redesign the system.

Avoid repeated speculative repair attempts.

## Verification, Repair, Diagnosis, and Waiver Loop

```text
/implement
   ↓
RUN_VERIFY
   ↓
/verify
   │
   ├── DONE + unchanged verified fingerprint
   │     ↓
   │   Delivery Gate: CLEAR
   │     ↓
   │   /review
   │
   └── NOT_DONE
          ↓
      investigate
       /      \
    /fix    /diagnose
      \       /
       \     /
        /verify
          │
          └── human explicitly accepts bounded residual risk
                    ↓
                  /waive
                    ↓
          Delivery Gate: CLEAR_WITH_EXCEPTION
                    ↓
                 /review
```

A waiver never turns a failed check into a pass.

## Review Workflow

Every non-trivial `/review` run must persist a new history-preserving report under:

`docs/reviews/`

Pre-review findings are persisted even when the pre-review result is `CHANGES_REQUIRED` and senior review is therefore skipped. In that case the report records:

- pre-review: `CHANGES_REQUIRED`
- senior review: `NOT_RUN`
- final AI review decision: `CHANGES_REQUIRED`
- next action: `/fix → /verify → /review`

When senior review runs, the same review-run artifact contains both the complete pre-review and senior-review evidence.

Completed review reports are never overwritten. Each new review run creates a new numbered artifact.

`/fix` should use the latest applicable persisted review, verification, or diagnosis artifact for the requested specification/change and branch rather than the newest artifact globally or chat history. If the implementation revision has advanced since the evidence was created, re-confirm each blocker against current code before editing.

Review occurs when the effective delivery gate is:

- `CLEAR` from a fresh `DONE` verification report, or
- `CLEAR_WITH_EXCEPTION` from a valid human-authorized waiver tied to the exact fresh `NOT_DONE` verification report/canonical manifest/implementation-state fingerprint/failure set.

Before invoking reviewers, `/review` must prove that:

- the requested specification/change matches
- current branch matches
- Contract v1 freshness is `MATCH`: the current canonical implementation-state manifest is byte-for-byte identical to the persisted canonical manifest

A later commit of the same verified contents does not invalidate verification by itself. A matching HEAD does not make evidence fresh if working-tree contents differ.

If the reconstructed fingerprint differs, verification evidence is stale and `/review` must stop and require a new `/verify`.

For `CLEAR_WITH_EXCEPTION`, reviewers must receive both the failed verification evidence and the waiver. They may still reject the change when the accepted risk is unsafe, stale, out of policy, or misclassified.

The review pipeline is:

1. DeepSeek pre-review
2. GPT-5.6 Sol senior review only if pre-review returns `READY_FOR_SENIOR_REVIEW`

Possible pre-review outcomes:

- `READY_FOR_SENIOR_REVIEW`
- `CHANGES_REQUIRED`

Possible senior-review outcomes:

- `APPROVE`
- `REQUEST CHANGES`

If pre-review returns `CHANGES_REQUIRED`:

```text
/review
   ↓
CHANGES_REQUIRED
   ↓
/fix
   ↓
/verify
   ↓
/review
```

If senior review returns `REQUEST CHANGES`:

```text
/review
   ↓
REQUEST CHANGES
   ↓
/fix
   ↓
/verify
   ↓
/review
```

The senior reviewer must not be invoked when the pre-review has blocking findings.

AI review does not replace deterministic CI.

## Definition of Done

A specification is complete only when:

- implementation is complete
- required applicable tests exist
- persisted verification evidence exists and Contract v1 freshness is `MATCH`; fingerprint equality alone is insufficient
- delivery gate is `CLEAR`, or an explicitly accepted `CLEAR_WITH_EXCEPTION` is permitted by project policy
- `/review` reaches `APPROVE`
- CI passes
- merge occurs through the normal PR process

A waiver is an explicit residual-risk acceptance, not a statement that verification passed.

Production deployment remains a separate human-approved action.

## Security

Use OWASP Top 10:2025 as the baseline application-security risk taxonomy. For web/API systems, use OWASP ASVS-style controls as a deeper technical verification reference where appropriate.

Where applicable, verification should cover:

- dependency/software supply-chain vulnerabilities
- secret exposure
- SAST/static security analysis
- IaC/container security
- authentication and authorization
- input validation and injection
- XSS, CSRF, SSRF
- unsafe deserialization/parser behavior
- path/file handling
- cryptography/key management
- sensitive-data storage/transport/logging
- abuse/resource exhaustion
- security logging/alerting
- exceptional-condition handling
- cloud/IAM trust and least privilege
- security-sensitive data integrity/concurrency/replay

Do not claim broad "OWASP compliant", "secure", or regulatory compliance solely from automated checks.

Use the global `security-verification` skill when security verification is applicable.

### Verification Waiver Policy

Waivers must:

- be explicitly human-authorized
- reference the exact failed verification report, its authoritative canonical manifest, and implementation-state fingerprint
- identify exact failed checks
- state classification, justification, residual risk, compensating controls, remediation, and expiry
- remain separate from verification evidence
- expire and never silently carry forward to a new verification run
- keep the waived checks executing

Project policy may mark categories such as security, data-integrity, or compliance failures non-waivable.

Never:

- hard-code credentials or secrets
- print secrets in logs or command output
- weaken authentication or authorization to obtain a pass
- disable required security checks
- commit local credential material

Treat these as sensitive by default:

- `.env`
- `.env.*`
- `*.pem`
- `*.key`
- cloud credentials
- API tokens
- private certificates

## Cloud and Cost

Cloud cost is a first-class implementation concern.

Where applicable, consider:

- fixed monthly cost
- variable usage cost
- storage cost
- data-transfer cost
- observability cost
- scaling behavior
- operational burden
- failure and recovery cost

Prefer managed or serverless services when they provide the best balance of reliability, simplicity, and cost.

Do not introduce always-on or premium infrastructure unless justified by approved requirements.

## Deployment

Infrastructure and deployment must follow approved architecture and IaC decisions.

Do not manually create production cloud resources when IaC is required.

CI/CD must enforce applicable build, test, quality, security, and IaC gates.

Do not auto-deploy to production.

Production deployment requires explicit human approval.

## Workflow Ownership

The normal lifecycle is:

```text
/grill (optional)
  ↓
DISCOVERY_READY
  ↓
/prd
  ↓
PRD_READY
  ↓
/architect
  ├─ ARCHITECTURE_BLOCKED → resolve → /architect
  └─ ARCHITECTURE_READY
            ↓
      /project-init
  ├─ PROJECT_INIT_BLOCKED → resolve as directed
  └─ PROJECT_INIT_READY
            ↓
          /spec
  ├─ SPEC_BLOCKED → resolve as directed
  └─ SPEC_READY
            ↓
       /implement
  ├─ IMPLEMENTATION_BLOCKED → resolve as directed
  └─ RUN_VERIFY
            ↓
         /verify
  ├─ DONE + unchanged verified fingerprint → CLEAR ──────────────┐
  │                                                              │
  └─ NOT_DONE                                                    │
       ├─ understood defect → /fix → /verify                     │
       ├─ unclear/intermittent → /diagnose → /fix → /verify      │
       └─ explicit bounded human risk acceptance → /waive        │
                                                   ↓              │
                                        CLEAR_WITH_EXCEPTION      │
                                                   └──────┬───────┘
                                                          ↓
                                                       /review
                                                          ↓
                                                DeepSeek pre-review
  ├─ CHANGES_REQUIRED → persisted REVIEW → /fix → /verify → /review
  └─ READY_FOR_SENIOR_REVIEW
                   ↓
            GPT-5.6 Sol senior review
  ├─ REQUEST CHANGES → persisted REVIEW → /fix → /verify → /review
  └─ APPROVE → persisted REVIEW
                   ↓
                  CI
                   ↓
              PR / merge
                   ↓
       human-approved production deployment
```

Auxiliary paths:

```text
hard bug → /diagnose → /fix → /verify
high-risk decision → /adversarial-check → owning stage continues or resolves findings
stale verification evidence → /verify
```

Blocked stages must state the owner, required action, and exact next command rather than leaving the operator to infer the recovery path.
