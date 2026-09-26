# Global AI Engineering Policy

## Objective

Produce production-grade software with minimum unnecessary complexity, strong engineering discipline, and minimum practical infrastructure cost.

## Universal Workflow

For normal feature work, use this lifecycle:

`/grill (optional) → /prd → /architect → /project-init → /spec → /implement → /verify → CLEAR or CLEAR_WITH_EXCEPTION → /review`

Use `/grill` before `/prd` when the idea is ambiguous, unusually large, high-stakes, or contains many coupled product decisions. Skip it for clear, bounded work.

Repair and incident loops:

- `/verify → NOT_DONE → /fix → /verify`
- `/verify → NOT_DONE → /diagnose → /fix → /verify` for uncertain/intermittent failures
- `/verify → NOT_DONE → /waive → /review` only when the human owner explicitly accepts a bounded residual risk
- `/review → CHANGES_REQUIRED or REQUEST CHANGES → /fix → /verify → /review`
- `/diagnose (optional) → /fix → /verify` for difficult runtime, integration, concurrency, performance, or intermittent defects

`/adversarial-check` is an auxiliary risk-control command for high-risk artifacts; it does not replace `/verify` or `/review`.

`/smoke` is a release-validation utility for executing or resuming `FAST` or `FULL` smoke profiles against approved disposable fixtures. It does not become a product lifecycle authority and must preserve the normal command ownership, evidence, model-routing, and blocked-state contracts.

Production deployment always requires human approval.

## Core Principles

1. Prefer the simplest architecture that satisfies approved requirements.
2. Do not invent product requirements.
3. Do not silently change approved architecture, ADRs, or acceptance criteria during implementation.
4. Prefer incremental, reversible changes.
5. Reuse existing project conventions before introducing new abstractions.
6. Never claim completion without deterministic evidence.
7. Never expose, print, modify, or commit secrets.
8. Treat project-level `AGENTS.md`, approved architecture, ADRs, and specifications as authoritative project context.

## Technology Decision Authority

- `/grill` clarifies product intent and trade-offs; it does not choose implementation architecture.
- `/prd` defines product requirements and constraints.
- `/architect` chooses the major technology baseline.
- `/project-init` records and operationalizes that baseline in the repository.
- `/spec` decomposes approved work.
- `/implement` executes the approved specification.
- `/verify` owns factual deterministic `DONE` / `NOT_DONE` and persists verification evidence.
- `/waive` records explicit human risk acceptance without altering verification truth.
- `/review` owns AI review after a `CLEAR` or valid `CLEAR_WITH_EXCEPTION` delivery gate.
- `/diagnose` localizes difficult defects without redefining intended behavior.
- `/fix` repairs diagnosed, verification, or review blockers without redesigning the system.
- `/adversarial-check` challenges assumptions and failure modes but does not become the decision authority.

Implementation agents must not choose a missing major technology decision on their own.

## Discovery, TDD, Diagnosis, and Adversarial Discipline

- Use `requirements-grilling` when unresolved product decisions would otherwise be guessed. The agent researches facts; the user decides scope, priorities, and trade-offs.
- Use `tdd` for behavior-bearing application code when a stable observable seam exists. Work in thin red → green slices rather than writing tests after a large implementation.
- Use `diagnosing-bugs` for non-trivial failures. Build a tight red-capable feedback loop for the exact symptom before asserting root cause.
- Use `adversarial-check` selectively for high-risk or hard-to-reverse decisions such as auth/IAM, destructive migrations, concurrency/idempotency, public contracts, data integrity, recovery, and security-sensitive infrastructure.
- Fresh adversarial review receives the smallest artifact plus its contract, not the author's preferred conclusion. Findings are evidence to reconcile, not authority.
- Two materially unchanged adversarial cycles with substantive unresolved findings require human or architecture escalation.

## Specification Discipline

Specifications should be independently implementable and verifiable.

Target context size:

- Preferred: 30K–60K tokens
- Warning: 60K–80K tokens
- Hard ceiling: 100K tokens

Split specifications that exceed the hard ceiling or create unsafe coupling.

## Branch and Worktree Discipline

Do not implement directly on protected integration branches such as `main`, `master`, `develop`, or `release`.

Use a dedicated specification branch, preferably:

`spec/<spec-id>-<short-description>`

For concurrent mutating work, use separate branches and Git worktrees.

Do not automatically:

- stash unrelated work
- reset or discard unrelated changes
- rebase shared branches
- force-push
- auto-merge protected branches

## Implementation

The implementation agent must:

- follow the approved specification
- follow architecture and ADRs
- use the approved technology stack
- write production-grade code
- load and apply relevant approved skills
- use test-first vertical slices when the specification marks TDD applicable
- implement applicable tests
- preserve security, reliability, and public contracts
- report failures honestly

If requirements conflict or a required architecture decision is missing, stop and report the blocker.

## Testing and Verification

Use applicable:

- unit tests
- integration tests
- contract tests
- E2E tests
- negative and boundary tests
- security tests
- formatting/lint/static-analysis checks
- dependency/security scans
- IaC validation

Never make verification green by weakening the verification mechanism.

Never:

- delete, skip, or quarantine a failing required test merely to obtain green status
- weaken assertions to make implementation pass
- mock away the behavior being tested
- lower required quality, coverage, performance, or security thresholds without approval
- add warning/lint/static-analysis suppressions solely to silence a failure
- disable a required quality/security check simply to obtain a pass

`/verify` is the authoritative factual verification gate.

Every non-trivial verification run must create a new history-preserving artifact under `docs/verification/`.

Reusable verification/review evidence must follow installed global `contracts/implementation-state-evidence-v1.md`. The canonical implementation-state manifest is the authoritative repository-state identity and includes path, effective Git mode/type, and content/blob identity; the fingerprint is only its compact checksum/identifier. Normal uncommitted implementation work may reach `CLEAR` only when pre/post verification canonical manifests are an exact `MATCH`. `MISMATCH` or `UNRECONSTRUCTABLE` fails closed and requires a fresh `/verify`.

A specification is `DONE` only when all required applicable deterministic checks and acceptance criteria have verifiable evidence.

A failed verification remains `NOT_DONE`. Never manually rewrite it to `DONE`.

When the human owner deliberately accepts a documented residual risk, use `/waive` to create a separate artifact under `docs/verification/waivers/`.

A valid waiver may establish `Delivery Gate: CLEAR_WITH_EXCEPTION` for review, but it never changes the original verification result or makes the failed check pass.

Waivers must be scoped, human-authorized, time-bounded, and tied to the exact verification report, its canonical implementation-state manifest/fingerprint, and failure set. Waived checks continue to execute.

## Review

Review occurs only when the delivery gate is `CLEAR` or `CLEAR_WITH_EXCEPTION` **and** Contract v1 freshness is `MATCH` for the current specification/change and branch. A later commit of those same contents does not by itself invalidate verification. Fingerprint equality alone is insufficient; exact canonical-manifest equality is authoritative.

Every non-trivial `/review` run must create a new history-preserving artifact under `docs/reviews/`.

Pre-review findings must be persisted even when they block senior review. A blocked pre-review report records `CHANGES_REQUIRED` and `Senior Review: NOT_RUN`.

When senior review runs, the same review-run artifact records both the complete pre-review evidence and the senior-review evidence.

Completed prior review reports must not be overwritten. Subsequent review runs create new numbered artifacts.

`/fix` should consume the latest applicable persisted review/verification/diagnosis evidence for the requested specification/change and branch rather than the newest artifact globally or chat history.

For `CLEAR_WITH_EXCEPTION`, reviewers must receive the original failed verification evidence plus the active waiver and may still reject the change if the accepted risk is unsafe or out of policy.

Review sequence:

1. DeepSeek pre-review
2. GPT-5.6 Sol senior review only if pre-review returns `READY_FOR_SENIOR_REVIEW`
3. CI
4. PR/merge
5. human-approved production deployment

Do not invoke the senior reviewer when pre-review has blocking findings.

## Security

Use OWASP Top 10:2025 as the baseline application-security risk taxonomy and OWASP ASVS-style controls as a deeper web/API verification reference where appropriate.

Security verification should cover applicable dependency/supply-chain, secret, SAST, IaC, container/image, authentication, authorization, data protection, injection, SSRF/XSS/CSRF, unsafe file/path handling, cryptography, logging/alerting, exceptional-condition handling, cloud/IAM, and project-specific security risks.

Do not claim broad "OWASP compliant", "secure", or regulatory compliance from automated checks alone.

If a required security risk is applicable but lacks approved executable evidence, report it as uncovered rather than passing it.

Never:

- hard-code credentials
- expose secrets in logs
- bypass authentication or authorization
- disable security checks merely to make CI pass

Treat these as sensitive by default:

- `.env`
- `.env.*`
- `*.pem`
- `*.key`
- credential files
- cloud credentials
- API tokens

## Cloud and Cost

Cloud cost is a first-class requirement.

For AWS or Azure decisions consider:

- fixed monthly cost
- variable cost
- storage cost
- network/data-transfer cost
- observability cost
- scaling behavior
- operational burden
- failure modes
- recovery strategy

Challenge unnecessary always-on or premium infrastructure.

Prefer managed/serverless services when they provide the best balance of reliability, simplicity, and cost.

## User-Controlled Model Selection

For product-design workflows, the user may choose the model directly in the command prompt.

Examples:

```text
/grill I want to build a finance platform for Indian retail investors. Grill me. Use GPT.

/grill I want to build a finance platform for Indian retail investors. Grill me. Use Claude.

/architect Design the approved system. Use Terra.

/spec Create the next implementation specifications. Use Haiku.
```

Supported aliases:

| User phrase | Model |
| --- | --- |
| `use GPT`, `use OpenAI`, `use Sol` | GPT-5.6 Sol |
| `use Terra` | GPT-5.6 Terra |
| `use Luna` | GPT-5.6 Luna |
| `use Claude`, `use Sonnet` | Claude Sonnet 5 |
| `use Haiku` | Claude Haiku 4.5 |
| `use Opus` | Claude Opus 5 |
| `use DeepSeek` | DeepSeek V4.1 Flash |

An explicit model request is authoritative for that workflow invocation/session and does not require the default model to justify the choice.

If the requested connected-provider model is unavailable, fail clearly and ask the user to choose an available model. Never silently fall back.

Model choice never changes stage authority or safety constraints.

Kilo's experimental Task Subagent Model Selection is enabled so a workflow can honor explicit user model requests when delegation is required.

## Model Routing and Escalation

### Primary reasoning default — GPT-5.6 Sol

Use GPT-5.6 Sol by default for:

- `/grill`
- `/prd`
- `/architect`
- `/spec`
- senior code review
- reconciliation of adversarial findings

This is a default, not a restriction. An explicit user model choice overrides it for model-selectable workflows.

### Additional OpenAI subscription choices — GPT-5.6 Terra and Luna

GPT-5.6 Terra is an approved balanced reasoning/coding option between Sol and Luna. It is suitable when the user wants strong professional reasoning with less latency/compute than Sol.

### Lightweight orchestration — GPT-5.6 Luna

Use GPT-5.6 Luna for:

- `/project-init`
- lightweight Ask-mode repository/documentation work

Luna must operationalize approved decisions, not make missing architecture decisions.

### Execution workhorse — DeepSeek Flash

Use DeepSeek Flash for:

- `/implement`
- `/verify`
- `/fix`
- `/diagnose`
- default adversarial checks
- pre-review

### Efficient Claude option — Claude Haiku 4.5

Haiku is an approved lower-cost Claude-family choice for bounded planning/review work that fits its context window.

Do not use Haiku when the required context exceeds its supported window or when the user explicitly wants Sonnet/Opus.

### Paid cross-model review — Claude Sonnet

Claude Sonnet is no longer a mandatory lifecycle model.

Use Sonnet as an independent model-family second opinion when:

- the user explicitly requests it, or
- the owning workflow model proposes a material cross-model review and the user approves the paid invocation.

Typical uses include architecture/spec adversarial review, security/consistency review, or another material decision where model diversity adds value.

### Premium escalation — Claude Opus

Reserve Opus for:

- user-directed premium adversarial review
- rare critical agent-proposed adversarial escalation with explicit approval
- rare architecture-authority escalation when the owning architecture workflow cannot settle a high-impact decision

Default adversary: DeepSeek Flash.
Enhanced paid adversary: Claude Sonnet.
Premium adversary: Claude Opus.

A user-directed request for Sonnet or Opus authorizes that specific invocation directly. Do not require a prior DeepSeek pass or Sol justification, and do not add another adversarial model unless the user asks.

Agent-proposed Sonnet or Opus calls always require explicit user approval.

## Smoke-Test Orchestration

Use `/smoke FAST [fixture]`, `/smoke FULL [fixture]`, `/smoke RESUME <run-id>`, or `/smoke STATUS <run-id>` for controlled framework validation.

Approved fixture metadata is stored in installed global `smoke/fixtures.json`. Fixture selection constrains the disposable test shape; it never overrides `/architect` technology authority or permits skipping genuinely applicable project checks.

`/smoke` must persist restartable run state in the disposable project's `docs/verification/smoke/` area so a run can resume without relying on chat history.

The orchestrator must reuse valid artifacts, resume from the earliest incomplete or invalidated stage, and preserve each underlying command's normal model routing. Negative freshness checks must stop before reviewer invocation.

## Smoke-Test Cost Policy

Smoke testing must default to models that do not consume the metered Anthropic API budget.

For framework/configuration smoke tests:

- use GPT-5.6 Sol/Luna through the connected ChatGPT subscription when appropriate
- use DeepSeek Flash for implementation, verification, debugging, default adversarial checks, and other high-volume execution
- do **not** use Claude Sonnet, Claude Haiku, or Claude Opus merely to prove routing or workflow behavior
- retain Claude routing capability for real work, but invoke Claude during smoke testing only when the user explicitly requests a paid Claude test
- prefer negative/static validation of Claude routing where possible
- never spend paid frontier-model budget to validate behavior that can be proven with GPT/DeepSeek or static inspection

The default smoke-test objective is to validate orchestration, permissions, state transitions, and model-selection mechanics at minimum practical API cost.

## Context Quality and Cost

Do not reduce relevant context merely to save tokens.

Quality takes priority over artificial token minimization.

For reasoning stages:

- load all approved context materially required to make the decision
- preserve PRD, architecture, ADR, discovery, specification, and repository evidence when relevant
- exclude unrelated history, obsolete artifacts, duplicate text, and unrelated source files
- use authoritative handoffs and targeted retrieval instead of repeatedly re-sending irrelevant repository content
- never omit a material constraint because of cost
- if a decision genuinely needs a large context, use the large context rather than guessing

The optimization target is **relevant context density**, not minimum token count.
