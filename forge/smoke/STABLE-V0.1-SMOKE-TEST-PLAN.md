# Stable v0.1 Workflow Smoke-Test Runbook

## Purpose

This document is the executable smoke-test and recovery runbook for the Kilo workflow release:

```text
stable_v_0.1.0
```

It is designed to be usable in **two different ways**:

1. as a full end-to-end validation beginning at `/grill`, or
2. as a restartable runbook when the repository is already somewhere in the workflow and repeating earlier stages would be unnecessary or incorrect.

Do **not** assume prior chat history.

Do **not** assume that all earlier stages have already run.

Do **not** blindly restart from `/grill`.

At every stage, first inspect the persisted repository artifacts and current workflow state, then begin from the earliest stage that is actually incomplete, stale, blocked, or invalidated.

The primary lifecycle is:

```text
/grill (optional)
→ /prd
→ /architect
→ /project-init
→ /spec
→ /implement
→ /verify
→ CLEAR or CLEAR_WITH_EXCEPTION
→ /review
→ CI / PR / merge
```

Supporting loops are:

```text
/verify → NOT_DONE → /fix → /verify

/verify → NOT_DONE
        → /diagnose
        → /fix
        → /verify

/verify → NOT_DONE
        → /waive
        → CLEAR_WITH_EXCEPTION
        → /review

/review → CHANGES_REQUIRED or REQUEST CHANGES
        → /fix
        → /verify
        → /review

/architect or /spec
        → adversarial findings
        → RECONCILE_ONLY
        → targeted recheck if materially changed
```

The runbook validates:

- discovery and requirement grilling
- PRD readiness and restart behavior
- architecture ownership and operating-cost considerations
- project initialization
- specification decomposition
- first-spec implementation before any implementation commit
- deterministic verification
- review-before-commit
- evidence freshness
- commit-after-verification behavior
- content and Git mode/type identity
- verification mutation detection
- persisted review evidence
- repair and diagnosis loops
- bounded human waivers
- adversarial reconciliation
- stale downstream-artifact handling
- recovery when a run starts from the middle of the workflow
- low-cost model routing
- zero-Claude-by-default smoke testing

---

# 1. Release Under Test

Validate the exact release/tag:

```text
stable_v_0.1.0
```

Before running any model workflow, record:

- `kilo-configuration` tag
- exact `kilo-configuration` commit SHA
- exact test-project baseline SHA
- Kilo Code version
- Git version
- OS
- shell/runtime information
- materially relevant SDK/tool versions

Do not test an unrecorded moving branch.

If the tag is intentionally moved after documentation-only additions, record the final SHA before testing.

---

# 2. Smoke-Test Repository and Fixture Selection

Use a disposable branch, clone, or worktree based on the reusable project template.

Each fixture declares its own `source_repository` in `smoke/fixtures.json`.

The current Stable-v0.1 fixtures all use:

`subhadlearner/production-ai-project`

Do not assume future fixtures use the same repository.

Recommended branch pattern:

```text
smoke/<profile>-<fixture>-<run-id>
```

Do not mutate protected `main`.

The implementation fixture should be deliberately small. The goal is to test the workflow, not application complexity.

Approved fixture definitions and profile scenario registries are version-controlled in the source repository as:

```text
kilo/smoke/fixtures.json
kilo/smoke/profiles.json
kilo/smoke/failure-recipes.json
```

When installed as the global Kilo configuration, runtime lookups use:

```text
smoke/fixtures.json
smoke/profiles.json
smoke/failure-recipes.json
smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md
```

Do not require the `kilo-configuration` repository checkout to exist at runtime.

Do not invent an additional fixture during an automated smoke run.

## 2.1 Fixture registry

### FAST — `fast-micro-library` (default)

Purpose:

- cheapest lifecycle/evidence validation
- first-spec uncommitted verification
- review-before-commit
- freshness invalidation
- direct fix loop
- malformed evidence

Default application-test budget:

- 1–2 unit tests
- no integration test
- no E2E test
- no persistence/network/cloud

### FULL — `full-minimal-api` (default)

Purpose:

- complete lifecycle
- recovery loops
- diagnosis
- waiver
- review
- adversarial reconciliation
- arbitrary-stage restart

Product shape:

- one small HTTP behavior
- one validation/error path
- in-memory state only
- no external DB/cloud/auth/queue/container requirement

Default application-test budget:

- 1–2 unit tests
- at most 1 lightweight in-process integration test
- no E2E suite

### FULL — `full-local-persistence-api` (optional)

Use only when the framework change being validated materially touches persistence/database guidance, project-init persistence setup, or integration verification.

Default application-test budget:

- 1–2 unit tests
- 1 focused embedded/local persistence-backed integration test
- no E2E suite

This is intentionally not the FULL default because it costs more tokens and runtime.

## 2.2 Executing the runbook

The runbook is orchestrated through:

```text
/smoke FAST DEFAULT
/smoke FULL DEFAULT
```

Explicit fixture selection:

```text
/smoke FAST fast-micro-library
/smoke FULL full-minimal-api
/smoke FULL full-local-persistence-api
```

If the profile is supplied without a fixture, the orchestrator must show the compatible registry entries and request a choice.

Resume an interrupted run:

```text
/smoke RESUME <run-id>
```

Inspect without executing:

```text
/smoke STATUS <run-id>
```

The smoke-run state is persisted in the disposable project under:

```text
docs/verification/smoke/<run-id>.md
```

The Run ID is allocated automatically before substantive smoke execution using:

```text
SMOKE-<PROFILE>-<fixture-id>-<SEQ>
```

Examples:

```text
SMOKE-FAST-fast-micro-library-001
SMOKE-FULL-full-minimal-api-001
SMOKE-FULL-full-minimal-api-002
```

The orchestrator scans existing run records for the selected profile/fixture, increments the highest valid three-digit suffix, creates the new run record immediately, and never overwrites an existing run.

Every smoke response must repeat the active Run ID near the top.

The run record, not chat history, is the continuation authority.

`/smoke STATUS <run-id>` is read-only and reports progress, latest verification/review state, model/cost ledger, blockers, and the exact next action without invoking lifecycle/reviewer models.

`/smoke RESUME <run-id>` reconstructs continuation from the run record plus current repository evidence and resumes from the earliest still-required or invalidated stage.

## 2.3 Fixture versus architecture authority

The fixture defines:

- product shape
- profile compatibility
- test-budget target
- permitted failure-injection recipes

The fixture does **not** choose:

- programming language
- runtime
- framework
- persistence technology when not intrinsic to the selected fixture
- cloud provider
- IaC tooling

Those remain owned by `/architect`.

A fixture test budget never permits skipping a genuinely applicable check required by the approved architecture/specification.

---

## 2.4 Canonical scenario IDs

`smoke/profiles.json` is authoritative for which scenarios are required or optional for each profile.

The runbook uses these stable scenario IDs for persisted progress:

| Scenario ID | Runbook coverage / acceptance meaning |
| --- | --- |
| `static-release-gate` | Static command, routing, policy, evidence-contract, and cost-policy invariants pass |
| `grill` | Discovery can complete/block/resume without repeating settled decisions |
| `prd` | PRD readiness/blocking and product-authority routing work |
| `architect` | Architecture readiness/blocking, cost treatment, and authority routing work |
| `project-init-contract-propagation` | Project init creates required directories and synchronizes the evidence contract |
| `spec` | Specification readiness/blocking and upstream routing work |
| `implement` | Approved spec implementation reaches ready-for-verify without overstepping authority |
| `first-uncommitted-verify` | Fully uncommitted first-spec implementation reaches deterministic verification |
| `review-before-commit` | Fresh uncommitted implementation can enter the normal review pipeline |
| `identical-commit-freshness` | Committing identical verified contents preserves `MATCH` |
| `content-mutation-stale-evidence` | Identity-bearing content change blocks review with `MISMATCH` |
| `mode-type-identity` | Git mode/type change produces `MISMATCH` or valid platform `UNRECONSTRUCTABLE` |
| `verification-mutation` | Verification-time implementation mutation blocks delivery |
| `direct-fix-loop` | `NOT_DONE → /fix → /verify → /review` completes correctly |
| `diagnose-fix-loop` | `NOT_DONE → /diagnose → /fix → /verify → /review` completes correctly |
| `waive-review-loop` | Safe waivable `NOT_DONE` becomes only `CLEAR_WITH_EXCEPTION` and can enter review |
| `stale-waiver` | Implementation identity change invalidates waiver applicability |
| `malformed-evidence` | Malformed/unavailable evidence fails closed as `UNRECONSTRUCTABLE` |
| `fail-closed-evidence` | FAST profile proves at least one stale/malformed/unreconstructable evidence case stops review |
| `evidence-exclusion` | Evidence-only paths do not change implementation identity; specs/architecture/code/config do |
| `adversarial-reconcile-only` | Material findings reconcile through `RECONCILE_ONLY`, not full re-authoring |
| `arbitrary-stage-resume` | Fresh session resumes from persisted repository state without chat memory |
| `upstream-rerouting` | Blockers route to the correct upstream authority and regenerate affected downstream work |
| `pre-review-blocker` | Blocking DeepSeek pre-review persists evidence and skips senior review |
| `static-model-routing` | FAST profile validates configured model routes without unnecessary paid runtime calls |
| `static-claude-routing` | FULL profile validates Claude routes statically with zero default Claude calls |
| `paid-claude-runtime` | Optional explicitly authorized paid cross-model runtime check |

A scenario is complete only when the run record contains evidence satisfying its mapped acceptance meaning.

Do not count a phase merely because its command was invoked.

---

# 3. Cost Policy

## 3.1 Default routing

Use Stable-v0.1 defaults:

| Work | Default |
| --- | --- |
| Discovery / PRD / architecture / spec | GPT-5.6 Sol |
| Project initialization | GPT-5.6 Luna |
| Implementation | DeepSeek Flash |
| Verification | DeepSeek Flash |
| Fix | DeepSeek Flash |
| Diagnosis | DeepSeek Flash |
| Default adversarial review | DeepSeek Flash |
| Pre-review | DeepSeek Flash |
| Senior review | GPT-5.6 Sol |

## 3.2 Claude policy

Do not invoke Claude Sonnet, Haiku, or Opus merely to smoke-test routing.

Validate their routing statically.

A paid Claude invocation is allowed only when explicitly approved as a separate isolated test.

Expected default:

```text
Claude invocation count: 0
Claude spend: 0
```

## 3.3 Repetition stop-loss

Never repeatedly rerun an expensive model merely because a workflow did not behave as expected.

If the same framework symptom occurs twice with materially unchanged inputs:

1. stop,
2. preserve the evidence,
3. classify the defect,
4. diagnose the workflow,
5. fix it in a later framework version.

Do not consume budget by brute-force retries.

## 3.4 Token and runtime-cost optimization strategy

The smoke test exists to prove **workflow mechanics**, not to prove production readiness of the disposable smoke application.

Minimize tokens by reducing unnecessary scope while preserving every workflow invariant being tested.

### Principle A — use one micro-fixture for almost everything

Use one tiny project/feature throughout the smoke test.

Recommended shape:

```text
one small library/module
one production function
one public behavior
one or two unit tests
no network
no database
no cloud
no authentication
no queue
no filesystem dependency unless needed for a specific test
```

Do not create separate applications for:

- fix testing
- diagnosis testing
- waiver testing
- freshness testing
- review testing

Mutate and restore the same disposable fixture between scenarios.

This reduces:

- repeated repository discovery
- repeated architecture/spec context
- repeated generated code
- repeated test generation
- repeated verification output
- repeated reviewer context

### Principle B — test the workflow at the lowest sufficient layer

For the smoke application, prefer:

```text
unit test
> component/integration test
> E2E test
```

Use the lowest layer that proves the workflow behavior.

Default smoke-test test surface:

- 1 happy-path unit test
- 1 failure/boundary unit test only when needed by the spec
- 1 intentionally manipulated failure for recovery-loop testing

Do **not** add merely for smoke testing:

- broad integration suites
- E2E browser/API suites
- contract-test matrices
- load tests
- soak tests
- fuzzing/property-based suites
- large parameterized datasets
- coverage-maximization tests
- mutation testing
- multiple test projects
- containerized dependency stacks

unless the scenario specifically exists to validate one of those workflow capabilities.

The production workflow may require such tests for real projects. Their omission here is a property of the **smoke fixture**, not a weakening of production policy.

### Principle C — make non-applicable capabilities truly non-applicable

Choose a fixture for which the following are genuinely absent:

- external APIs
- databases
- queues
- cloud resources
- IAM
- containers
- infrastructure-as-code
- browser UI
- distributed consistency
- migrations

Then the smoke specification and architecture can truthfully mark those concerns as not applicable.

Do not configure expensive tooling simply so the smoke test can say it ran.

For example, do not introduce:

- LocalStack
- Docker Compose
- a test database
- Playwright
- Selenium
- cloud emulators
- vulnerability scanners requiring new infrastructure

unless validating that exact capability is the purpose of the scenario.

### Principle D — one acceptance criterion should prove one workflow behavior

Keep the smoke spec intentionally narrow.

A suitable core acceptance set is:

```text
AC-1: the deterministic function returns the expected result
AC-2: invalid input follows one defined boundary behavior
```

Do not create many product requirements merely to make the PRD/spec appear realistic.

The planning stages are being tested for:

- authority
- artifact persistence
- routing
- blocked-state handling
- downstream handoff

not for the ability to write a large product.

### Principle E — keep planning artifacts minimal but complete

For `/grill`, `/prd`, `/architect`, and `/spec`:

- provide only the micro-fixture's actual requirements
- answer only frontier questions
- avoid speculative future roadmap
- avoid optional capabilities
- avoid multiple architecture alternatives once requirements clearly select a simple design
- avoid long non-functional requirement catalogs unrelated to the fixture

A smoke architecture can legitimately be:

```text
local deterministic library
no persistence
no network
no deployment
no cloud infrastructure
unit-test-only verification
```

Operating-cost analysis should still be present and can correctly conclude:

```text
fixed production infrastructure cost: none for this fixture
variable cloud cost: none
external service cost: none
operational burden: minimal/local only
```

This validates the architecture cost requirement without creating infrastructure to measure.

### Principle F — never regenerate a valid artifact for a downstream test

Once a stage has produced a valid reusable artifact, reuse it.

Examples:

- do not rerun `/prd` to test `/verify`
- do not rerun `/architect` for each failure scenario
- do not rerun `/spec` after a simple implementation defect
- do not rerun `/implement` after a defect when `/fix` is the correct path
- do not rerun `/verify` before deliberately testing that stale evidence blocks `/review`

A runtime invocation is justified only when:

1. the artifact is missing,
2. the artifact is stale/invalidated,
3. the scenario specifically tests that workflow stage,
4. upstream authority changed.

### Principle G — use repository checkpoints between scenarios

Because the smoke repository is disposable, establish small human-controlled checkpoints after important valid states.

Suggested checkpoints:

```text
CHECKPOINT-A: project-init ready
CHECKPOINT-B: spec ready
CHECKPOINT-C: implementation verified but uncommitted
CHECKPOINT-D: implementation committed and verified/reviewed
CHECKPOINT-E: clean post-repair state
```

Use branches/commits/worktrees appropriate to the disposable environment to restore these states.

Do not ask an LLM to reconstruct a prior fixture when Git can restore it deterministically.

Do not use destructive cleanup on a non-disposable repository.

### Principle H — negative freshness tests should consume zero reviewer tokens

For scenarios such as:

- content mutation after verification
- mode/type mutation
- malformed evidence
- stale waiver
- wrong branch/scope
- `UNRECONSTRUCTABLE`

the freshness gate must stop `/review` **before** invoking:

- DeepSeek pre-review
- GPT-5.6 Sol senior review

Therefore these scenarios should consume only orchestration/freshness-validation work, not reviewer-model tokens.

If a reviewer runs after freshness has already failed, treat that as a framework defect.

### Principle I — run successful senior review only as many times as necessary

A complete smoke test does not need senior review for every scenario.

Required senior-review executions should normally be limited to:

1. one normal `DONE + CLEAR + MATCH` review-before-commit path
2. optionally one `CLEAR_WITH_EXCEPTION` waiver path when validating that senior review receives and reasons over the waiver

All other review scenarios should either:

- reuse persisted review evidence, or
- intentionally stop at freshness/pre-review gates.

Do not rerun senior review merely to reconfirm the same clean code.

### Principle J — use one cheap pre-review blocker

To test:

```text
CHANGES_REQUIRED
Senior Review: NOT_RUN
```

inject one obvious review defect that is not already caught by deterministic verification.

Keep it small.

Examples:

- clearly misleading variable/API naming that violates an explicit project rule
- unnecessary duplicate logic against an established repository convention
- a deliberately documented maintainability issue that deterministic tests do not detect

Do not create a large defective implementation just to exercise pre-review.

The objective is to prove that senior review is skipped.

### Principle K — reuse failures across adjacent scenarios only when semantics remain valid

Reuse is encouraged, but do not distort routing.

Allowed:

- use one `NOT_DONE` deterministic defect for `/fix`
- restore clean state, then create one ambiguous deterministic symptom for `/diagnose`
- restore clean state, then create one trivial policy-allowed quality failure for `/waive`

Do not use the obvious `/fix` defect for `/diagnose`, because that would falsely teach that every failure requires diagnosis.

Do not use a real behavioral defect for a trivial waiver merely to save one verification invocation.

Correct workflow semantics take precedence over token minimization.

### Principle L — static-check configuration instead of invoking models

Use static inspection for:

- Claude route existence
- Opus/Sonnet permissions
- model aliases
- task model-selection configuration
- command existence
- agent existence
- skill existence
- lifecycle text
- `AUTHOR / CONTINUE / RECONCILE_ONLY` support
- evidence-contract equality
- security policy presence
- cloud/operating-cost policy presence
- smoke-test cost policy

Do not invoke a model solely to prove that a configuration entry exists.

### Principle M — avoid optional adversarial cycles

Run one bounded DeepSeek adversarial scenario to prove the mechanism.

If the challenged artifact does not materially change after reconciliation:

- do not run a second adversarial pass.

If it does materially change:

- at most one targeted follow-up pass is sufficient for smoke validation.

Do not test Sonnet and Opus runtime routes by default.

### Principle N — minimize repository-reading context

Each command should consume only the material context required by its authority stage.

For the smoke fixture:

- do not create unrelated files
- do not add large sample data
- do not add generated lockfile noise unless required
- do not include unrelated historical docs
- keep the test project deliberately small

When invoking a stage, identify the target spec/change explicitly so the workflow does not need to discover unrelated artifacts.

Token reduction must come from **irrelevant-context elimination**, not from omitting relevant constraints.

### Principle O — keep persisted evidence concise

Verification/review/diagnostic evidence must remain complete, but avoid:

- full successful test logs
- repeated source-code dumps
- repeated PRD/architecture prose
- duplicate command output
- entire environment dumps

Persist:

- command
- exit status
- concise relevant evidence
- failure excerpt when needed
- artifact references

Do not paste hundreds of passing log lines when the exit status and concise summary prove the check executed.

### Principle P — do not optimize by weakening gates

Token savings must never come from:

- deleting required checks
- marking applicable checks `NOT_APPLICABLE`
- weakening assertions
- lowering real project thresholds
- suppressing security failures
- avoiding a required fresh `/verify`
- bypassing pre-review/senior review on the one path meant to exercise them
- treating stale evidence as reusable

The smoke fixture should be simpler; the workflow contract should not be weaker.

## 3.5 Recommended minimal runtime invocation budget

For a full end-to-end run from `/grill`, target approximately this number of substantive model invocations:

| Stage/scenario | Target runtime invocations |
| --- | ---: |
| `/grill` | 1 |
| `/prd` | 1 |
| `/architect` | 1 |
| project-init | 1 |
| `/spec` | 1 |
| `/implement` | 1 |
| first successful `/verify` | 1 |
| normal review: pre-review | 1 |
| normal review: senior | 1 |
| obvious failure `/verify` | 1 |
| `/fix` | 1 |
| post-fix `/verify` | 1 |
| ambiguous failure `/verify` | 1 |
| `/diagnose` | 1 |
| `/fix` after diagnosis | 1 |
| post-diagnosis `/verify` | 1 |
| trivial waiver failure `/verify` | 1 |
| `/waive` | 1 |
| waiver review pre-review | 1 |
| waiver senior review | 0–1 |
| one adversarial challenge | 1 |
| targeted reconciliation | 1 |
| optional follow-up adversary | 0–1 |
| freshness/malformed/stale negative tests | reviewer calls: **0** |
| Claude runtime calls | **0** |

This table is a target, not a mandate.

If a valid artifact already exists because the smoke run resumes mid-workflow, subtract the corresponding completed stages.

Do not create artificial invocations to reach the target count.

## 3.6 Fast smoke versus full smoke

Two execution depths are allowed.

### FAST_SMOKE

Use after a documentation/config-only framework change.

Required:

- static release gate
- project-init contract propagation
- first uncommitted verify
- review-before-commit
- identical commit remains fresh
- content mutation stale check
- one fix loop
- one fail-closed evidence case
- static model routing

Normally omit:

- diagnosis
- waiver
- adversarial runtime
- mode/type test when environment setup is costly
- second senior review

### FULL_SMOKE

Use before a milestone release or after changes to:

- lifecycle routing
- verification evidence
- review gates
- waiver semantics
- fix/diagnosis routing
- adversarial reconciliation
- model orchestration

Run all required acceptance criteria in this document.

For `stable_v_0.1.0`, use:

```text
FULL_SMOKE
```

because Stable v0.1 establishes the baseline framework behavior.

---

# 4. Core Rule: Determine Where to Start

Before running any workflow command, determine the current repository state.

Inspect, where present:

```text
docs/discovery/
docs/prd/
docs/architecture/
docs/adr/
docs/specs/
docs/diagnostics/
docs/verification/
docs/verification/waivers/
docs/reviews/
docs/workflow/
AGENTS.md
README.md
.kilo/rules/
.kilo/skills/
```

Also inspect:

- current branch
- current HEAD
- current working-tree changes
- latest applicable persisted evidence
- whether upstream artifacts have changed since downstream artifacts were generated
- whether any current artifact is explicitly blocked

Do not use the newest artifact globally merely because it is newest.

Use the latest **applicable** artifact for the current:

- product/change
- specification
- branch
- repository state

---

# 5. Start/Resume Decision Table

Use this table before spending model budget.

| Current situation | Start/resume at |
| --- | --- |
| Idea is vague, coupled, high-risk, or unresolved | `/grill` |
| Product intent is already clear but no approved PRD exists | `/prd` |
| Approved PRD exists, architecture missing | `/architect` |
| Architecture is blocked by product ambiguity | `/prd` |
| Architecture is ready, repo not initialized | `/project-init` |
| Project-init reports architecture conflict | `/architect` |
| Architecture + project-init are ready, no implementation spec | `/spec` |
| Spec is blocked by requirement ambiguity | `/prd` |
| Spec is blocked by architecture ambiguity | `/architect` |
| Spec is blocked by incomplete project initialization | `/project-init` |
| Approved spec exists and implementation has not started | `/implement` |
| Implementation is blocked by spec ambiguity | `/spec` |
| Implementation is blocked by architecture change | `/architect` |
| Implementation is blocked only by repository/environment state | fix environment, then rerun `/implement` |
| Implementation exists but has never been deterministically checked | `/verify` |
| Verification is `DONE + CLEAR` | `/review` |
| Verification is `NOT_DONE` and defect is understood | `/fix` |
| Verification is `NOT_DONE` and root cause is uncertain/intermittent | `/diagnose` |
| Verification is `NOT_DONE`, risk is explicitly accepted and waivable | `/waive` |
| Verification evidence is stale or `MISMATCH` | `/verify` |
| Verification evidence is `UNRECONSTRUCTABLE` | `/verify` |
| Pre-review returns `CHANGES_REQUIRED` | `/fix → /verify → /review` |
| Senior review returns `REQUEST CHANGES` | `/fix → /verify → /review` |
| Review is `APPROVE` | CI / PR / merge |
| High-risk architecture/spec decision should be challenged | `/adversarial-check` or built-in adversarial path |
| Adversarial findings require revision of existing architecture/spec | `RECONCILE_ONLY`, not full re-authoring |

---

# 6. Artifact Invalidation Rules

A workflow should resume from the **earliest invalidated authority stage**, not necessarily from the command that failed last.

## 6.1 Product decision changed

If an approved product requirement or acceptance criterion materially changes:

```text
/prd
→ /architect if architecture may be affected
→ /project-init if technical baseline/repo rules may be affected
→ /spec
→ /implement or /fix
→ /verify
→ /review
```

Do not retain downstream artifacts that contradict the new product requirement.

## 6.2 Architecture decision changed

If architecture, persistence strategy, public system boundary, reliability/security guarantee, or major technology changes:

```text
/architect
→ /project-init
→ /spec
→ /implement or /fix
→ /verify
→ /review
```

Do not skip project-init when repository instructions, verification commands, skills, or technology baseline need synchronization.

## 6.3 Project initialization changed only

If architecture is unchanged but project rules/tooling are incomplete:

```text
/project-init
→ /spec only if spec assumptions need regeneration
→ otherwise resume implementation/fix
→ /verify
→ /review
```

## 6.4 Specification changed

If implementation requirements or acceptance criteria change without changing product/architecture authority:

```text
/spec
→ /implement or /fix
→ /verify
→ /review
```

## 6.5 Implementation changed

Any implementation-state change after reusable verification evidence requires:

```text
/verify
```

before review can proceed.

## 6.6 Review findings changed code

After `/fix` changes implementation:

```text
/verify
→ /review
```

Never jump directly from `/fix` back to senior review.

---

# 7. Phase 0 — Static Release Gate

**Cost: zero/negligible**

Run before any end-to-end smoke workflow.

Confirm:

## 7.1 Commands exist

Expected commands:

- `/grill`
- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`
- `/verify`
- `/review`
- `/fix`
- `/diagnose`
- `/waive`
- `/adversarial-check`

## 7.2 Planning modes

Confirm `planning-worker` supports:

- `AUTHOR`
- `CONTINUE`
- `RECONCILE_ONLY`

If no valid mode is supplied, the worker must not guess.

## 7.3 Model routing

Confirm normal lifecycle does not require Claude.

## 7.4 Architecture cost policy

Confirm architecture still treats cloud/operating cost as first-class and evaluates:

- fixed recurring cost
- variable cost
- storage cost
- network/data transfer
- observability cost
- scaling behavior
- operational burden
- cost drivers
- cost risks
- irreversible recurring-cost/platform commitments

## 7.5 Evidence contract

Confirm these are byte-for-byte identical:

```text
kilo/contracts/implementation-state-evidence-v1.md

docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md
```

Confirm contract includes:

- canonical manifest authority
- path identity
- effective Git mode/type
- content/blob identity
- `MATCH`
- `MISMATCH`
- `UNRECONSTRUCTABLE`
- exact evidence exclusion set
- ignored-file boundary
- environment boundary
- waiver binding
- fail-closed semantics

If Phase 0 fails, stop.

---

# 8. Phase 1 — /grill

## When to run

Run `/grill` when the product idea is:

- ambiguous
- broad
- coupled
- high-stakes
- unclear on priorities/trade-offs
- missing important decisions

Skip `/grill` when product intent is already sufficiently clear for PRD authoring.

Skipping is valid.

## Inputs

Provide the product idea and relevant constraints.

The user does not need to answer questions whose answers can be safely discovered from existing repository artifacts or authoritative sources.

## Expected behavior

The workflow should:

- inspect discoverable facts before asking
- ask only unresolved frontier questions
- avoid prematurely choosing architecture
- persist discovery under `docs/discovery/`

## Expected statuses

Success:

```text
DISCOVERY_READY
```

Blocked:

```text
DISCOVERY_BLOCKED
```

## Resume rules

If `DISCOVERY_BLOCKED`:

1. resolve the specific unanswered product decision,
2. rerun `/grill`,
3. do not restart unrelated settled questions.

If a discovery artifact already exists and remains valid, do not rerun `/grill` merely because a later stage failed.

## Next step

```text
DISCOVERY_READY → /prd
```

---

# 9. Phase 2 — /prd

## When to run

Run when:

- discovery is ready, or
- discovery was legitimately skipped because requirements are already clear.

## Reuse existing PRD

If an approved PRD already exists and the product intent has not materially changed, do not rerun `/prd`.

Resume downstream.

## Expected behavior

PRD should define product requirements and constraints without inventing architecture.

Persist approved PRD under:

```text
docs/prd/
```

## Expected statuses

```text
PRD_READY
```

or:

```text
PRD_BLOCKED
```

## If blocked

Typical owner:

```text
PRODUCT
```

Typical next command:

```text
/prd
```

after user clarification.

## Regression test

Create one deliberate unresolved product decision.

Confirm:

- PRD refuses to invent the answer
- returns `PRD_BLOCKED`
- points to the exact missing decision
- rerunning after clarification resolves only that issue

## Next step

```text
PRD_READY → /architect
```

---

# 10. Phase 3 — /architect

## Preconditions

Require:

- approved PRD
- relevant existing architecture/ADRs when modifying an existing system

Do not start architecture from an unapproved or blocked PRD.

## What architecture owns

Architecture chooses major technical decisions.

Smoke-test that it covers, where relevant:

- language/runtime
- framework
- persistence
- cloud/provider
- IaC
- networking
- security
- observability
- reliability
- deployment
- operational burden
- operating/cloud cost

## Operating-cost validation

Explicitly confirm the architecture documents:

- estimated cloud cost
- fixed recurring cost
- usage-based/variable behavior
- major cost drivers
- cost risks
- operational burden

The smoke test should fail if cost is silently ignored in a cloud architecture.

## Expected statuses

```text
ARCHITECTURE_READY
```

or:

```text
ARCHITECTURE_BLOCKED
```

## Blocked routing

Product ambiguity:

```text
owner: PRODUCT
next: /prd
```

Technical decision unresolved:

```text
owner: ARCHITECTURE
next: /architect
```

Explicit premium/user decision required:

```text
owner: USER_APPROVAL
next: /architect
```

## Repetition rule

Do not rerun the full architecture workflow merely because an adversarial check found a bounded issue.

Use:

```text
MODE: RECONCILE_ONLY
```

against:

- existing architecture
- affected ADRs
- findings
- relevant contract/invariants

## Next step

```text
ARCHITECTURE_READY → /project-init
```

---

# 11. Phase 4 — /project-init

## Preconditions

Require:

- approved PRD
- `ARCHITECTURE_READY`
- relevant ADRs

## Responsibilities

Project-init operationalizes architecture.

It should update/preserve:

- `AGENTS.md`
- `README.md`
- `.kilo/rules/`
- `.kilo/skills/`

It must ensure:

```text
docs/discovery/
docs/prd/
docs/architecture/
docs/adr/
docs/specs/
docs/diagnostics/
docs/verification/
docs/verification/waivers/
docs/reviews/
docs/workflow/
```

and:

```text
docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md
```

The project evidence contract must be synchronized verbatim with the global canonical contract.

## Expected statuses

```text
PROJECT_INIT_READY
```

or:

```text
PROJECT_INIT_BLOCKED
```

## Blocked routing

Architecture conflict/missing decision:

```text
/architect
```

Repository-local initialization issue:

```text
/project-init
```

Approval needed:

```text
/project-init
```

after approval.

## Resume rule

If project-init is already ready and architecture has not changed, do not rerun it merely because a spec or implementation failed.

## Negative test

Make exact evidence-contract synchronization unavailable.

Expected:

```text
PROJECT_INIT_BLOCKED
```

No independently summarized replacement contract is acceptable.

## Next step

```text
PROJECT_INIT_READY → /spec
```

---

# 12. Phase 5 — /spec

## Preconditions

Require:

- approved PRD
- `ARCHITECTURE_READY`
- `PROJECT_INIT_READY`
- project `AGENTS.md` aligned with approved stack

## Expected behavior

Specifications should be independently implementable.

For greenfield work, explicitly create bootstrap/CI/repository setup specifications where required instead of pretending those capabilities already exist.

Each spec should include:

- scope
- relevant architecture
- acceptance criteria
- testing expectations
- TDD applicability
- security verification needs
- DoD

Definition of Done must ultimately require:

```text
/verify → DONE + CLEAR
```

or a valid separate:

```text
CLEAR_WITH_EXCEPTION
```

## Expected statuses

```text
SPEC_READY
```

or:

```text
SPEC_BLOCKED
```

## Blocked routing

Requirement ambiguity:

```text
/prd
```

Architecture issue:

```text
/architect
```

Initialization issue:

```text
/project-init
```

Local decomposition issue:

```text
/spec
```

## Adversarial repetition rule

If a spec is challenged:

- do not regenerate the whole specification set
- use `RECONCILE_ONLY`
- supply the challenged spec + findings + minimum required architecture/contract context

## Resume rule

If several specs already exist and only one is being implemented, do not rerun `/spec` for completed unaffected specs.

## Next step

```text
SPEC_READY → /implement
```

for one selected specification.

---

# 13. Phase 6 — /implement

## Preconditions

Require:

- approved implementation-ready spec
- approved architecture
- initialized project context
- correct specification branch/worktree

## Branch behavior

Preferred branch:

```text
spec/<spec-id>-<short-description>
```

If an appropriate branch already exists, reuse it.

Do not automatically discard unrelated work.

## TDD behavior

Where applicable:

```text
red
→ green
→ next thin slice
```

If TDD is required but the spec lacks a viable observable seam:

```text
IMPLEMENTATION_BLOCKED
owner: SPECIFICATION
next: /spec
```

Do not invent brittle private-method tests.

## Expected success status

```text
IMPLEMENTATION_READY_FOR_VERIFY
```

## Expected blocked status

```text
IMPLEMENTATION_BLOCKED
```

## Blocked routing

Repository/environment issue:

```text
fix repository/environment
→ /implement
```

Spec issue:

```text
/spec
```

Architecture issue:

```text
/architect
```

Approval for a valid new dependency:

```text
approve
→ /implement
```

## Critical first-spec test

For the smoke fixture, do **not commit** the implementation after `/implement`.

The first implementation may consist entirely of:

- modified tracked files
- untracked non-ignored files

That state must still be verifiable.

## Next step

```text
IMPLEMENTATION_READY_FOR_VERIFY → /verify
```

---

# 14. Phase 7 — /verify

## When to run

Run after:

- `/implement`
- `/fix`
- any identity-bearing implementation change
- stale verification evidence
- `MISMATCH`
- `UNRECONSTRUCTABLE`

## First-spec/no-commit scenario

The repository must already have a baseline HEAD.

The implementation itself does not need a commit.

The canonical implementation-state manifest must capture:

- changed tracked paths
- untracked non-ignored paths
- effective Git mode/type
- blob/content identity

## Expected evidence

Persist a new report under:

```text
docs/verification/
```

Include:

- verification ID
- spec/change identity
- branch
- verification base HEAD
- evidence contract version
- canonical manifest
- fingerprint
- freshness result
- executed commands
- acceptance criteria
- security evidence
- environment assumptions
- result
- delivery gate

## Verification truth

Only:

```text
DONE
NOT_DONE
```

## Delivery gate

Possible states:

```text
CLEAR
BLOCKED
```

`CLEAR_WITH_EXCEPTION` is never created inside `/verify`.

## Expected success

```text
Verification Result: DONE
Delivery Gate: CLEAR
Freshness: MATCH
```

## Expected failure

```text
Verification Result: NOT_DONE
Delivery Gate: BLOCKED
```

## Checks pass but repository changes during verification

Expected:

```text
Verification Result: DONE
Freshness: MISMATCH or UNRECONSTRUCTABLE
Delivery Gate: BLOCKED
```

Then rerun `/verify` after stabilizing the state.

## Routing from NOT_DONE

Known repair:

```text
/fix
```

Unclear/intermittent:

```text
/diagnose
```

Explicit accepted waivable risk:

```text
/waive
```

---

# 15. Phase 8 — /review before commit

Immediately after a successful first-spec verification, leave implementation uncommitted.

Run:

```text
/review
```

## Pre-review gate

Before any reviewer model:

- choose latest applicable verification report
- validate same spec/change
- validate same branch
- reconstruct manifest from recorded base HEAD
- require canonical byte-for-byte `MATCH`

If no applicable evidence exists:

```text
STOP
→ /verify
```

If stale:

```text
STOP
→ /verify
```

## Review sequence

1. DeepSeek pre-review
2. if `READY_FOR_SENIOR_REVIEW`, GPT-5.6 Sol senior review
3. persist one review artifact

## Pre-review blocker

Expected:

```text
CHANGES_REQUIRED
Senior Review: NOT_RUN
```

Next:

```text
/fix
→ /verify
→ /review
```

## Senior blocker

Expected:

```text
REQUEST CHANGES
```

Next:

```text
/fix
→ /verify
→ /review
```

## Success

Expected:

```text
APPROVE
```

Next:

```text
CI
→ PR
→ merge
```

## Pass condition

Review succeeds while implementation is still uncommitted.

No artificial commit requirement exists.

---

# 16. Phase 9 — Commit identical verified state

After successful verification/review:

1. commit the exact implementation state,
2. do not change contents,
3. do not change effective Git mode/type.

Re-enter `/review` freshness checking.

HEAD now differs from verification-time HEAD.

Expected:

```text
MATCH
```

A later commit of identical verified state must remain valid.

---

# 17. Phase 10 — Content mutation stale-evidence test

Start from fresh verified evidence.

Modify one identity-bearing byte.

Do not rerun verification.

Run `/review`.

Expected:

```text
MISMATCH
```

Review must stop before pre-review.

Next:

```text
/verify
```

---

# 18. Phase 11 — Git mode/type identity test

Establish fresh evidence.

Change only mode/type, where reliably supported:

- `100644 → 100755`
- file → symlink
- gitlink transition

Do not alter content if testing executable bit.

Expected:

```text
MISMATCH
```

If platform cannot reliably determine mode/type:

```text
UNRECONSTRUCTABLE
```

Both must fail closed.

On Windows, use WSL for the specific mode test if necessary rather than faking mode semantics.

---

# 19. Phase 12 — Verification mutation test

Use a disposable verification behavior that changes an identity-bearing non-evidence path while verification runs.

Expected:

```text
Verification Result: DONE
Freshness: MISMATCH
Delivery Gate: BLOCKED
```

assuming checks themselves pass.

Then restore/stabilize and rerun:

```text
/verify
```

---

# 20. Phase 13 — /fix loop

Introduce a deterministic defect.

Run:

```text
/verify
```

Expected:

```text
NOT_DONE
BLOCKED
```

Then:

```text
/fix
```

## Fix evidence priority

Fix should consume latest applicable:

1. review report
2. verification report
3. diagnosis artifact
4. relevant specification/contract

Do not rely on chat history when persisted evidence exists.

If implementation advanced since evidence was written, first confirm historical findings still apply.

## Expected fix success

The fix command does not return `DONE`.

After repair:

```text
/verify
```

## FIX_BLOCKED routing

Product issue:

```text
/prd
```

Architecture issue:

```text
/architect
```

Project-init mismatch:

```text
/project-init
```

Spec issue:

```text
/spec
```

Repository issue:

```text
/fix
```

after repository correction.

When an upstream stage changes, rerun required downstream stages.

## 20.1 Concrete failure recipe — deterministic implementation defect

Use this recipe when you want to prove the shortest repair loop through review:

```text
/verify
→ NOT_DONE
→ /fix
→ /verify
→ DONE + CLEAR + MATCH
→ /review
```

### Safe fixture

Choose a trivial deterministic function already covered by one smoke-test unit test.

Example intended behavior:

```text
Add(2, 3) = 5
```

Temporarily introduce an obvious defect such as:

```text
return a - b;
```

instead of:

```text
return a + b;
```

Do not modify the test.

### Expected /verify result

Run:

```text
/verify
```

Expected:

```text
Verification Result: NOT_DONE
Delivery Gate: BLOCKED
```

The verification report should identify the failing test and acceptance criterion.

### Expected /fix behavior

Run:

```text
/fix
```

Expected behavior:

- consume the applicable persisted verification report
- confirm the defect still exists
- make the smallest code correction
- do not alter the test merely to obtain green status
- do not redesign architecture
- do not claim `DONE`

Then rerun:

```text
/verify
```

Expected:

```text
Verification Result: DONE
Delivery Gate: CLEAR
Freshness: MATCH
```

Then run:

```text
/review
```

Expected:

- the newly created verification report is selected
- freshness remains `MATCH`
- the review pipeline runs normally
- the review artifact is persisted

The `direct-fix-loop` scenario is complete only after the repaired, freshly verified state re-enters the review pipeline.

### Pass condition

The original failed verification artifact remains unchanged and a new successful verification artifact is created.

---

---

# 21. Phase 14 — /diagnose loop

Use only when root cause is genuinely unclear, intermittent, concurrent, integration-related, performance-related, or otherwise difficult.

Expected flow:

```text
/verify
→ NOT_DONE
→ /diagnose
→ DIAGNOSIS_READY
→ /fix
→ /verify
→ DONE + CLEAR + MATCH
→ /review
```

Diagnosis persists under:

```text
docs/diagnostics/
```

Expected statuses:

```text
DIAGNOSIS_READY
DIAGNOSIS_BLOCKED
```

If blocked because evidence/environment access is missing, obtain only the minimum missing input and rerun `/diagnose`.

Do not invent a complex flaky system solely for smoke testing. This phase may be marked optional if no cheap deterministic diagnostic fixture exists.

## 21.1 Concrete failure recipe — force diagnosis before fixing

The purpose of this recipe is to ensure the workflow distinguishes:

- a known straightforward defect that belongs directly to `/fix`
- an observed failure whose root cause is not yet established and therefore belongs to `/diagnose`

### Recommended low-cost fixture

Create two small functions where the externally observed failure does not reveal which internal assumption is wrong.

Example:

```text
NormalizeAmount("10.50") → 10.50
FormatAmount(10.50)      → "10.50"
```

Introduce a defect in one underlying transformation while the failing test observes only the end-to-end result.

For example, make normalization incorrectly use integer parsing or culture-sensitive parsing, then keep the high-level test expectation unchanged.

The failure should be real and deterministic, but the verification output should not itself establish whether the defect is in parsing, normalization, or formatting.

### Step 1 — verify

Run:

```text
/verify
```

Expected:

```text
Verification Result: NOT_DONE
Delivery Gate: BLOCKED
```

The report should contain the observed failure, not an invented root-cause claim.

### Step 2 — diagnose

Run:

```text
/diagnose
```

Expected behavior:

- read the persisted verification evidence
- reproduce the exact symptom
- narrow the failure to a specific component/assumption
- use the existing spec/tests/contracts to establish intended behavior
- persist diagnostic evidence under `docs/diagnostics/`
- avoid changing production code while root cause is still uncertain

Expected status:

```text
DIAGNOSIS_READY
```

A good diagnosis should say what failed, why it failed, and what evidence proves that conclusion.

### Step 3 — fix

Run:

```text
/fix
```

Expected behavior:

- consume the diagnosis plus applicable verification evidence
- apply the smallest correction
- preserve approved behavior and test strength

### Step 4 — verify again

Run:

```text
/verify
```

Expected:

```text
Verification Result: DONE
Delivery Gate: CLEAR
Freshness: MATCH
```

### Step 5 — review the repaired state

Run:

```text
/review
```

Expected behavior:

- review selects the new applicable verification report
- freshness remains `MATCH`
- pre-review executes normally
- senior review runs only when pre-review returns `READY_FOR_SENIOR_REVIEW`
- the resulting review artifact is persisted

The `diagnose-fix-loop` scenario is complete only after the repaired, freshly verified state successfully re-enters the review pipeline.

### Negative routing check

If the failure is already obvious from verification evidence—for example a unit test clearly shows `Add` subtracts instead of adds—do **not** force `/diagnose`.

Use:

```text
/verify
→ NOT_DONE
→ /fix
→ /verify
```

The smoke test should prove that diagnosis is used because uncertainty exists, not merely because the command exists.

---

---

# 22. Phase 15 — /waive loop

Use only from a real:

```text
Verification Result: NOT_DONE
```

for a policy-allowed bounded risk.

A waiver must never turn verification truth into `DONE`.

## Required human input

Require explicit:

- acceptance
- justification
- residual risk
- compensating controls/evidence
- remediation
- expiry

## Expected status

Valid:

```text
WAIVER_APPROVED
```

Invalid/missing input/non-waivable:

```text
WAIVER_BLOCKED
```

## Effective gate

Valid waiver establishes:

```text
Verification Result: NOT_DONE
Delivery Gate: CLEAR_WITH_EXCEPTION
```

Then:

```text
/review
```

Review receives both:

- failed verification report
- waiver

## Stale-waiver test

Change content or mode/type after waiver.

Attempt review.

Expected:

```text
MISMATCH
```

Waiver must not authorize the changed implementation.

## 22.1 Concrete failure recipe — trivial waivable quality issue

The waiver smoke test must use a failure that is:

- real
- intentionally introduced
- low impact
- explicitly allowed by project policy
- temporary
- easy to remediate
- not security-critical
- not data-integrity-critical
- not destructive
- not an authentication/authorization failure

### Preferred fixture

Use a deliberately configured non-security quality gate that is required by the smoke specification but safe to accept temporarily.

Example:

- require documentation coverage for one public smoke-test method
- intentionally omit that documentation
- verification command returns failure because the required documentation check fails
- application behavior and tests remain correct

Another acceptable fixture is a harmless formatting/lint rule designated by the smoke project as temporarily waivable.

Do **not** use:

- failing unit/integration behavior that means the acceptance criterion is actually wrong
- secret-scanning failures
- authentication or authorization failures
- dependency vulnerabilities
- IaC security failures
- data-loss/integrity failures
- destructive migration failures
- required safety/reliability invariants

Those should not be normalized as routine waiver examples.

### Step 1 — establish NOT_DONE

Run:

```text
/verify
```

Expected:

```text
Verification Result: NOT_DONE
Delivery Gate: BLOCKED
```

The failed report must identify the exact trivial quality check.

### Step 2 — request human waiver

Run:

```text
/waive
```

Provide explicit smoke-test authorization, for example:

```text
Accept this documentation-only smoke-test failure temporarily.

Justification:
This is an intentionally introduced non-runtime documentation gap used only to validate the waiver workflow.

Residual risk:
One smoke-test public API lacks the required documentation.

Compensating control:
Behavioral tests and all runtime/security checks remain passing.

Remediation:
Add the missing documentation immediately after the waiver/review scenario.

Expiry:
End of this smoke-test session.
```

Expected:

```text
WAIVER_APPROVED
```

and:

```text
Verification Result: NOT_DONE
Delivery Gate: CLEAR_WITH_EXCEPTION
```

The verification report itself must remain `NOT_DONE`.

### Step 3 — review with exception

Run:

```text
/review
```

Expected behavior:

- review first validates Contract-v1 freshness
- review receives the failed verification evidence
- review receives the active waiver verbatim
- reviewers may still reject the change if the waiver is unsafe or misclassified
- if otherwise acceptable, the review may proceed under `CLEAR_WITH_EXCEPTION`

### Step 4 — prove waiver staleness

Before remediation, change one identity-bearing source/test/configuration file.

Run:

```text
/review
```

Expected:

```text
MISMATCH
```

The old waiver must not authorize the new implementation state.

### Step 5 — remediate instead of carrying the waiver forever

Restore the verified implementation state as needed, then actually fix the trivial quality issue.

Run:

```text
/verify
```

Expected:

```text
Verification Result: DONE
Delivery Gate: CLEAR
```

The historical waiver and historical `NOT_DONE` report remain preserved as evidence.

---

## 22.2 Full recovery-flow matrix

Use these deliberately injected scenarios to validate the intended routing:

| Injected condition | First result | Correct next path |
| --- | --- | --- |
| Obvious deterministic code defect | `NOT_DONE` | `/fix → /verify` |
| Failure observed but root cause genuinely unclear | `NOT_DONE` | `/diagnose → /fix → /verify` |
| Trivial policy-allowed temporary quality failure | `NOT_DONE` | `/waive → CLEAR_WITH_EXCEPTION → /review` |
| Non-waivable security/integrity failure | `NOT_DONE` | repair via `/fix` or upstream authority; waiver must be blocked |
| Review finds blocking implementation issue | `CHANGES_REQUIRED` or `REQUEST CHANGES` | `/fix → /verify → /review` |
| Evidence becomes stale after any repair/change | stale/`MISMATCH` | fresh `/verify` before review |

The smoke test passes only if the workflow chooses the path that matches the nature of the failure rather than mechanically invoking every recovery command.

---

---

# 23. Phase 16 — malformed evidence test

Use copied disposable evidence.

Create one case where freshness cannot be reliably proven:

- missing required field
- unavailable base HEAD
- malformed canonical manifest
- mode/type ambiguity
- other reconstruction failure

Expected:

```text
UNRECONSTRUCTABLE
```

Then:

```text
/verify
```

No reviewer should run.

Do not infer freshness from:

- HEAD equality
- fingerprint equality alone
- chat history
- newer unrelated reports

---

# 24. Phase 17 — evidence exclusion test

Excluded paths:

```text
docs/verification/**
docs/reviews/**
docs/diagnostics/**
```

Add/change only evidence there.

Expected implementation freshness:

```text
MATCH
```

Then change one identity-bearing path such as:

```text
docs/specs/**
docs/architecture/**
docs/adr/**
AGENTS.md
.kilo/**
source/tests
build/package configuration
lockfiles
CI/IaC
```

Expected:

```text
MISMATCH
```

---

# 25. Phase 18 — /adversarial-check

Use for a bounded high-risk architecture/spec decision.

Default adversary:

```text
DeepSeek
```

The orchestrator should extract:

- smallest artifact
- contract/invariants
- relevant risk

The adversary challenges rather than re-authors.

## No-material finding

Continue the owning workflow.

## Material finding

Owning model reconciles.

When planning-worker is used:

```text
MODE: RECONCILE_ONLY
```

Do not rerun full `AUTHOR`.

One additional default adversarial pass is allowed only if reconciliation materially changes the challenged decision.

Do not automatically cycle indefinitely.

---

# 26. Phase 19 — Restart from an arbitrary middle stage

This phase specifically validates that the workflow can be followed without prior conversational baggage.

Create separate restart scenarios.

## Scenario A — approved architecture already exists

Start a fresh chat/session.

Provide only repository access.

Expected behavior:

- agent discovers existing PRD/architecture
- does not rerun `/grill` or `/prd`
- starts at `/project-init` if initialization is incomplete

## Scenario B — project-init already ready

Fresh session.

Expected:

- discovers project baseline and artifacts
- starts at `/spec`

## Scenario C — approved spec exists

Fresh session.

Expected:

- identifies relevant spec
- starts at `/implement`

## Scenario D — implementation exists, no verification

Fresh session.

Expected:

- starts at `/verify`

## Scenario E — valid fresh verification exists

Fresh session.

Expected:

- starts at `/review`

## Scenario F — stale verification exists

Fresh session.

Expected:

- detects stale state
- requires `/verify`
- does not trust prior chat

## Scenario G — review blocker exists

Fresh session.

Expected:

- `/fix` consumes persisted review evidence
- no need to reproduce reviewer conversation

## Pass condition

Persisted repository artifacts are sufficient to determine the correct continuation point.

Chat memory must not be required.

---

# 27. Phase 20 — upstream-change rerouting tests

Validate that blocked workflows route to authority rather than inventing decisions.

## Architecture discovers product ambiguity

Expected:

```text
ARCHITECTURE_BLOCKED
→ /prd
```

## Spec discovers architecture ambiguity

Expected:

```text
SPEC_BLOCKED
→ /architect
```

## Implementation requires unapproved architecture change

Expected:

```text
IMPLEMENTATION_BLOCKED
→ /architect
```

## Fix reveals requirement contradiction

Expected:

```text
FIX_BLOCKED
→ /prd
```

## Fix reveals architecture defect

Expected:

```text
FIX_BLOCKED
→ /architect
```

After upstream correction, explicitly regenerate invalidated downstream artifacts.

---

# 28. Phase 21 — Review persistence/cost gate

Create a genuine pre-review blocker.

Run:

```text
/review
```

Expected:

```text
CHANGES_REQUIRED
Senior Review: NOT_RUN
```

Persist review report.

GPT-5.6 Sol senior reviewer must not run.

After:

```text
/fix
→ /verify
→ /review
```

senior review may run only if pre-review returns:

```text
READY_FOR_SENIOR_REVIEW
```

---

# 29. Phase 22 — Static Claude routing

Do not invoke Claude.

Confirm:

- Sonnet route exists
- Opus route exists
- user-directed invocation can select them
- agent-proposed paid escalation requires approval
- normal smoke path does not require them

Record:

```text
CLAUDE_RUNTIME_TEST: NOT_RUN_BY_POLICY
```

---

# 30. Required Smoke-Test Report

The authoritative smoke-run report is the run-state record itself:

```text
docs/verification/smoke/<run-id>.md
```

Do not create a second top-level `docs/verification/SMOKE-*.md` report containing duplicate run state.

The run-state record is both:

- the restart/resume authority for `/smoke`
- the final scenario/cost/outcome report when the run completes

Include:

## Release identity

- tag/SHA
- project baseline SHA
- tool versions
- OS

## Entry point used

Record where the run began:

```text
START_STAGE:
WHY:
EXISTING_ARTIFACTS_REUSED:
ARTIFACTS_DECLARED_STALE:
```

This is required because the workflow may start from any valid stage.

## Model usage

For each invocation:

- workflow
- model
- purpose
- approximate observed cost/usage when available

## Scenario table

| Scenario | Starting state | Command | Expected | Actual | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |

## Cost summary

Record:

- DeepSeek usage/cost
- OpenAI calls
- Claude calls
- Claude spend

## Defect classification

Use:

- `FRAMEWORK_DEFECT`
- `TEST_FIXTURE_DEFECT`
- `ENVIRONMENT_LIMITATION`
- `MODEL_VARIANCE`
- `DOCUMENTATION_DEFECT`

---

# 31. Stable-v0.1 Required Acceptance Criteria

Required:

1. `/grill` can be used when needed and skipped when not needed
2. discovery blockers do not force settled questions to be repeated
3. PRD routes unresolved product decisions correctly
4. architecture preserves operating-cost requirements
5. architecture routes product blockers back to PRD
6. project-init synchronizes repository instructions and evidence contract
7. spec routes blockers to the correct authority
8. implementation can proceed on an approved dedicated spec branch
9. first-spec implementation can remain fully uncommitted
10. uncommitted implementation verifies successfully
11. review works before implementation commit
12. later identical commit preserves `MATCH`
13. content change produces `MISMATCH`
14. mode/type change produces `MISMATCH` or valid `UNRECONSTRUCTABLE`
15. verification-time mutation blocks delivery
16. `NOT_DONE → /fix → /verify` works
17. diagnosis path persists evidence when used
18. waiver preserves `NOT_DONE`
19. valid waiver establishes only `CLEAR_WITH_EXCEPTION`
20. stale waiver cannot authorize changed state
21. malformed evidence fails closed
22. evidence-path exclusions behave correctly
23. adversarial reconciliation uses `RECONCILE_ONLY`
24. pre-review blocker skips senior review
25. restart from arbitrary middle stages works using repository artifacts alone
26. upstream changes force correct downstream regeneration
27. no mandatory Claude runtime invocation occurs
28. prior chat history is not required to resume the workflow

---

# 32. Optional Acceptance Criteria

Optional when creating the fixture would add disproportionate cost:

- realistic intermittent-failure diagnosis scenario
- actual paid Claude invocation
- platform-specific symlink/gitlink mode transition where unsupported locally

Optional scenarios must be marked explicitly and must not silently appear as passes.

---

# 33. Release Validation Outcome

Use one final status.

## SMOKE_PASS

All required acceptance criteria passed.

## SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION

All workflow semantics passed, but a platform-specific mode/type scenario could not be represented and correctly failed closed.

## SMOKE_FAIL

One or more required workflow semantics failed.

If failed:

1. preserve evidence,
2. do not silently modify the tagged release,
3. fix on a branch,
4. run review/verification,
5. publish a later version such as:

```text
stable_v_0.1.1
```

---

# 34. Quick Operational Continuation Guide

When returning to a project after days/weeks, use this sequence:

```text
1. Inspect persisted artifacts.
2. Identify latest authoritative upstream state.
3. Determine whether downstream artifacts remain valid.
4. Identify latest applicable verification/review/diagnosis evidence.
5. Inspect branch + working tree.
6. Choose the earliest incomplete/stale stage.
7. Run only that stage and required downstream stages.
```

Examples:

```text
PRD ready, no architecture
→ /architect

Architecture ready, project rules missing
→ /project-init

Everything planned, spec exists
→ /implement

Code exists, no current evidence
→ /verify

DONE + CLEAR + MATCH
→ /review

NOT_DONE + known bug
→ /fix

NOT_DONE + uncertain root cause
→ /diagnose

NOT_DONE + explicitly accepted bounded risk
→ /waive

Review blocker
→ /fix → /verify → /review

Product requirement changed
→ /prd → regenerate affected downstream artifacts

Architecture changed
→ /project-init → /spec → implementation/fix → /verify → /review
```

---

# 35. Intended Stable-v0.1 Guarantee

The smoke test should demonstrate that the workflow can be entered and resumed from the correct stage based on persisted repository state, without relying on conversational history and without unnecessarily repeating earlier model-expensive stages.

The core guarantee is:

> The workflow preserves authority boundaries, reuses valid prior artifacts, invalidates downstream work when upstream authority changes, and ensures that the exact repository state that was deterministically verified is the state being reviewed—even when implementation was never committed before verification.
