# Project Name

Briefly describe the project.

## Purpose

This repository is a reusable production-grade AI-assisted software-engineering template.

The project-specific technology stack is selected during `/architect` and synchronized into the repository during `/project-init`. Project initialization also synchronizes the Stable-v1 evidence contract into `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`.

## Development Workflow

The standard lifecycle is:

1. `/grill` when discovery is needed (optional)
2. `/prd`
3. `/architect`
4. `/project-init`
5. `/spec`
6. `/implement`
7. `/verify`
8. `/review`

`/waive` is an exception path used only when `/verify` is `NOT_DONE` and the human owner explicitly accepts a bounded residual risk.

For difficult defects use `/diagnose → /fix → /verify`.

For high-risk decisions use `/adversarial-check` or the automatic risk-triggered checks inside architecture/specification work.

For framework validation use the global `/smoke` command. `/smoke` is not part of the normal product lifecycle; it orchestrates disposable FAST/FULL validation runs while preserving the underlying workflow authorities.

The complete flow is:

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
  ├─ ARCHITECTURE_BLOCKED → resolve as directed → /architect
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
  ├─ NOT_DONE → /fix or /diagnose → /verify
  ├─ NOT_DONE + explicit human risk acceptance → /waive
  │                                              ↓
  │                                   CLEAR_WITH_EXCEPTION
  └─ DONE + unchanged verified fingerprint → CLEAR
       ↓
     /review
       ↓
DeepSeek pre-review
  ├─ CHANGES_REQUIRED → /fix → /verify → /review
  └─ READY_FOR_SENIOR_REVIEW
                   ↓
            GPT-5.6 Sol senior review
  ├─ REQUEST CHANGES → /fix → /verify → /review
  └─ APPROVE
       ↓
       CI
       ↓
   PR / merge
       ↓
human-approved production deployment
```

Blocked workflow stages must report the blocker, its owner, the minimum required action, and the exact next command.

For the complete command, agent, model-routing, TDD, diagnosis, adversarial-escalation, skill, blocked-state, and **sample invocation prompt** reference, see:

`docs/workflow/AI-ENGINEERING-WORKFLOW.md`

## Technology Ownership

The major technology baseline is chosen during:

`/architect`

That includes, where applicable:

- application language/runtime
- framework
- persistence technology
- cloud/provider/region
- infrastructure as code
- testing stack
- code-quality tooling
- CI/CD approach

`/project-init` does not independently choose the stack.

It synchronizes the approved architecture into:

- `AGENTS.md`
- `README.md`
- `.kilo/rules/`
- `.kilo/skills/`

It also ensures the standard workflow artifact directories exist, including `docs/verification/`, `docs/verification/waivers/`, `docs/verification/smoke/`, `docs/reviews/`, `docs/diagnostics/`, and `docs/workflow/`, with the Stable-v1 evidence contract synchronized into `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`.

If required technology decisions are missing, `/project-init` must stop instead of guessing.

## Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── .gitignore
├── .kilo/
│   ├── rules/
│   └── skills/
└── docs/
    ├── discovery/
    ├── diagnostics/
    ├── prd/
    ├── architecture/
    ├── adr/
    ├── specs/
    ├── reviews/
    └── verification/
        ├── smoke/
        └── waivers/
```

Project-local concurrent worktrees may use `.kilo/worktrees/`, which is intentionally ignored by Git.

## Branch and Worktree Workflow

Each specification should be implemented on its own branch.

Preferred naming:

`spec/<spec-id>-<short-description>`

Example:

`spec/SPEC-001-create-short-url`

Do not implement directly on protected integration branches such as:

- `main`
- `master`
- `develop`
- `release`

For parallel implementation:

- use separate branches
- use separate Git worktrees
- avoid concurrent mutation of the same files

`/fix`, `/verify`, `/waive`, and `/review` continue on the existing implementation branch.

They do not create another branch for the same specification.

Merge should happen through the normal PR/CI process.

## Discovery, TDD, Diagnosis, and Adversarial Checks

Use `/grill` before PRD work when an idea is large, ambiguous, or contains coupled decisions. Confirmed discovery is written under `docs/discovery/` and becomes input to `/prd`.

Specifications define stable observable test seams and whether TDD is applicable. When applicable, `/implement` uses behavioral red → green vertical slices rather than writing tests only after implementation.

Use `/diagnose` when a defect is difficult to reproduce or localize. It creates a red-capable feedback loop before root-cause claims and may persist a concise report under `docs/diagnostics/`.

Use `/adversarial-check` for high-risk architecture/specification/migration/security decisions. DeepSeek Flash is the default adversary. You may explicitly request Claude Sonnet for a paid cross-model second opinion or Claude Opus for a premium critical review; a user-directed request authorizes that specific invocation without a prior DeepSeek pass or GPT-5.6 Sol justification. It is not a substitute for `/verify`, `/review`, CI, or human approval.

## Project Skills

Project-scoped skills are stored under:

`.kilo/skills/`

Skills should only be added when they materially improve implementation quality.

Preference order:

1. official/vendor-maintained skills
2. reputable community skills
3. adapted project-specific skills
4. custom skills only when necessary

Third-party skills must be reviewed and explicitly approved before installation.

Do not install large or unrelated skill collections.

## Verification Evidence, Security, Repair, and Waivers

Every non-trivial `/verify` run creates a new history-preserving report under:

`docs/verification/`

Restartable `/smoke` orchestration state is stored separately under:

`docs/verification/smoke/<run-id>.md`

The smoke record tracks profile, fixture, release/config SHA, current stage/scenario, progress, model/cost ledger, blockers, and next action so `/smoke STATUS` and `/smoke RESUME` do not depend on chat history.

Typical global command usage:

```text
/smoke FAST DEFAULT
/smoke FULL DEFAULT
/smoke STATUS <run-id>
/smoke RESUME <run-id>
```

Reusable verification evidence follows `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`. The canonical implementation-state manifest is the authoritative identity of all non-evidence tracked differences plus untracked, non-ignored paths relative to the verification base HEAD, including effective Git mode/type; the fingerprint is only a compact checksum/identifier.

This intentionally supports review-before-commit. Uncommitted implementation work may establish `Delivery Gate: CLEAR` only when the pre/post canonical manifests are an exact `MATCH`. `MISMATCH` or `UNRECONSTRUCTABLE` fails closed.

If a verification command changes non-evidence contents, checks may still report factual `DONE`, but the delivery gate remains `BLOCKED` until `/verify` is rerun against the new state.

Verification remains factual:

- `DONE` means all required applicable checks and acceptance criteria passed
- `NOT_DONE` means one or more required conditions failed
- historical `NOT_DONE` reports are never rewritten to `DONE`

Security verification uses project-approved executable checks and the global `security-verification` skill. OWASP Top 10:2025 is the baseline application-security risk taxonomy; OWASP ASVS-style controls are used as a deeper web/API verification reference where appropriate.

If a failed verification should be repaired, use `/fix`. If root cause is unclear, intermittent, or flaky, use `/diagnose`.

When the human owner deliberately accepts a bounded residual risk, use `/waive`. The waiver is persisted separately under:

`docs/verification/waivers/`

A valid waiver may establish `Delivery Gate: CLEAR_WITH_EXCEPTION` so review can proceed with both the failed evidence and accepted risk visible. The failed verification remains `NOT_DONE`, and the failed check continues to execute.

`/review` validates evidence freshness under Contract v1 before invoking reviewers. It reconstructs the current canonical manifest from the verification report's base HEAD and requires byte-for-byte manifest equality. A later commit of identical verified contents is allowed. `MISMATCH`, `UNRECONSTRUCTABLE`, malformed evidence, or unavailable reconstruction inputs require a fresh `/verify`.

Normal repair flow:

For a hard defect whose cause is not established:

```text
/diagnose
   ↓
DIAGNOSIS_READY
   ↓
/fix
   ↓
/verify
```

For implementation verification:

```text
/implement
   ↓
RUN_VERIFY
   ↓
/verify
   │
   ├── DONE + unchanged verified fingerprint → CLEAR → /review
   │
   └── NOT_DONE
          ├── understood defect → /fix → /verify
          ├── unclear/intermittent → /diagnose → /fix → /verify
          └── explicit bounded human risk acceptance
                    ↓
                  /waive
                    ↓
          CLEAR_WITH_EXCEPTION
                    ↓
                 /review
```

`/fix` is also used when review finds blocking issues:

```text
CHANGES_REQUIRED or REQUEST CHANGES
                ↓
              /fix
                ↓
             /verify
                ↓
             /review
```

`/verify` is the authoritative factual verification gate.

It must validate all required applicable checks, persist evidence, evaluate configured security gates, and provide deterministic evidence for the specification's acceptance criteria.

Review may proceed only when the effective delivery gate is `CLEAR` or `CLEAR_WITH_EXCEPTION`.

## Choosing the Model Per Workflow

For product-design commands, you can choose the model directly in the prompt.

Examples:

```text
/grill I want to build a finance platform for Indian retail investors. Grill me. Use GPT.

/grill I want to build a finance platform for Indian retail investors. Grill me. Use Claude.

/architect Use Terra.

/spec Use Haiku.

/adversarial-check Use Opus directly for this review.
```

Supported aliases include GPT/Sol, Terra, Luna, Claude/Sonnet, Haiku, Opus, and DeepSeek.

For `/architect` and `/spec`, a plain model choice selects the workflow authoring model only. The adversary stays DeepSeek unless you separately say something like `for adversarial review use Opus` or `adversary: Sonnet`.

For `/adversarial-check`, the model phrase selects the adversary directly.

After adversarial review, architecture/specification reconciliation is a focused delta pass. It should update only affected sections and must not rerun the whole authoring workflow.

If no model is named, the default routing below applies.

The model choice changes the intelligence provider, not the workflow's permissions or authority.

Kilo's Task Subagent Model Selection feature must remain enabled for natural-language routing to a different subagent model.

## Model Routing

The default workflow uses:

- GPT-5.6 Sol for discovery, PRD, architecture, specification design, adversarial reconciliation, and senior review
- GPT-5.6 Luna for project initialization and lightweight repository/documentation work
- DeepSeek Flash for implementation, verification, repair, diagnosis, default adversarial checks, and pre-review
- Claude Sonnet as an optional paid independent second opinion
- Claude Opus as an optional premium rare-critical escalation

GPT-5.6 Sol/Luna use the connected ChatGPT subscription in Kilo; Claude Sonnet/Opus consume the separate Anthropic API budget.

Do not reduce relevant context merely to save tokens. Remove irrelevant context, not required context.

For framework smoke testing, do not use metered Claude models unless explicitly requested. Use GPT-5.6 Sol/Luna plus DeepSeek to validate behavior while preserving Claude capability for real work.

## Review Evidence

Every non-trivial `/review` run creates a new history-preserving report under:

`docs/reviews/`

A review report contains the verification input, active waiver when applicable, complete pre-review findings, senior-review findings when invoked, final AI review decision, and next action.

If pre-review returns `CHANGES_REQUIRED`, the report is still written and records `Senior Review: NOT_RUN`.

Subsequent review runs create new numbered artifacts instead of overwriting previous reports. These reports are the durable handoff into `/fix`.

`/fix` selects the latest **applicable** review/verification/diagnosis evidence for the requested specification/change and branch, not merely the newest artifact in the repository.

## Review Model

The review pipeline is cost-controlled and consumes the latest **applicable, Contract-v1-fresh** persisted verification report for the requested specification/change and branch. If the delivery gate is `CLEAR_WITH_EXCEPTION`, it also receives the exact active waiver bound to that verification report/canonical manifest/fingerprint/failure set. Reviewers may still reject an unsafe, stale, misclassified, or out-of-policy waiver.

The review pipeline is:

1. DeepSeek performs the first-pass pre-review.
2. GPT-5.6 Sol runs only when pre-review returns `READY_FOR_SENIOR_REVIEW`.
3. CI remains the deterministic merge gate.
4. Production deployment still requires human approval.

The AI review results are:

- pre-review: `READY_FOR_SENIOR_REVIEW` or `CHANGES_REQUIRED`
- senior review: `APPROVE` or `REQUEST CHANGES`

## CI and Merge

The approved architecture defines the CI/CD approach.

A greenfield project should include an explicit specification for repository/bootstrap work when CI/CD, IaC bootstrap, or project scaffolding does not yet exist.

CI should enforce the applicable:

- build
- unit/integration/E2E tests
- lint/format/static analysis
- security/dependency checks
- IaC validation

Do not bypass CI to merge implementation changes.

## Production Deployment

Production deployment is never implied by an AI `APPROVE` result.

The required order is:

```text
AI review APPROVE
      ↓
CI passes
      ↓
PR / merge
      ↓
explicit human production approval
      ↓
production deployment
```

## Getting Started

For a new project:

1. clone or copy this template
2. replace the project name and description
3. run `/grill` if the product idea is still broad/ambiguous; otherwise start at `/prd`
4. proceed through the workflow in order
5. let `/project-init` populate the actual technology and build/test commands after architecture is approved

Do not manually fill technology choices that have not yet been approved by the architecture stage.
