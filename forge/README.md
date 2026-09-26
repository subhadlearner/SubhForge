# Kilo Configuration

Opinionated global configuration for an AI-assisted software-engineering workflow built around [Kilo Code](https://kilo.ai/).

This repository contains the reusable **global workflow layer** used across projects: engineering policy, lifecycle commands, specialized agents, model-routing rules, permissions, reusable skills, and the Stable-v0.1 implementation-state evidence contract.

The companion project-side template is:

- [subhadlearner/production-ai-project](https://github.com/subhadlearner/production-ai-project)

## What this repository does

The configuration establishes a production-oriented workflow for moving from an idea to reviewed implementation while keeping stage ownership explicit:

```text
/grill (optional)
  ↓
/prd
  ↓
/architect
  ↓
/project-init
  ↓
/spec
  ↓
/implement
  ↓
/verify
  ↓
CLEAR or CLEAR_WITH_EXCEPTION
  ↓
/review
```

It also defines repair and investigation loops for failed verification, diagnosis, fixes, human-authorized waivers, and adversarial review.

The main design goals are:

- production-grade engineering discipline
- explicit PRD → architecture → specification → implementation ownership
- deterministic verification before AI code review
- review-before-commit support
- persistent verification and review evidence
- bounded human risk acceptance without rewriting failed verification
- security verification based on OWASP-oriented risk coverage
- cost-aware architecture and infrastructure choices
- low-cost model routing for high-volume implementation work
- optional higher-cost model escalation only when justified or explicitly requested

## Repository layout

The deployable Kilo configuration lives under `kilo/`.

```text
kilo/
├── AGENTS.md
├── kilo.jsonc
├── agents/
├── commands/
├── contracts/
├── smoke/
└── skills/
```

### `AGENTS.md`

Defines the global AI engineering policy, including:

- lifecycle and stage authority
- branch/worktree discipline
- TDD and diagnosis expectations
- verification and review rules
- security requirements
- cloud and operating-cost considerations
- model routing and escalation
- smoke-test cost policy
- context-quality rules

### `commands/`

Global slash-command workflows such as:

- `/grill`
- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`
- `/verify`
- `/waive`
- `/review`
- `/fix`
- `/diagnose`
- `/adversarial-check`
- `/smoke`

### `agents/`

Specialized agents used by the workflows, including:

- planning worker
- implementation/builder
- debugger
- DeepSeek pre-reviewer
- GPT-5.6 Sol senior code reviewer
- default and optional adversarial reviewers

Planning workflows support the explicit execution modes:

- `AUTHOR`
- `CONTINUE`
- `RECONCILE_ONLY`

The reconciliation mode prevents an adversarial review from unnecessarily rerunning an entire planning workflow.

### `contracts/`

Contains the normative implementation-state evidence contract used by `/verify`, `/review`, and `/waive`.

Stable v0.1 uses:

`contracts/implementation-state-evidence-v1.md`

The contract supports verification and review **before the implementation is committed**. It binds reusable evidence to a canonical repository-state manifest containing:

- repository-relative path
- effective Git mode/type
- content/blob identity

Freshness outcomes are fail-closed:

- `MATCH`
- `MISMATCH`
- `UNRECONSTRUCTABLE`

A later commit of the exact same verified repository state does not invalidate otherwise-fresh evidence.

### `skills/`

Curated reusable engineering skills covering areas such as:

- .NET
- Python
- PostgreSQL
- SQLite
- React / Next.js / frontend engineering
- AWS serverless
- AWS IAM
- DynamoDB
- Azure architecture
- TDD
- diagnosis
- adversarial review
- security verification
- requirements grilling

Skills provide implementation guidance but do not override approved PRDs, architecture, ADRs, specifications, or project-level rules.

### `kilo.jsonc`

Defines the global Kilo model and permission configuration.

The Stable-v0.1 routing strategy is intentionally cost-aware:

| Work | Default |
| --- | --- |
| PRD / architecture / specification | GPT-5.6 Sol |
| Project initialization / lightweight orchestration | GPT-5.6 Luna |
| Implementation / verification / fixes / diagnosis | DeepSeek Flash |
| Pre-review | DeepSeek Flash |
| Senior code review | GPT-5.6 Sol |
| Default adversarial review | DeepSeek Flash |
| Optional cross-model review | Claude Sonnet |
| Rare premium escalation | Claude Opus |

Explicit user model selection remains authoritative where supported.

## Verification and review model

Verification is factual:

- `DONE`
- `NOT_DONE`

Delivery-gate state is separate:

- `CLEAR`
- `BLOCKED`
- `CLEAR_WITH_EXCEPTION`

A failed verification is never rewritten to `DONE`.

A human-authorized waiver can establish `CLEAR_WITH_EXCEPTION` for an exact verification report, implementation state, failure set, and expiry while preserving the original `NOT_DONE` result.

Production review is cost-controlled:

1. DeepSeek pre-review
2. GPT-5.6 Sol senior review only when pre-review returns `READY_FOR_SENIOR_REVIEW`
3. CI
4. PR / merge
5. human-approved production deployment

## Architecture and operating cost

Cloud and operating cost are first-class architecture concerns.

Architecture is expected to document and challenge:

- fixed recurring cost
- variable/usage-based cost
- storage cost
- network/data-transfer cost
- observability cost
- scaling characteristics
- operational burden
- major cost drivers and risks
- irreversible platform or recurring-cost commitments

The default preference is the simplest architecture that provides the required production qualities at the lowest practical operating cost.

## Installation / local use

The contents of the repository's `kilo/` directory are intended to represent the global Kilo configuration directory.

On Windows, the global configuration location is typically:

```text
C:\Users\<username>\.config\kilo
```

The effective layout should therefore look like:

```text
C:\Users\<username>\.config\kilo
├── AGENTS.md
├── kilo.jsonc
├── agents\
├── commands\
├── contracts\
├── smoke\
└── skills\
```

How the repository is cloned, copied, linked, or synchronized into that location is a local setup choice.

Keep credentials and API keys out of version control. Use environment variables or provider-specific secure configuration for secrets.

## About README files in the global config directory

A plain `README.md` is documentation only.

Kilo's global instruction loading is based on recognized instruction/configuration locations such as `AGENTS.md`, `kilo.jsonc`, and the dedicated commands/agents directories. A `README.md` placed in the global configuration directory does not become a global instruction file merely because it is present there.

This repository-level README is kept at the repository root so GitHub can present normal project documentation. If a copy also ends up under the local Kilo configuration directory, it is still harmless ordinary documentation.

## Project initialization

`/project-init` operationalizes approved architecture into a project repository.

Among other things it prepares project instructions, verification commands, workflow artifact directories, skill coverage, and synchronizes the Stable-v0.1 evidence contract into:

```text
docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md
```

The project copy must match the global canonical contract exactly.

## Versioning

Stable framework releases are tagged in Git.

The first frozen release is:

```text
stable_v_0.1.0
```

After a stable tag, framework changes should be treated as deliberate versioned changes rather than incidental edits.

## Smoke testing

Release validation is documented in:

```text
kilo/smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md
```

The runbook can be followed end-to-end from `/grill` or resumed from any valid workflow stage based on persisted repository artifacts. It does not require prior conversational history.

Two smoke-test depths are defined.

### FAST_SMOKE

Use `FAST_SMOKE` after low-risk framework changes such as:

- documentation-only updates
- comments or examples
- non-behavioral configuration cleanup
- changes that do not alter lifecycle routing, verification freshness, review gates, waiver semantics, diagnosis/fix routing, adversarial reconciliation, or model orchestration

Typical FAST_SMOKE coverage includes:

- static release/configuration checks
- project-init evidence-contract propagation
- first-spec uncommitted verification
- review-before-commit
- identical commit remaining fresh
- stale-evidence rejection after content mutation
- one `/fix → /verify` loop
- one fail-closed evidence case
- static model-routing checks

FAST_SMOKE normally avoids unnecessary diagnosis, waiver, paid Claude, repeated senior review, integration/E2E suites, and expensive environment setup unless the changed area specifically requires them.

### FULL_SMOKE

Use `FULL_SMOKE`:

- before a milestone/stable release
- after lifecycle-routing changes
- after verification/evidence-contract changes
- after review-gate changes
- after waiver changes
- after `/fix` or `/diagnose` routing changes
- after adversarial/reconciliation changes
- after material model-orchestration changes

FULL_SMOKE exercises the complete restartable workflow, including:

```text
/grill
→ /prd
→ /architect
→ /project-init
→ /spec
→ /implement
→ /verify
→ /review
```

plus the recovery paths:

```text
/verify → NOT_DONE → /fix → /verify

/verify → NOT_DONE
        → /diagnose → /fix → /verify

/verify → NOT_DONE
        → /waive → CLEAR_WITH_EXCEPTION → /review

/review → CHANGES_REQUIRED or REQUEST CHANGES
        → /fix → /verify → /review
```

For `stable_v_0.1.0`, use:

```text
FULL_SMOKE
```

because this release establishes the baseline framework behavior.

### Running smoke tests

Smoke testing is executable through the global `/smoke` command.

Common invocations:

```text
/smoke FAST DEFAULT
/smoke FULL DEFAULT
/smoke FAST fast-micro-library
/smoke FULL full-minimal-api
/smoke FULL full-local-persistence-api
/smoke RESUME <run-id>
/smoke STATUS <run-id>
```

If no fixture is supplied, `/smoke` shows the compatible approved fixture list and asks for a selection rather than inventing one.

Approved fixture metadata lives in:

```text
kilo/smoke/fixtures.json
kilo/smoke/profiles.json
kilo/smoke/failure-recipes.json
```

Current fixtures:

| Fixture | Profile | Purpose |
| --- | --- | --- |
| `fast-micro-library` | FAST | Cheapest lifecycle/evidence/fix smoke fixture |
| `full-minimal-api` | FULL | Default complete workflow fixture |
| `full-local-persistence-api` | FULL | Optional local-persistence-oriented validation |

Failure-injection behavior is separately defined in `kilo/smoke/failure-recipes.json`, so the executor does not infer how to manufacture a failure from prose.

Fixture choice controls the disposable product shape and default test budget. It does **not** choose the implementation technology; `/architect` retains that authority.

A smoke run persists restartable state in the disposable target project under:

```text
docs/verification/smoke/<run-id>.md
```

The Run ID is generated automatically by `/smoke` using:

```text
SMOKE-<PROFILE>-<fixture-id>-<SEQ>
```

Examples:

```text
SMOKE-FAST-fast-micro-library-001
SMOKE-FULL-full-minimal-api-001
```

The Run ID is printed near the top of every smoke response and the run record is created before substantive smoke execution begins.

This allows:

```text
/smoke STATUS <run-id>
```

to show the current profile, fixture, release SHA, stage/scenario, progress, latest verification/review state, model ledger, observed cost, blocker/user action, and next step without executing the workflow.

It also allows:

```text
/smoke RESUME <run-id>
```

to continue after user input, interruption, or a later chat session without depending on conversation memory.

### Smoke-test cost discipline

Smoke testing should prove workflow mechanics with the smallest practical fixture.

Prefer:

- one tiny reusable smoke project/feature
- one or two focused unit tests
- static checks when runtime execution adds no additional evidence
- reuse of valid persisted PRD/architecture/spec/evidence
- Git checkpoints instead of asking models to reconstruct prior states
- zero Claude runtime calls by default

Do not add integration, E2E, cloud, database, browser, load, or similar test infrastructure merely to make the smoke application look production-sized.

The rule is:

> simplify the smoke fixture, not the production workflow contract.

Required production gates must never be weakened just to reduce token consumption.

## Status

Stable-v0.1 focuses on making the workflow deterministic, evidence-driven, production-oriented, and practical to operate without unnecessary frontier-model or infrastructure spend.

The next validation step for `stable_v_0.1.0` is the `FULL_SMOKE` run defined in `kilo/smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md`.
