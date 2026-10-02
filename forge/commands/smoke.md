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

When a run is paused at an allow-listed human-authorization gate, the human
must provide the requested authorization fields in the **same user message**
that invokes `/smoke RESUME <run-id>` (or explicitly include that RESUME
invocation with the authorization response). A bare RESUME while the gate is
open is valid only as a no-op: return `SMOKE_USER_INPUT_REQUIRED` and preserve
the existing open interval. Do not recover authorization from earlier chat
history.

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
4. do not delegate any substantive model/task child from the current session
   yet. Provisioning a sibling clone does not change Kilo's current project
   root. Until workspace handoff is proven, only deterministic helpers may
   target the returned `run_directory` through explicit path arguments.
5. immediately execute the deterministic smoke bootstrap exactly once:

   ```text
   python <global-config>/scripts/smoke_bootstrap.py \
     --repo <run-directory> \
     --run-id <run-id> \
     --profile <FAST|FULL> \
     --fixture <fixture-id> \
     --source <source_checkout_path> \
     --source-commit <source_commit> \
     --baseline-head <baseline_head> \
     --required-contract <global-config>/contracts/implementation-state-evidence-v1.md \
     --required-contract <run-directory>/docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md
   ```

   This single helper is authoritative for:
   - path-aware Contract-v1 parity
   - canonical `<run-id>.state.json` initialization
   - source-checkout fingerprint pinning
   - pinned profile/invocation snapshot and S1 ACTIVE transition
   - elapsed-time budget initialization
   - deterministic Phase 0 static release validation
   - persistence of the `static-release-gate` scenario transition and timing

   The bootstrap derives the installed `<global-config>` root from its own
   installed script location. The orchestrator MUST NOT call
   `smoke_static.py release-gate` separately, probe either helper with
   `--help`, or infer whether `<global-config>` means a directory or a file.

6. require bootstrap `ok: true`, require both `<run-id>.state.json` and
   `<run-id>.budget.json` to exist, require
   `completed_scenarios` to contain `static-release-gate`, and require the
   canonical next stage to be `grill` for FULL or `project-init` for FAST
   before launching any planning/execution model
7. if bootstrap reports the static release gate blocked, retain its persisted
   `BLOCKED` state and report the failing check IDs
8. before any substantive model/task delegation, invoke the deterministic
   workspace-root handoff:

   ```text
   python <global-config>/scripts/smoke_handoff.py \
     --repo <run-directory> \
     --run-id <run-id> \
     ensure
   ```

   Invoke this one shell-tool call with a per-command timeout of at least
   **3,600,000 ms (60 minutes)**. Kilo's shell timeout is only transport
   supervision for the nested CLI process; it is NOT the smoke qualification
   budget and MUST NOT replace, reset, or extend the pinned ACTIVE-segment
   `smoke_budget.py` clock. It does not itself pause qualification time.
   Qualification time excludes only helper-validated, allow-listed
   human-authorization wait intervals as defined below.

   The helper validates that the target is the initialized `smoke-run`
   repository for this run. It never trusts the shell working directory alone:
   a session counts as rooted only when it carries the handoff marker
   (`SUBHFORGE_SMOKE_RUN_ID`, `SUBHFORGE_SMOKE_RUN_DIRECTORY`,
   `SUBHFORGE_SMOKE_HANDOFF_TOKEN`) whose token digest matches the current
   `docs/verification/smoke/<run-id>.handoff.json` record, and its working
   tree is the disposable repository. Otherwise it mints a fresh token, writes
   that record, and launches a top-level continuation with the disposable
   repository as both process working directory and Kilo `--dir`. A new
   handoff invalidates every earlier rooted session for the same run.

   Because the continuation runs with Kilo `--auto` (which approves every
   permission not explicitly denied), the helper also injects a
   `KILO_CONFIG_CONTENT` overlay that disables `adversary-opus` and
   `adversary-sonnet` and denies `external_directory` access to the protected
   SubhForge source checkout (from install provenance and the launching
   session's root). Kilo strips that variable from model-visible shells, so
   rooted agents cannot remove it.

   - `ALREADY_ROOTED` — continue in this session
   - `HANDOFF_COMPLETE` — the rooted continuation owned smoke execution; the
     source-root invocation MUST stop and relay its result rather than execute
     another smoke stage
   - helper failure — return `SMOKE_BLOCKED`; do not delegate a child model.
     A marked session whose marker is stale, belongs to another run, or whose
     working tree is not the disposable repository fails here instead of
     launching a nested continuation.

9. only in an `ALREADY_ROOTED` session, ensure the human-readable
   `docs/verification/smoke/<run-id>.md` projection exists before the first
   substantive child/model stage
10. never replace bootstrap or workspace handoff with ad-hoc PowerShell/Python
    equality checks, manual state creation, a separate budget-start sequence,
    a second static release-gate invocation, direct `kilo run` construction,
    or prompt-only instructions to write into a sibling repository
11. never reuse an existing run directory or run ID

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

- locate the run workspace using `python <global-config>/scripts/smoke_workspace.py locate --source <source_checkout_path> --run-id <run-id>` and validate the returned run directory/branch
- run `smoke_budget.py ... check` before handoff and inspect
  `active_human_wait`
- when an allow-listed human wait is open, treat the budget ledger as the
  qualification-time authority. Canonical smoke state should be
  `WAITING_FOR_USER` with the same `gate_type`/`gate_id`; if a crash
  occurred after the helper opened the wait but before that projection was
  persisted, repair only that exact projection from the helper-returned gate
  identity before continuing
- an open wait does not by itself authorize anything. If the current RESUME
  invocation does not contain explicit human authorization for that exact
  request, return `SMOKE_USER_INPUT_REQUIRED` without handoff and without
  changing the wait interval
- when the current RESUME contains explicit waiver authorization, capture it
  before handoff with the deterministic `human-wait-authorize` action using
  the active `gate_id`, exact report/failure set/classification, and the
  human-supplied decision, justification, residual risk, compensating control,
  remediation, and expiry. This action validates the disposable workspace and
  gate binding but intentionally does not require a rooted marker because it is
  the bridge that persists the current user's decision before the autonomous
  rooted continuation starts
- if `human-wait-authorize` rejects missing, mismatched, or invalid input,
  return `SMOKE_USER_INPUT_REQUIRED`; the existing open interval remains
  byte-for-byte unchanged. Do not close/reopen it and do not launch a model
- if authorization was already persisted before a crash, do not ask the human
  to repeat it; continue from the closed interval and its persisted
  authorization
- invoke `python <global-config>/scripts/smoke_handoff.py --repo <run-directory> --run-id <run-id> ensure` before any substantive child/model delegation, using a shell-tool timeout of at least 3,600,000 ms (60 minutes); this transport timeout does not alter the pinned ACTIVE-segment qualification budget
- if handoff returns `HANDOFF_COMPLETE`, stop the source-root invocation and
  relay the rooted continuation result; do not continue smoke orchestration in
  the source checkout
- require `ALREADY_ROOTED` before continuing lifecycle orchestration
- immediately run
  `python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> recover-active --source <source_checkout_path> --reason RESUME_RECOVERY`
  before any new model call or budget-continuation decision; this helper
  performs the persisted pre-child source-fingerprint comparison before writing
  the recovery transition
- `INTERRUPTED_INVOCATION_RECOVERED` with
  `source_guard_result.result=MATCH` permits normal state/evidence
  re-evaluation; do not accept interrupted child artifacts merely because they
  exist
- recovered source `MISMATCH` persists a restart-safe
  `SOURCE_CHECKOUT_MUTATED` continuation blocker and returns
  `SMOKE_BLOCKED / SOURCE_CHECKOUT_MUTATED`
- missing/invalid legacy source fingerprint persists
  `INTERRUPTED_SOURCE_GUARD_UNAVAILABLE` and returns
  `SMOKE_RUN_UNRECONSTRUCTABLE`; a fresh fingerprint cannot prove the
  interrupted interval
- `RECOVERY_BLOCKED` means an earlier continuation blocker remains authoritative
  across repeated RESUME attempts
- if the recovery source-guard helper itself fails, the invocation remains
  ACTIVE so a later RESUME can retry
- if recovery reports multiple ACTIVE invocations or corrupt timing evidence,
  fail closed for diagnosis
- ensure `docs/verification/smoke/<run-id>.md` exists in the rooted repository
  before the next substantive child/model stage
- validate profile and fixture from the run record
- identify completed, pending, blocked, and invalidated scenarios
- run the end-to-end budget guard before any lifecycle/model continuation
- if the run is already `PERFORMANCE_BUDGET_EXCEEDED`, do not launch another
  lifecycle/model stage; RESUME may only support diagnosis/evidence handling,
  STATUS, or abandonment for that exhausted run
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

The packet MUST include:

- `SMOKE_RUN_DIRECTORY: <absolute run_directory>`
- exact project paths under a `CONTEXT_PATHS` section
- one smoke discovery policy

`SMOKE_RUN_DIRECTORY` is an assertion of the already-established Kilo project
root, not a request for a child to operate on an external sibling directory.
The orchestrator MUST have received `ALREADY_ROOTED` from
`smoke_handoff.py` before any `task` delegation. All project artifact paths
must resolve inside that actual rooted repository. A smoke child must never be
used to bridge from the SubhForge source checkout into a sibling clone.

This is enforced deterministically, not only by prompt discipline:
`smoke_budget.py stage-start` and `stage-end` call
`smoke_handoff.py assert-rooted` and fail closed outside the current rooted
handoff. A child launched from any other session therefore cannot obtain a
timing record, and its result cannot be accepted into canonical state.

The smoke orchestrator must fingerprint the source checkout with
`smoke_workspace.py source-guard` immediately before every substantive child
invocation and verify the same fingerprint immediately after it returns. A
mismatch is `SMOKE_BLOCKED / SOURCE_CHECKOUT_MUTATED`; do not accept the
child's stage result.

The discovery policy MUST be one of:

- `DISCOVERY_POLICY: EXACT_ONLY` when all required context for the stage is known
- `DISCOVERY_POLICY: BOUNDED` only when the parent can name a concrete unresolved item

Under `EXACT_ONLY`, repository-wide glob/grep/search is prohibited. If a
required supplied path is missing, stale, ambiguous, or insufficient, the child
must return the concrete unresolved item to the parent instead of widening
discovery on its own.

Under `BOUNDED`, the packet MUST name the unresolved item and smallest allowed
search scope. The child may search only that scope and must report why the
search was needed.

When a required path is supplied and validates successfully, repository
globbing to rediscover that same artifact or directory remains prohibited.

The rooted continuation uses Kilo autonomous mode only so configured
tool-permission prompts can execute non-interactively inside the validated
disposable repository. That mode is **not human authorization**. It MUST NOT be
treated as approval for a verification waiver, paid Claude invocation,
security/risk acceptance, product decision, destructive action, or any other
human-controlled gate. When such a gate lacks already-persisted explicit user
authorization, persist the required state and return the normal user-input/
blocked status instead of deciding autonomously.

`WAITING_FOR_USER` by itself never stops the qualification clock. Only an
open interval created by the deterministic human-wait helper for an
allow-listed gate type is excluded. Stable v0.1 currently allow-lists only
`WAIVER_AUTHORIZATION`; paid-model escalation, destructive-action approval,
product decisions, and other human gates remain blocked/non-pausing unless a
future hardening decision explicitly adds their gate contract.

Paid Claude adversaries are unavailable inside the rooted autonomous
continuation: `smoke-orchestrator` denies them and the handoff overlay disables
them for every agent. The optional `paid-claude-runtime` scenario therefore
cannot run inside autonomous smoke; it requires a separate, interactive,
explicitly user-authorized invocation.

The child must not rediscover supplied paths unless one is missing, stale,
ambiguous, or points to unresolved authority:

- `AUTHOR`
- `CONTINUE`
- `RECONCILE_ONLY`

For smoke planning stages, the orchestrator owns smoke mechanics and MUST reduce
them into a compact handoff. The planning child must not independently read
`smoke/fixtures.json`, `smoke/profiles.json`, `smoke/failure-recipes.json`,
the full smoke runbook, or canonical smoke state merely to recover information
already present in the handoff.

The handoff SHOULD contain only:

- execution mode
- discovery policy
- exact authoritative artifact paths required by that planning stage
- project-level AGENTS/README paths when materially relevant
- fixture/runtime/acceptance constraints already resolved by the orchestrator
- the specific expected output artifact/path for the stage

Before and after the child invocation, record a stage metric in canonical smoke
state containing at minimum:

- stage ID
- model
- elapsed seconds
- exact context paths supplied
- discovery policy

This telemetry is diagnostic only; it must not change workflow authority or
completion semantics.

For the default Stable-v0.1 smoke path, use GPT-5.6 Sol for these planning stages.

### H08b bounded early-lifecycle procedure

For FULL S1, the orchestrator MUST use `smoke_h08b.py` to seed and score the
normal blocked/resumed discovery artifact without exposing hidden expectations:
`seed-discovery → real /grill → parse actual status → score-discovery --phase blocked --status <actual> →
restore-evidence → real /grill CONTINUE → parse actual status →
score-discovery --phase resumed --status <actual>`.
Never replace a parsed child status with the expected status token.

For the user-selected direct-to-PRD branch use:
`begin-direct-prd → one Sol /prd → score-direct-prd → restore-direct-prd`.
The scorer requires zero discovery artifacts during that isolated call.

For the main PRD blocked/resumed path use:
`seed-product-decision → one Sol /prd → score-prd blocked →
reveal-product-decision → one Sol /prd → score-prd resumed`.
The hidden approved value must not be supplied to the first child.

For the normal successful Luna `/project-init`, use a fresh
`h08b-luna-probe` child and include
`docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json` plus the canonical contract as
exact authoritative context. Parse its actual terminal status, then require
`score-project-init-policy --status <actual>` PASS.

For the independent negative, use:
`begin-project-init-negative → score-project-init-helper → fresh h08b-luna-probe
/project-init → parse actual status/OWNER/BLOCKING_ISSUE/REQUIRED_ACTION/NEXT_COMMAND →
score-project-init-luna with those exact actual fields →
restore-project-init-negative`.
The prepared branch removes the project canonical Contract-v1 file; neither the
helper nor Luna child may invent a substitute contract, and the normal blocker
must identify the canonical-contract cause and route back to `/project-init`.

For S2 `direct-fix-loop`, the exact sequence remains:

`DeepSeek /verify (behavioral-test NOT_DONE) → fresh h08b-luna-probe /waive →
DeepSeek /fix → DeepSeek /verify → DeepSeek pre-review → Sol senior review when ready`.

Do not provide the expected refusal reason/status to the Luna child. Parse its
actual terminal status and the normal refusal artifact it creates, then validate
with `smoke_h08b.py validate-refusal --run-id <run-id> --status <actual>`.
The run-scoped scorer is the component that requires actual `WAIVER_BLOCKED`
plus `POLICY_INELIGIBLE`, exact report/policy binding, and zero H07 wait.
No extra/fallback verification is permitted.

For every H08b scorer action, register its returned immutable `score_path`
with `smoke_segments.py register-evidence` for the matching required subprobe.
For direct PRD also register the returned immutable `prd_evidence_path`.
S1/S2 close validates the required H08b score files as schema-valid `PASS`
before the segment can close; a file-backed `FAIL` score is not acceptable.

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

When the waiver scenario reaches a policy-eligible failed verification but
explicit authorization is missing:

1. finish the current timed child normally; no model stage may remain ACTIVE
2. run the budget check
3. open the human gate from the rooted disposable session:

   ```text
   python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> human-wait-start \
     --gate-type WAIVER_AUTHORIZATION \
     --verification-report <exact-report-path> \
     --implementation-state-fingerprint <exact-GIT_BLOB_OID> \
     --failure <exact-failure-id> [--failure <exact-failure-id> ...] \
     --classification <waiver-classification>
   ```

   Before opening the interval, the helper also validates canonical smoke
   state: profile `FULL`, current scenario `waive-review-loop`, waiver
   verification/waive stage, and latest verification exactly
   `NOT_DONE / BLOCKED / MATCH`. This prevents a model from manufacturing a
   budget pause merely by naming an existing file.

   The helper derives `gate_id` as SHA-256 of a canonical payload containing
   the run ID, gate type, exact verification-report path, SHA-256 of the exact
   verification-report bytes, Contract-v1 implementation-state fingerprint,
   exact canonically ordered failure set, and classification. The orchestrator
   never invents an opaque gate ID. If the report bytes change while the human
   request is open, authorization fails closed and the interval is not mutated.

4. persist canonical smoke state as `WAITING_FOR_USER`; the blocker must carry
   the helper-returned `gate_type`, `gate_id`, and exact request identity
5. return `SMOKE_USER_INPUT_REQUIRED`

The helper permits at most one open interval. Repeating `human-wait-start`
for the same open request is an idempotent no-op and preserves its original
start timestamp. A different request cannot open while one is active, and a
completed `gate_id` can never be reopened.

While an interval is open, `stage-start` fails closed. The human may take any
amount of wall-clock time without consuming qualification time, but crashes,
retries, ordinary inactivity, debugging, and unrelated blocked states are not
excluded.

On the later source-root `/smoke RESUME <run-id>`, require the human to
explicitly supply/approve the normal `/waive` fields. Capture that exact
decision with:

```text
python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> human-wait-authorize \
  --gate-type WAIVER_AUTHORIZATION \
  --gate-id <persisted-gate-id> \
  --decision ACCEPTED_TEMPORARILY \
  --verification-report <exact-report-path> \
  --failure <exact-failure-id> [--failure <exact-failure-id> ...] \
  --classification <waiver-classification> \
  --justification <human-supplied-justification> \
  --residual-risk <human-supplied-residual-risk> \
  --compensating-control <human-supplied-control> \
  --remediation <human-supplied-remediation> \
  --expiry <human-supplied-expiry>
```

The source-root orchestrator may structure/quote those values for the helper,
but must copy the human decision faithfully and must not synthesize missing
risk acceptance. The helper verifies the disposable workspace, canonical FULL
`waive-review-loop` state, current `NOT_DONE / BLOCKED / MATCH`
verification, `WAITING_FOR_USER` blocker with the same `gate_type/gate_id`,
exact gate, report, failure set, classification, decision token, and all
required non-empty authorization fields **before** writing anything. A rejected/invalid RESUME is
therefore a pure no-op on the existing open interval.

A valid authorization closes that one interval and persists the authorization
payload with it. A deliberate human decline is not an authorization error to
reinterpret as approval: do not call `human-wait-authorize`; leave the gate
open and instruct the user to use `/smoke ABANDON <run-id>` if they want to
terminate the run. Then perform the normal rooted handoff only after acceptance. The rooted continuation
uses that persisted payload as the human input to `/waive`; it must not
reconstruct authorization from chat history or `--auto`. If freshness or
policy later blocks the waiver for a non-human-input reason, report that normal
blocker; never fabricate approval or reopen the completed gate. A genuinely new
verification report/failure set requires a new gate identity.

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

Do not use Claude during smoke testing unless the user explicitly authorizes that isolated paid invocation. Inside the rooted autonomous continuation, paid Claude adversaries are denied/disabled regardless of authorization; an authorized paid check runs as a separate interactive invocation.

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

Use the installed `scripts/smoke_resume.py` helper for all deterministic H05
mechanics. Its seven probe IDs (`r01`...`r07`) are harness-internal and
opaque. The routing model must never receive a probe ID, expected stage,
checkpoint label, score, or prior probe result.

For each probe:

1. require the clean source checkpoint to be `MATCH`
2. call `smoke_resume.py prepare` with the exact active Spec,
   implementation/test/config paths, applicable fresh verification path,
   disposable baseline HEAD, checkpoint label, and one opaque probe ID
3. require preparation validation to succeed
4. invoke a **new** GPT-5.6 Luna `resume-router` child with no prior probe
   answers and no stage-specific context packet
5. give that child only the rooted repository assertion, the deterministic
   manifest-helper path, and the instruction to inspect normal persisted
   repository evidence and choose the earliest continuation command
6. require exactly one `RESUME_STAGE:` and one concise `REASON:`
7. score the actual result with `smoke_resume.py score`
8. routing-only probes stop after scoring and exact restoration
9. after every probe, require the snapshot restoration and declared Contract-v1
   checkpoint to reproduce exactly

The fresh router may inspect normal project artifacts but must not read
`docs/verification/smoke/**`, canonical smoke state, timing/mechanics/resume
ledgers, global smoke registries/runbook/helper source, or another probe's
result.

For the one approved-Spec handoff case, a passing route score returns
`handoff_required=true`. Then invoke exactly one DeepSeek `smoke-executor`
request:

```text
WORKFLOW: /implement
HANDOFF_PROBE_ONLY: true
```

with the exact persisted active Spec and normal implementation context. Require
`SMOKE_IMPLEMENT_HANDOFF_ACCEPTED`, persist that handoff evidence through the
resume helper, and restore. Do not edit implementation files or replay the
implementation/verify/review lifecycle for this probe.

The H05 helper snapshots all Git-tracked plus non-ignored untracked repository
files except `docs/verification/smoke/**`. Prepared probes therefore alter
only the disposable smoke repository, and restoration must reproduce the full
snapshot plus the declared Contract-v1 checkpoint. A failed preparation,
routing score, handoff, or restoration is `SMOKE_BLOCKED`.

After seven passing, restored probes, require
`smoke_resume.py status` to return `PASS` before marking
`arbitrary-stage-resume` complete.

If a resume-router or bounded handoff child is interrupted before the probe is
scored, complete normal H02 invocation recovery, restore the active probe, then
retry the same opaque probe ID. Only `RESTORED + NOT_SCORED` is retryable;
scored `PASS` or `FAIL` attempts remain immutable and single-use.

Normal non-smoke resume behavior is unchanged. Do not replace resume routing
with a deterministic lookup table; only the fresh Luna routing context chooses
the continuation stage.

## Upstream-authority rerouting smoke optimization

The FULL `upstream-rerouting` scenario uses installed
`scripts/smoke_reroute.py` to prepare and restore eight opaque blocked-state
probes. The helper owns mechanics and hidden scoring only; the normal model
owner still classifies the authority boundary.

For each `u01`...`u08` probe:

1. start from one matching clean checkpoint
2. prepare exact normal PRD/architecture/ADR/Spec/project-instruction/
   implementation/verification context with `smoke_reroute.py prepare`
3. never pass the opaque probe ID, expected owner/command, checkpoint, score,
   helper source, or smoke ledger to the child
4. when the helper returns `classifier=planning`, use one GPT-5.6 Sol
   `planning-worker` call with `MODE: AUTHOR`,
   `UPSTREAM_ROUTE_PROBE_ONLY: true`, the returned workflow, exact context,
   and `DISCOVERY_POLICY: EXACT_ONLY`
5. when it returns `classifier=fix`, use one DeepSeek `smoke-executor`
   request with `WORKFLOW: /fix`, `UPSTREAM_ROUTE_PROBE_ONLY: true`, and
   exact repair context
6. require exactly `BLOCKED_STATUS:`, `OWNER:`, `NEXT_COMMAND:`, and
   `REASON:`; score only those actual values
7. after a passing score, persist the helper-returned deterministic
   regeneration path
8. restore every routing-only probe immediately and require exact snapshot +
   Contract-v1 checkpoint reproduction
9. if the child is interrupted before scoring, recover the interrupted stage,
   restore the active probe, and retry that same opaque ID only when the ledger
   says `RESTORED + NOT_SCORED`. Scored `PASS`/`FAIL` probes are never
   retried

The required prepared cases cover:

- architecture blocked by contradictory product behavior → product authority
- specification blocked by conflicting architecture/ADR authority
- implementation blocked because satisfying the Spec requires an unapproved
  architecture/persistence change
- fix blocked by product contradiction
- fix blocked by architecture change
- fix blocked by project-init/repository-initialization drift
- fix blocked by contradictory specification/acceptance criteria
- fix blocked by repository/environment state

The five normal H06 destinations are therefore `/prd`, `/architect`,
`/project-init`, `/spec`, and `/fix`. Human approval is explicitly out of
scope here.

One representative passing architecture route performs a bounded real handoff:
GPT-5.6 Sol `planning-worker` receives
`UPSTREAM_HANDOFF_PROBE_ONLY: true`, `WORKFLOW: /architect`, and exact
persisted context. Require `SMOKE_UPSTREAM_HANDOFF_ACCEPTED`; do not author
the correction or replay downstream regeneration. Record the handoff through
the reroute helper and restore exactly.

After all eight probes pass and restore, `smoke_reroute.py status` must return
`PASS` before marking `upstream-rerouting` complete.

Normal blocked-output contracts remain authoritative. H06 does not replace
real workflow authority with deterministic routing.

## Deterministic harness regression precondition

Repository hardening uses a separate deterministic-test runtime budget before
release-qualifying smoke:

- focused/current-item target <=60s, ceiling 90s
- full `forge/scripts` target <=180s, temporary H06-H11 ceiling 300s
- `tools` target <=30s, ceiling 60s
- >10% full-suite regression against the last accepted same-host baseline
  requires investigation/optimization before merge
- H12 requires the full <=180s target

This is a developer/release-preparation gate, not part of the pinned segmented smoke
qualification clock. Do not rerun the entire deterministic suite inside a
`/smoke` run merely to satisfy this policy; consume the pre-merge evidence.
Never reduce runtime by weakening required tests.

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
result. For Git mode changes, use the bounded platform-aware mechanics defined
by the scenario; never fake unsupported Windows mode semantics.

The `verification-mutation` recipe is special and MUST NOT use ordinary
`mutate`. From the matching clean checkpoint:

1. arm it with
   `smoke_mechanics.py ... arm-verification-mutation --mutation-id <id> --checkpoint <checkpoint>`
2. delegate exactly one DeepSeek `WORKFLOW: /verify` and include
   `VERIFICATION_MUTATION_ID: <id>`
3. the smoke executor fires that registered hook only after required checks and
   acceptance evidence, immediately before the post-check manifest
4. require the persisted `/verify` result to show factual checks `DONE`,
   freshness `MISMATCH`, and delivery gate `BLOCKED`; invoke zero reviewers
5. restore with `smoke_mechanics.py ... restore --mutation-id <id>` and require
   `check-checkpoint` to return `MATCH`

The hook creates/deletes only its harness-owned identity marker; neither Luna
nor DeepSeek chooses an application file or replacement. Do not run a second
`/verify` merely to complete this bounded H04 scenario. The restored state
still requires a fresh normal `/verify` before any later review attempts, as
the normal freshness contract requires.

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

FULL qualification runs as six sequential checkpoint-bound segments. Each segment uses
its pinned positive limit from the bootstrap snapshot; there is no second aggregate hard
limit. The provisional limits are S1=80, S2=48, S3=38, S4=53, S5=36, and S6=40 minutes
(295 minutes derived configured allowance). A segment clock starts only when its ACTIVE
transition commits and never resets after crash/recovery. Within an ACTIVE segment only
helper-validated `WAIVER_AUTHORIZATION` waits are excluded; ordinary inactivity, transport,
debugging, retries, and crash/recovery remain charged. BETWEEN_SEGMENTS gaps are recorded
separately and permit no substantive lifecycle/model work.


For FULL, `smoke_segments.py` is the only segment lifecycle authority. The
orchestrator MUST:

1. treat bootstrap's committed S1 ACTIVE record as the start of S1; never create
   another S1 start timestamp
2. after each required subprobe is scored, register the factual result and every
   accepted report/artifact path with:
   `smoke_segments.py ... register-evidence --scenario <scenario-id> --subprobe <subprobe-id> --fact <factual-score> [--evidence <repo-relative-path> ...]`.
   Every declared model-bearing subprobe requires at least one file-backed evidence
   path; free-text facts alone cannot create `SCORED_PASS`.
3. never mark a top-level scenario complete in place of its required subprobe
   evidence; segment close validates both
4. after the segment's assigned scenarios/subprobes are complete, the exact close
   checkpoint is MATCH, and no child/H07 wait is open, call
   `smoke_segments.py ... close --source <source_checkout_path>`. S5 additionally
   requires `smoke_resume.status(...).result == PASS` with its resume ledger in
   accepted evidence; S6 requires `smoke_reroute.status(...).result == PASS`,
   its reroute ledger, and an exact `CP-REPAIRED-STABLE` match before the
   `QUALIFICATION_EVIDENCE_READY` close marker is committed.
5. after a committed close, do no substantive work. Optional gap bookkeeping may
   use `gap-record` only for `OPERATOR_INACTIVITY`, `READ_ONLY_STATUS`, or
   `READ_ONLY_PREFLIGHT`
6. before continuing, call
   `smoke_segments.py ... open-next --source <source_checkout_path>`. A failed
   read-only preflight remains in the gap; proven source/checkpoint/config/evidence/
   ledger drift disqualifies the qualification and must not be repaired in-gap
7. use `smoke_segments.py ... report` for configured allowance, aggregate charged
   active time, excluded H07 waits, recorded inter-segment gaps, and total wall time.
   The report revalidates the complete closed evidence/ledger chain. Integrity drift
   disqualifies the qualification but does not suppress diagnostics: the report still
   returns `qualification_eligible: false`, the persisted disqualification reason,
   `integrity_status: FAILED`, and the integrity error alongside safely reconstructable
   timing/gap data. A terminal FULL PASS transition performs byte-level revalidation
   again and remains fail-closed.

The complete accepted evidence membership is derived from the immutable per-segment
scenario-evidence index; callers do not select a smaller close manifest. A segment
timeout permanently makes the qualification ineligible for PASS.

Before EVERY substantive lifecycle/model stage, run:

```text
python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> check
python <global-config>/scripts/smoke_budget.py --repo <run-directory> --run-id <run-id> stage-start --stage <stage-id> --model <model-id> --source-fingerprint <pre-child-source-fingerprint>
```

Retain the returned invocation ID. `stage-start`, `stage-end`,
`stage-abort`, and `recover-active` fail closed unless they run inside the
current rooted handoff for this run (see the workspace-root handoff above).
`stage-start` also fails closed whenever a human-authorization wait is open.
The only source-root budget mutation is `human-wait-authorize`, which can
close but never open/restart a wait and first validates the exact disposable
workspace and persisted gate identity.

After every child call returns or reports a transport/tool failure, verify the
pre-child source fingerprint **before** accepting the result:

- source mismatch: `stage-abort --reason SOURCE_CHECKOUT_MUTATED`; this
  persists a restart-safe continuation blocker, then block
- source-guard execution failure: leave the invocation ACTIVE and block the
  current session so RESUME can retry its persisted pre-child guard
- source matches but child transport/tool invocation failed:
  `stage-abort --reason CHILD_INVOCATION_FAILED`
- normal returned workflow result (including a domain BLOCKED/WAITING result):
  `stage-end`

Then run the budget check. A process/session crash may prevent both end and
abort; on the next rooted RESUME, `recover-active` changes the stale ACTIVE
record to INTERRUPTED before any new child is launched. Interrupted timing does
not fabricate elapsed runtime.

Use only a `COMPLETED` stage timing result for canonical successful
`stage_metrics`. ABORTED/INTERRUPTED records remain diagnostic ledger
evidence and do not make a workflow stage complete.

If the guard returns exit code 3 / `PERFORMANCE_BUDGET_EXCEEDED`:

- do not launch another lifecycle/model stage
- persist elapsed time, current stage, ledger, and blocker
- return `SMOKE_BLOCKED` with `PERFORMANCE_BUDGET_EXCEEDED`
- keep the workspace for diagnosis, STATUS, evidence preservation, or ABANDON
- do not call this a functional `SMOKE_FAIL`
- do not continue the same exhausted clock toward a release-qualifying PASS

The orchestration guard is a boundary stop: it prevents any new stage after the
budget is exceeded and catches over-budget child calls immediately on return.
It cannot forcibly terminate a child model invocation already in progress, so
one child may finish after the ceiling. A later `RESUME` does not reset the
segment clock or convert an over-budget qualification into a qualifying PASS. Do not claim
otherwise.

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

The helper is the fail-closed schema boundary for canonical state. Unknown
top-level fields, invalid run-state/stage/scenario IDs, duplicate or overlapping
completed/pending scenarios, invalid blocker/final-result shapes, premature
scenario completion, inconsistent terminal result tokens, and attempts to
change immutable identity or protected bootstrap context are rejected without
partially writing the JSON. Do not rely on the helper to auto-repair a
bad model update; correct the proposed transition and submit a coherent update.

For `context_index` and `stage_metrics`, send only the keys being added or
replaced. The helper merges those maps by key and preserves unrelated existing
entries. Bootstrap-owned `contract_parity` and `budget_started_at_utc` are
write-once: an identical repeat is harmless, but a different value fails
closed. Do not read/reconstruct/resend the entire nested map merely to append
one artifact path or one stage metric.

Example:

```text
{"context_index":{"discovery":"docs/discovery/..."}}
{"stage_metrics":{"grill":{"model":"GPT-5.6-Sol","elapsed_seconds":108.9,...}}}
```

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
