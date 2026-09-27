---
description: Orchestrate restartable FAST or FULL workflow smoke testing using approved disposable fixture projects
agent: smoke-orchestrator
model: openai/gpt-5.6-luna
---

# Smoke-Test Orchestrator

Run or resume a controlled workflow smoke test.

Supported invocation forms:

```text
/smoke FAST
/smoke FULL
/smoke FAST <fixture-id>
/smoke FULL <fixture-id>
/smoke RESUME <run-id>
/smoke STATUS <run-id>
/smoke ABANDON <run-id>
```

Canonical profile names are:

- `FAST`
- `FULL`

Treat user phrases `FAST_SMOKE` and `FULL_SMOKE` as aliases when they occur inside the `/smoke` invocation.

Do not treat free-form text outside this command as an executable smoke run.

## Stage 1 — Load smoke contracts

Read:

- installed global `smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md`
- installed global `smoke/fixtures.json`
- installed global `smoke/profiles.json`
- installed global `smoke/failure-recipes.json`
- global `AGENTS.md`
- global `.subhforge-install.json` when present; use it as installed-release provenance
- the minimum command/agent files needed for the next smoke stage from the plural `commands/` and `agents/` directories

The runbook is the smoke-test policy.

The normal workflow command files remain authoritative for each underlying lifecycle stage.

## Stage 2 — Select profile

If profile is neither `FAST` nor `FULL`, stop with:

`SMOKE_PROFILE_REQUIRED`

Show:

```text
FAST
FULL
```

and one-line guidance from the runbook.

## Stage 3 — Select fixture project

Filter the fixture registry to entries supporting the selected profile.

If the user supplied `DEFAULT`:

- resolve the single registry entry whose `default_for` contains the selected profile
- require exactly one default
- if no unique default exists, return `SMOKE_FIXTURE_INVALID`

If the user supplied a fixture ID other than `DEFAULT`:

- require an exact registry match
- require that fixture supports the selected profile
- otherwise return `SMOKE_FIXTURE_INVALID`

If the user did not supply a fixture ID:

1. display the compatible fixture list
2. mark the registry default
3. ask the user to choose one, or explicitly choose `DEFAULT`
4. return `SMOKE_FIXTURE_REQUIRED`

Do not invent an unregistered fixture during an automated smoke run.

### Fixture runtime constraints

When a fixture declares a `runtime` constraint, that constraint is authoritative for the smoke run.

- planning and architecture may choose implementation details only within that runtime
- they must not substitute another language/runtime
- validate generated architecture/ADR/spec artifacts against the fixture runtime before project initialization or implementation
- if an artifact selects a conflicting runtime, treat it as a planning defect and reconcile it before proceeding
- do not probe the machine for unrelated runtimes as a fallback


Examples:

```text
/smoke FAST DEFAULT
/smoke FULL full-minimal-api
```

### Installed release identity

The global Kilo config is an installed file tree, not necessarily a Git checkout. Do not run `git rev-parse` or `git tag` inside the global config directory merely to discover release identity.

When `.subhforge-install.json` exists, use its source repository, source commit, source branch and source tag fields as installation provenance.

During pre-release validation, `source_tag` may be `UNTAGGED_RELEASE_CANDIDATE`. Record the exact source commit and continue. The stable tag is created only after required smoke validation passes.

If the provenance manifest is missing `source_checkout_path` or `source_commit`, or the recorded checkout/commit cannot be resolved, stop with `SMOKE_BLOCKED` and request reinstall from the exact SubhForge checkout under test.

## Stage 4 — Prepare disposable project safely

Use the selected registry fixture, its `source_template`, and its product brief.

Smoke fixtures are internal SubhForge release assets. The user must never be
required to navigate to, clean, or maintain a separate fixture repository.

Require `.subhforge-install.json` to contain the exact installed
`source_checkout_path` and `source_commit`. For every new run, use the
deterministic installed helper:

```text
python <global-config>/scripts/smoke_workspace.py create --source <source_checkout_path> --source-commit <source_commit> --profile <FAST|FULL> --fixture <fixture-id>
```

The helper is the only supported mechanism for provisioning and allocating a
new smoke workspace.

It must:

- materialize `template/` from the exact recorded SubhForge commit
- create an internal temporary baseline Git repository automatically
- generate a globally unique run ID using UTC timestamp plus random suffix
- create a physically separate local clone under a sibling `SubhForge-smoke-runs/<run-id>/` directory
- delete temporary provisioning repositories before returning
- create exactly one fixed local branch named `smoke-run` inside the run clone
- return machine-readable JSON containing run ID, run directory, generated baseline HEAD, source commit, profile, fixture, and branch
- never require or mutate `production-ai-project` or another user-maintained fixture repository
- never require the SubhForge checkout working tree to be clean; provisioning comes from the recorded commit

Do not:

- allocate run IDs by scanning Git branches
- allocate run IDs by scanning old smoke records
- use sequential `001/002` numbering for new runs
- invent branch names from the run ID
- run smoke mutations in the baseline project repository
- create a new smoke workspace manually with ad hoc Git commands

If the helper fails, return:

`SMOKE_BLOCKED`

with the exact helper error.

## Stage 5 — Allocate, persist, resume, or inspect smoke state

Smoke progress has two persisted representations in the target disposable project:

```text
docs/verification/smoke/<run-id>.state.json
docs/verification/smoke/<run-id>.md
```

The JSON state is the canonical machine-readable orchestration state.
The Markdown record is the human-readable execution/evidence projection.

Both locations are inside the Contract-v1 evidence exclusion set.

Do not update orchestration state by matching and replacing large prose blocks
inside the Markdown record. Use `scripts/smoke_state.py set` for targeted
machine-state changes, then update the Markdown summary from that state when a
human-readable transition record is required.

### New-run allocation

The `/smoke` orchestrator never invents or sequences run IDs itself.

For a new run:

1. call the deterministic smoke workspace helper from Stage 4
2. require `ok: true`
3. use the returned `run_id` exactly as supplied
4. switch all subsequent repository operations to the returned `run_directory`
5. before any substantive smoke stage or child-model invocation, create:
   `docs/verification/smoke/<run-id>.md`
   inside that run directory
6. immediately execute the deterministic smoke bootstrap exactly once:

   ```text
   python <global-config>/scripts/smoke_bootstrap.py \
     --repo <run-directory> \
     --run-id <run-id> \
     --profile <FAST|FULL> \
     --fixture <fixture-id> \
     --source-commit <source_commit> \
     --baseline-head <baseline_head> \
     --required-contract <global-config>/contracts/implementation-state-evidence-v1.md \
     --required-contract <run-directory>/docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md \
     --optional-contract <run-directory>/kilo/contracts/implementation-state-evidence-v1.md
   ```

   This single helper is authoritative for:
   - path-aware Contract-v1 parity
   - canonical `<run-id>.state.json` initialization
   - elapsed-time budget initialization
   - persistence of parity/budget bootstrap evidence into canonical state

7. require bootstrap `ok: true`, require both `<run-id>.state.json` and
   `<run-id>.budget.json` to exist, and require canonical state to identify
   the same run/profile/fixture/source commit/baseline before launching any
   planning or execution model
8. never replace bootstrap with ad-hoc PowerShell/Python equality checks,
   manual state creation, or a separate budget-start sequence
9. never reuse an existing run directory or run ID

Canonical run IDs are collision-resistant identifiers such as:

```text
SMOKE-FAST-fast-micro-library-20260926T201500Z-a1b2c3d4
```

Run IDs are identifiers, not chronology authority. The run record's explicit timestamps and repository evidence remain authoritative.

If the run record cannot be created safely, stop with:

`SMOKE_BLOCKED`

Do not continue with an unpersisted anonymous run.

### Required smoke-run record

A smoke-run record must contain:

- run ID
- profile
- fixture ID
- source template and exact SubhForge source commit
- release/tag and exact configuration SHA
- target project branch/worktree
- baseline HEAD
- started-at timestamp
- last-updated timestamp
- current stage
- current scenario
- total required scenario count loaded from `smoke/profiles.json`
- completed scenario count derived from persisted completed required scenario IDs
- completed scenarios
- pending scenarios
- skipped scenarios with reason
- current authoritative artifact paths
- one compact context index (release SHA, baseline HEAD, fixture, current spec,
  verification base/report, review/waiver paths, and checkpoint labels)
- current applicable verification/review/diagnosis/waiver evidence
- latest verification result, delivery gate, and freshness when available
- latest review result when available
- checkpoint notes
- model invocation ledger by model/workflow
- observed token/cost usage when available
- Claude invocation count and spend when available
- blockers / required user action
- defects
- final result

Do not rely on prior chat history to resume.

### New-run acknowledgement

Immediately after allocating the ID, report at minimum:

```text
Run ID: <run-id>
Profile: <FAST|FULL>
Fixture: <fixture-id>
Release: <tag>@<configuration-sha>
Current Stage: <stage>
Progress: <completed>/<required>
Claude Calls: 0
Next: <next stage/scenario>
```

Every later `/smoke` response for this run must repeat:

```text
Run ID: <run-id>
```

near the top.

### RESUME

For:

```text
/smoke RESUME <run-id>
```

reconstruct state from the exact run record and current repository evidence.

Before continuing:

- validate profile and fixture from the run record
- locate the run workspace using `python <global-config>/scripts/smoke_workspace.py locate --source <source_checkout_path> --run-id <run-id>` and validate the returned run directory/branch
- identify completed, pending, blocked, and invalidated scenarios
- re-evaluate whether the recorded next stage is still correct
- never trust chat history over repository state

Read the canonical JSON smoke state first. Use its persisted context index to
open exact paths. Validate the relevant artifact and repository identity before
reuse; do not repeatedly glob the repository or reread unchanged planning
documents for each scenario. Refresh the index when an upstream authority or
implementation identity changes.

Then continue from the earliest required incomplete/invalidated stage.

### STATUS

For:

```text
/smoke STATUS <run-id>
```

perform a read-only status operation.

Do not:

- mutate repository files
- inject failures
- execute lifecycle stages
- invoke child/subagent models
- alter the run record

Read the run record plus only the minimum repository evidence needed to detect obvious drift.

Return this fixed status shape:

```text
Smoke Run Status

Run ID: <run-id>
State: <IN_PROGRESS|WAITING_FOR_USER|BLOCKED|PASS|PASS_WITH_ENVIRONMENT_LIMITATION|FAIL>
Profile: <FAST|FULL>
Fixture: <fixture-id>
Release: <tag>@<configuration-sha>
Target: <isolated-run-directory>
Baseline HEAD: <sha>

Current Stage: <workflow-stage>
Current Scenario: <scenario-id-or-name>
Progress: <completed>/<required> required scenarios
Skipped: <count> (only policy-approved/optional scenarios)

Latest Verification:
- Result: <DONE|NOT_DONE|N/A>
- Delivery Gate: <CLEAR|BLOCKED|CLEAR_WITH_EXCEPTION|N/A>
- Freshness: <MATCH|MISMATCH|UNRECONSTRUCTABLE|N/A>

Latest Review: <APPROVE|REQUEST CHANGES|CHANGES_REQUIRED|NOT_RUN|N/A>

Model Ledger:
- GPT-5.6 Sol: <count>
- GPT-5.6 Luna: <count>
- DeepSeek Flash: <count>
- Claude: <count>

Observed Cost:
- DeepSeek: <value-or-UNAVAILABLE>
- Claude: <value-or-0/UNAVAILABLE>
- Other: <value-or-UNAVAILABLE>

Blocker / User Action: <none-or-exact-action>
Next: <next required stage/scenario-or-COMPLETE>
Last Updated: <timestamp>
```

If repository evidence shows that the recorded state has drifted, append:

```text
Drift Detected: YES
Required Action: /smoke RESUME <run-id>
```

Do not silently repair drift during `STATUS`.

### ABANDON

For:

```text
/smoke ABANDON <run-id>
```

perform a terminal cleanup of a failed, blocked, or intentionally discontinued smoke run.

Before destroying the workspace:

1. locate the run using the deterministic smoke workspace helper
2. read the run record and current diagnostic/failure evidence
3. update the run record to terminal state `ABANDONED`
4. persist the final blocker/defect/diagnostic summary and last-updated timestamp
5. export/copy the final smoke run record and any evidence required for long-term retention outside the disposable workspace
6. invoke:
   `python <global-config>/scripts/smoke_workspace.py destroy --source <source_checkout_path> --run-id <run-id>`
7. confirm the run directory no longer exists

Do not use `ABANDON` for a run that should be resumed.

If evidence cannot be preserved safely, return `SMOKE_BLOCKED` and do not destroy the workspace.

### Missing/unusable run record

If a supplied run ID does not exist, is malformed, or cannot be reconstructed safely, return:

`SMOKE_RUN_UNRECONSTRUCTABLE`

## Stage 6 — Determine the correct entry point

Inspect persisted repository artifacts first.

Use the runbook's Start/Resume Decision Table and Artifact Invalidation Rules.

Do not blindly start from `/grill`.

For a brand-new FULL run, normally begin at `/grill`.

For a brand-new FAST run, prefer the earliest stage required by the FAST profile and selected fixture. Reuse valid planning artifacts from the template/project when available.

When prior valid artifacts exist:

- reuse them
- record them in the smoke-run file
- do not regenerate them merely to spend a model call

For FULL, establish one canonical verified implementation checkpoint after the
first successful uncommitted `/verify`. Fan out independent freshness, mode,
evidence, waiver-staleness, and review-blocker probes from that checkpoint
where their prerequisites fit. Record each probe's checkpoint, evidence path,
mutation ID, and outcome. Restore only disposable smoke mutations with an
exact checkpoint comparison; if the state drifts, stop and diagnose. A probe
must not overwrite historical verification/review evidence. Repair loops still
execute the real `/fix`, `/diagnose`, `/verify`, and `/review` contracts when
their scenario requires them.

When upstream authority changed:

- mark invalidated downstream artifacts
- resume from the earliest invalidated authority stage

## Stage 7 — Execute underlying workflows with preserved model routing

The smoke orchestrator coordinates; it does not replace stage ownership.

### Planning stages

For:

- `/grill`
- `/prd`
- `/architect`
- `/spec`

delegate to `planning-worker` with the workflow's normal model, an explicit
execution mode, and a compact context packet containing the exact authoritative
paths needed by that stage.

The packet MUST enumerate exact paths under a `CONTEXT_PATHS` section. When a
required path is supplied and validates successfully, repository globbing to
rediscover that same artifact or directory is prohibited. If a supplied path is
missing, stale, ambiguous, or insufficient, the child may perform bounded
discovery only for that unresolved item and must report why discovery was
needed.

The child must not rediscover supplied paths unless one is missing, stale,
ambiguous, or points to unresolved authority:

- `AUTHOR`
- `CONTINUE`
- `RECONCILE_ONLY`

For the default Stable-v0.1 smoke path, use GPT-5.6 Sol for these planning stages.

The predefined smoke fixture product brief is required to be sufficient for
planning. Do not turn a framework smoke run into an interactive product
discovery session.

If a planning child returns `USER_INPUT_REQUIRED` because product behavior,
runtime, scope, or acceptance criteria are missing:

- persist the exact missing information
- mark the run `SMOKE_BLOCKED`
- classify it as `SMOKE_FIXTURE_UNDERSPECIFIED`
- do not ask the user to invent product requirements for the smoke fixture

Human input remains allowed only for an explicit human-controlled workflow gate
that the FULL profile intentionally tests, such as bounded waiver acceptance.

### Project initialization

Before invoking Luna-owned `/project-init`, execute the deterministic mechanical
setup helper once:

```text
python <global-config>/scripts/project_init_mechanics.py --repo <run-directory> --contract <global-config>/contracts/implementation-state-evidence-v1.md
```

Persist its result in canonical smoke state. Then execute only the remaining
judgment-bearing `/project-init` contract using GPT-5.6 Luna with an exact
context packet containing PRD, architecture, ADR, AGENTS, README, and helper
result paths. Do not repeat directory creation, contract synchronization, or
broad repository discovery already proven by the helper.

### DeepSeek execution stages

Delegate to `smoke-executor` for exactly one of:

- `/implement`
- `/verify`
- `/fix`
- `/diagnose`

The executor must read and obey the corresponding command contract.

For each execution stage, supply a compact `CONTEXT_PATHS` packet from
canonical smoke state containing only the exact paths/identity needed by that
workflow. Valid supplied paths MUST be consumed directly. Globbing to
rediscover a supplied Spec, Architecture, ADR, AGENTS, verification report,
manifest, source, test, or fixture path is prohibited. Bounded discovery is
allowed only for an explicitly missing/stale/ambiguous dependency and the
executor must state that reason in its handoff.

### Waiver

Execute the `/waive` contract using GPT-5.6 Luna.

Human risk acceptance can never be fabricated by the smoke orchestrator.

If explicit authorization is required:

- persist state
- return `SMOKE_USER_INPUT_REQUIRED`
- resume only after the user supplies/approves the required waiver details

### Review

Apply the normal `/review` contract.

Freshness must be validated before any reviewer invocation.

Use:

1. DeepSeek `pre-reviewer`
2. GPT-5.6 Sol `code-reviewer` only when pre-review returns `READY_FOR_SENIOR_REVIEW`

Negative freshness scenarios must invoke **zero reviewer models**.

### Adversarial review

Use the default DeepSeek `adversary`.

When material findings require planning correction:

- reconcile through `planning-worker`
- use `MODE: RECONCILE_ONLY`
- do not restart AUTHOR

Do not use Claude during smoke testing unless the user explicitly authorizes that isolated paid invocation.

## Stage 8 — Profile scenario selection

Load the selected profile definition from installed global `smoke/profiles.json`.

The profile registry is authoritative for:

- required scenario IDs
- optional scenario IDs
- denominator used by `Progress: <completed>/<required>`

Do not invent, renumber, or infer the required scenario count from prose.

Mark a required scenario complete only when its acceptance condition has actually been evidenced and persisted in the run record.

If a required scenario is skipped because of an allowed environment limitation, record it separately and use the profile's environment-limitation completion semantics; do not count it as silently completed.

### FAST

Run only the FAST_SMOKE scenarios defined by the runbook.

Default intent:

- static release/config checks
- project-init contract propagation when applicable
- first-spec uncommitted verification
- review-before-commit
- identical commit freshness
- content-mutation stale-evidence gate
- one direct `/fix → /verify` loop
- one fail-closed evidence scenario
- static model-routing checks

Skip diagnosis, waiver, adversarial runtime, repeated senior review, persistence-heavy integration, and paid Claude unless the changed framework area specifically requires them.

### FULL

Run the FULL_SMOKE scenarios defined by the runbook.

Start from the correct current stage and exercise all required acceptance criteria, including:

- full lifecycle authority
- fix
- diagnosis
- waiver
- review
- adversarial reconciliation
- arbitrary-stage resume
- upstream invalidation routing



## Arbitrary-stage resume smoke optimization

The FULL `arbitrary-stage-resume` scenario validates routing from persisted
repository state, not seven repeated downstream lifecycle executions.

For its seven subcases:

- six are routing-only
- Scenario C (approved Spec exists) is routing + real `/implement` handoff
- the harness may retain the expected stage for scoring, but MUST NOT expose it
  to the routing child in prompts, checkpoint labels, artifact names, or context
- each probe starts from a deterministic known persisted state with no prior
  conversational answers
- the routing child must inspect normal persisted repository evidence and
  produce the next stage itself
- routing-only probes stop immediately after persisting the chosen stage and
  concise reason
- Scenario C crosses into the normal `/implement` owner only far enough to
  prove persisted Spec/context handoff correctness; it does not replay the
  entire implementation/verify/review lifecycle
- normal non-smoke resume semantics are unchanged: real project resumes continue
  executing the selected lifecycle stage normally

Do not replace the routing decision with a deterministic lookup table. Helpers
may prepare/verify checkpoint state and freshness, but the workflow reasoning
under test must choose the continuation stage.



## Post-first-review FULL execution contract

After `review-before-commit` succeeds, execute the remaining FULL scenarios
according to the authoritative matrix in
`smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md §3.5`.

For each remaining scenario, that matrix is authoritative for:

- execution class: deterministic, single-owner, or bounded multi-agent
- required starting checkpoint/state
- permitted substantive model invocations
- whether reviewers are permitted
- restoration/completion behavior
- exact-context expectations for recovery loops

Do not silently add model calls beyond the listed sequence. Do not serialize
independent deterministic probes through one another's mutated state. Verify
and restore the declared checkpoint between independent probes.

Negative freshness/evidence scenarios MUST terminate before pre-review or
senior-review invocation.

Recovery loops MUST use canonical `CONTEXT_PATHS` packets with exact Spec,
failure evidence, source/test paths, diagnosis/review evidence where applicable,
and mutation/checkpoint identity. Broad rediscovery is a defect when those
inputs are valid.

If the execution matrix cannot be followed because required checkpoint/context
evidence is missing or drifted, return `SMOKE_BLOCKED` and persist the exact
gap rather than expanding the workflow ad hoc.

## Stage 9 — Fixture budget enforcement

Treat the selected fixture's test budget as the default maximum application-test surface.

Do not add broad integration/E2E/load/soak suites merely for smoke realism.

If an underlying approved spec genuinely requires a check outside the fixture budget:

- the real workflow contract wins
- record why the budget was exceeded

Never mark a genuinely applicable required check `NOT_APPLICABLE` merely to save tokens.

## Stage 10 — Failure injection

Use only the failure recipes permitted by the selected fixture registry entry.

The Luna smoke orchestrator must not directly author implementation defects.

Delegate the selection of a safe fixture-specific anchor and the required
workflow route to `smoke-executor` using:

```text
ACTION: INJECT_FAILURE
RECIPE: <registered-recipe-id>
```

Before injection:

- persist the clean checkpoint/state
- state the expected workflow route
- require the recipe ID to be listed in the selected fixture
- load that exact recipe definition from installed global `smoke/failure-recipes.json`
- require a unique matching recipe definition
- change only what is necessary for that scenario

For an exact single-file text change, use the installed
`scripts/smoke_mechanics.py` helper after recording a checkpoint. Give it the
registered recipe ID, repository-relative file path, exact old and new UTF-8
text, and a unique mutation ID. It requires an exact single anchor, rejects
evidence/Git paths, and records hashes in the excluded smoke ledger. The
executor must still establish the intended failure through `/verify` or the
appropriate gate; the helper's successful mutation is not a verification
result. For scenarios the helper cannot represent (such as a Git mode change
or verification-time mutation), use a bounded deterministic command and record
its exact before/after identity. Restore a helper mutation only when that
scenario is finished and a real `/fix` is not the required route.

Example (arguments abbreviated; quote text for the active shell):

```text
python <global-config>/scripts/smoke_mechanics.py --repo <run-directory> --run-id <run-id> checkpoint --label verified-clean
python <global-config>/scripts/smoke_mechanics.py --repo <run-directory> --run-id <run-id> mutate --mutation-id freshness-1 --checkpoint verified-clean --recipe content-freshness-mismatch --path app.py --old <exact-old> --new <exact-new>
python <global-config>/scripts/smoke_mechanics.py --repo <run-directory> --run-id <run-id> restore --mutation-id freshness-1
python <global-config>/scripts/smoke_mechanics.py --repo <run-directory> --run-id <run-id> check-checkpoint --label verified-clean
```

`manifest --base <verification-base-HEAD>` produces a Contract-v1 canonical
manifest and fingerprint for deterministic freshness preflight. Compare the
full manifest bytes with the persisted verification manifest; fingerprint
equality alone does not establish `MATCH`. A missing/malformed report,
unsupported file type, or uncertain Git state fails closed. The authoritative
`/verify` report and `/review` gate remain responsible for their verdicts.

Never use a security, auth, data-integrity, destructive, or vulnerability failure as the trivial waiver recipe.

After each scenario:

- restore/remediate through the workflow path being tested
- obtain fresh verification whenever implementation identity changed

## Stage 11 — Cost controls

Enforce the runbook's token/cost rules:

- one fixture per run
- minimal tests
- static checks instead of model calls where sufficient
- no regeneration of valid artifacts
- zero reviewer calls after freshness failure
- normally one successful senior review
- one bounded default adversarial challenge
- stop after two materially identical failed attempts
- Claude invocation count target: zero

For the tiny FULL fixture, target 25 minutes and enforce a 30-minute hard
orchestration ceiling with the installed executable guard.

Before EVERY substantive lifecycle/model stage, and immediately after EVERY
child/subagent returns, run:

```text
python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> check --limit-minutes 30
```

If the guard returns exit code 3 / `PERFORMANCE_BUDGET_EXCEEDED`:

- do not launch another lifecycle/model stage
- persist elapsed time, current stage, ledger, and blocker
- return `SMOKE_BLOCKED` with `PERFORMANCE_BUDGET_EXCEEDED`
- keep the workspace for diagnosis/resume
- do not call this a functional `SMOKE_FAIL`

The orchestration guard is a boundary stop: it prevents any new stage after the
budget is exceeded and catches over-budget child calls immediately on return.
It cannot forcibly terminate a child model invocation already in progress.
Do not claim otherwise.

Record every substantive model invocation in the run ledger.

## Stage 12 — Persist after every meaningful transition

Update canonical smoke state after:

- stage completion
- blocker
- user-input request
- failure injection
- verification result
- review result
- fix/diagnosis result
- waiver result
- checkpoint/restoration
- defect classification

Use `scripts/smoke_state.py set` with narrowly scoped JSON field updates.
Do not patch long expected prose blocks in the Markdown record.

After the machine-state update succeeds, update the human-readable Markdown
record only with the concise transition/evidence summary needed for audit.

This makes the smoke run restartable without chat history while avoiding
formatting-drift failures.

## Stage 12.5 — Workspace retention and cleanup

The disposable run clone is temporary execution state, not long-term evidence.

Retention policy:

- while a run is `IN_PROGRESS`, `WAITING_FOR_USER`, or `BLOCKED`: keep the workspace so `RESUME` and diagnosis remain possible
- on `SMOKE_FAIL`: keep the workspace by default for diagnosis; destroy it only after the failure has been captured and the user explicitly abandons or archives the run
- on `FAST_SMOKE_PASS`, `FAST_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION`, `FULL_SMOKE_PASS`, or `FULL_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION`: persist/export the final smoke run record and any required evidence first, then destroy the disposable workspace using:

```text
python <global-config>/scripts/smoke_workspace.py destroy --source <source_checkout_path> --run-id <run-id>
```

Cleanup must never delete the baseline repository.

If automatic cleanup fails after a successful smoke result:

- keep the PASS result
- record `WORKSPACE_CLEANUP_FAILED`
- report the exact run directory requiring manual cleanup

## Stage 13 — Completion

For FAST, finish with exactly one of:

- `FAST_SMOKE_PASS`
- `FAST_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION`
- `SMOKE_FAIL`

For FULL, finish with exactly one of:

- `FULL_SMOKE_PASS`
- `FULL_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION`
- `SMOKE_FAIL`

When paused rather than complete, use only:

- `SMOKE_FIXTURE_REQUIRED`
- `SMOKE_USER_INPUT_REQUIRED`
- `SMOKE_BLOCKED`
- `SMOKE_RUN_UNRECONSTRUCTABLE`

Never report PASS merely because only a subset of required scenarios executed.

## Output discipline

During execution, keep chat output concise.

Persist detailed evidence in the smoke-run record and normal workflow artifacts.

In chat report only:

- run ID, repeated near the top on every response
- profile + fixture
- stage/scenario just completed
- progress count
- PASS/FAIL/BLOCKED
- next stage
- material model/cost note
- required user action, if any
- final status token

Never make the user search prior chat history to discover the active Run ID.
