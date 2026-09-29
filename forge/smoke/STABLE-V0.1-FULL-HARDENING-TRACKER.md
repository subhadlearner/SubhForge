# Stable v0.1 FULL Smoke Hardening Tracker

This tracker is the Git-authoritative work list for the audit-discovered
hardening required before another release-qualifying FULL smoke run.

It exists to avoid relying on chat history and to enforce one-issue-at-a-time,
reviewable hardening.

## Governing rules

For every item:

1. Work on one tracker item at a time.
2. Define the invariant and acceptance gate before changing code.
3. Make the smallest coherent change that satisfies that invariant.
4. Add regression tests reproducing the observed or audited failure class.
5. Add adjacent negative/boundary coverage where the change could affect
   another invariant.
6. Review the complete diff and second-order effects before closing the item.
7. Record the closing commit SHA in this tracker.
8. Do not begin the next item until the current item is closed or explicitly
   deferred with rationale.
9. Passing tests alone are not sufficient to close an item; the underlying
   system invariant must also be demonstrated.
10. Do not run another FULL smoke until all release-gating tracker items below
    are closed and the small Kilo integration probe passes.

Preserve the existing engineering principle:

> Deterministic infrastructure/mechanics, probabilistic agents.

Do not make planning, implementation, verification judgment, review judgment,
adversarial reasoning, or routing decisions deterministic merely to make the
smoke test easier.

## Durable hardening operating context

This section records the working rules and closed design decisions that must
survive chat/context changes. Treat it as part of the hardening contract, not
as informal history.

### Branch and PR discipline

For each hardening item:

1. Start from the current `harden/v0.1-full-smoke` head.
2. Create one dedicated branch named for that item, e.g.
   `harden/h05-...`.
3. Keep the branch scoped to that tracker item. Do not make H(N+1)+ changes
   unless they are strictly required to make the current invariant correct;
   record any such coupling before expanding scope.
4. Prefer one coherent implementation commit on the item branch. Rewriting
   that one commit during pre-merge review is acceptable while the PR is still
   open and unmerged.
5. Open the PR as **Draft** until deterministic/local verification is complete.
6. Verification normally includes:
   - focused regression tests for the item;
   - adjacent compatibility tests;
   - the full `forge/scripts` suite;
   - the `tools` suite;
   - `git diff --check harden/v0.1-full-smoke...HEAD`;
   - a clean `git status --short`.
7. Review the full diff and second-order effects after tests pass. Green tests
   alone are not sufficient.
8. Move the PR out of Draft only after the invariant and verification evidence
   are both satisfactory.
9. Squash-merge the PR into `harden/v0.1-full-smoke`.
10. Only after the real squash SHA exists, update this tracker on the hardening
    branch: mark the item `DONE`, record the merge SHA/evidence, and promote
    the next item to `TODO — NEXT`.
11. Do not start the next tracker item before that closure update.
12. Do not spend model/Kilo calls on an item whose acceptance gate is fully
    deterministic. Real integrated Kilo proof belongs to H13 unless the
    current item explicitly requires a model-bearing acceptance test.

Operator note for the current Windows workstation: use `python` for local
test execution; the local `py -3` launcher has previously pointed at a stale
Python path and is not a reliable hardening command.

### Global smoke invariants

The following invariants apply across the tracker unless a later item
explicitly and intentionally changes them:

- **Disposable repository ownership:** smoke must provision/use its own
  disposable repository. The user must not be required to manually open or
  select an arbitrary repository merely to run the harness.
- **Real Kilo rooting:** substantive model-bearing smoke work must execute with
  the top-level Kilo session rooted in the disposable smoke repository. Child
  tasks inherit that real project/worktree; prompt-only path instructions are
  not an isolation mechanism.
- **Source checkout protection:** the SubhForge source checkout is an input,
  not the smoke workspace. Before and after every substantive child invocation,
  the source checkout is fingerprinted deterministically. Source mutation is a
  fail-closed blocker and the child result is not accepted.
- **Deterministic mechanics, probabilistic judgment:** helpers may provision,
  fingerprint, validate, checkpoint, mutate, restore, time, and enforce
  contracts. They must not replace planning, implementation, verification,
  review, adversarial, or resume-routing judgment with lookup tables merely to
  make smoke tests pass.
- **Canonical machine state:** `<run-id>.state.json` is the authoritative
  orchestration record. Markdown is an audit projection, not a competing state
  source.
- **Fail-closed continuation:** malformed/inconsistent canonical state,
  unreconstructable identity, source drift, invalid recovery state, or failed
  checkpoint restoration stops the run rather than being silently repaired.
- **Contract-v1 identity:** implementation freshness is based on the canonical
  Contract-v1 manifest, not HEAD equality alone. Evidence under
  `docs/verification/**`, `docs/reviews/**`, and `docs/diagnostics/**`
  is excluded; identity-bearing source/config/spec/project-instruction changes
  are not.
- **Negative freshness/evidence paths invoke zero reviewers:** when freshness
  is `MISMATCH`/`UNRECONSTRUCTABLE` or reusable evidence is invalid,
  pre-review and senior review must not run.
- **Model routing/cost:** smoke defaults to GPT-5.6 Sol/Luna and DeepSeek.
  Paid Claude is not required for release qualification and is denied inside
  the rooted autonomous smoke continuation; any explicit paid Claude check is
  a separate user-authorized interactive action.
- **Qualification budget remains authoritative:** the 30-minute FULL
  qualification budget is not silently raised. Transport/process timeouts are
  not permission to extend qualification time. Human-wait semantics and the
  final invocation/runtime model remain unresolved until H07/H08.
- **No premature FULL:** another release-qualifying FULL is forbidden until
  H01-H12 are closed and H13's small real Kilo integration probe passes.
- **H13 is the integration catch-all, not a substitute for unit hardening:**
  deterministic items should be proven cheaply first; H13 then proves the
  assembled real Kilo path with minimal model spend.

### Closed decision record — H01 through H05

#### H01 — real disposable-workspace rooting

Closed decision:

- `smoke_handoff.py` establishes a token-bound rooted continuation and
  `assert-rooted` proves the current Git root is exactly the disposable run
  repository.
- The top-level rooted Kilo run is launched with the smoke orchestrator; child
  tasks inherit that same disposable project/worktree.
- The autonomous overlay denies access to the SubhForge source checkout and
  disables paid Claude routes for the rooted smoke continuation.
- Rooting is enforced mechanically by smoke timing/handoff guards; a child from
  the wrong session cannot obtain/complete an accepted stage timing record.
- The representative real Kilo probe
  `SMOKE-FULL-full-minimal-api-20260928T172150Z-9f874862` proved rooted
  parent handoff, real `planning-worker` delegation, denied source-checkout
  read, child-only write in the disposable repo, and unchanged source checkout.

Do not regress to a design where the operator manually opens a separate project
or where a child is merely told to write to a sibling path.

#### H02 — interrupted invocation recovery

Closed decision:

- Stage invocation lifecycle is explicit:
  `ACTIVE -> COMPLETED | ABORTED | INTERRUPTED`.
- `stage-start` persists the exact pre-child source-checkout fingerprint.
- Normal returned completion uses `stage-end`; known returned/transport
  failure uses `stage-abort`.
- `SOURCE_CHECKOUT_MUTATED` is a restart-safe continuation blocker.
- Rooted RESUME uses atomic `recover-active --source <source>`: the persisted
  pre-child source fingerprint is revalidated before ACTIVE is closed.
- A matching source closes stale ACTIVE as `INTERRUPTED`; an interrupted run
  does **not** fabricate `ended_at_utc` or elapsed runtime.
- Source mismatch persists a blocker. Missing legacy source fingerprint becomes
  `INTERRUPTED_SOURCE_GUARD_UNAVAILABLE`/unreconstructable.
- If the source-guard helper itself cannot execute, ACTIVE is deliberately left
  open so a later RESUME can retry safely.
- Duplicate terminal transitions and multiple simultaneous ACTIVE records fail
  closed.

#### H03 — canonical smoke-state validation

Closed decision:

- Canonical state has an exact top-level schema. Unknown/typo and missing fields
  fail closed.
- Identity fields such as run/profile/fixture/source/baseline are immutable
  through targeted state updates.
- Run states are a closed enum; scenarios are validated against the selected
  profile's installed registry.
- Completed/pending scenario lists are unique and disjoint. Invalid overlap is
  rejected; the helper does not silently “repair” model output.
- `static-release-gate` is the first completed smoke scenario; workflow
  advancement/current scenario cannot bypass it.
- Bootstrap-owned `contract_parity` and `budget_started_at_utc` are
  established only during bootstrap, are typed, become protected/write-once,
  and must exist once the static gate is complete.
- Terminal state and `final_result` must be consistent with the selected
  profile and required-scenario completion. Nonterminal states cannot carry a
  final result.
- `BLOCKED`/`WAITING_FOR_USER` require a non-empty blocker object, but H03
  intentionally did **not** invent a mandatory `blocker.code` schema.
- `stage_metrics` keys remain flexible non-empty telemetry labels; H03 did not
  turn telemetry into a closed workflow enum.
- Both load and set validate the whole state. A candidate update is persisted
  only after full validation, so invalid updates cannot partially mutate the
  canonical JSON.

#### H04 — deterministic verification-time mutation

Closed decision:

- `verification-mutation` is a special deterministic smoke hook and cannot
  use ordinary pre-verification `mutate`.
- Lifecycle is `ARMED -> APPLIED -> RESTORED`.
- The harness owns a fixed, local, reversible, non-evidence identity marker;
  Luna/DeepSeek do not choose an application source/test mutation.
- The hook is armed from a matching clean checkpoint without changing identity.
- DeepSeek `/verify` captures its normal pre-check manifest and runs all real
  required checks/acceptance evidence.
- Only **after checks and before the post-check manifest**, the smoke executor
  fires the registered hook. The helper itself proves Contract-v1 identity is
  now `MISMATCH`.
- The normal `/verify` contract therefore records factual
  `Verification Result: DONE` when checks passed, but
  `Freshness: MISMATCH` and `Delivery Gate: BLOCKED`.
- Reviewer calls for this negative freshness probe are zero.
- Restoration removes the marker and must reproduce the exact checkpoint.
  Armed-but-unfired hooks can also be safely disarmed.
- The authoritative post-first-review matrix permits exactly one DeepSeek
  `/verify` for this bounded scenario. Do not spend a second `/verify`
  merely to close H04; the restored implementation still needs fresh normal
  verification before any later review use.
- The static release gate verifies that the installed smoke executor/helper
  contain the H04 hook contract.

#### H05 — arbitrary-stage resume probe mechanics

Closed decision:

- The seven resume subcases are represented by opaque harness IDs `r01` through
  `r07`; their expected continuation stages remain inside deterministic
  harness code only.
- `smoke_resume.py` owns deterministic preparation, validation, scoring,
  snapshotting, restoration, and final status. It does **not** choose the
  continuation stage.
- Every probe starts from a declared matching clean checkpoint and snapshots all
  Git-tracked plus non-ignored untracked repository files except
  `docs/verification/smoke/**`.
- The seven persisted states cover: architecture-ready/project-init-incomplete,
  project-init-ready/no-Spec, Spec-ready/no-implementation,
  implementation/no-verification, fresh verification, stale verification, and
  unresolved blocking review evidence.
- Stale verification is established by a real Contract-v1 implementation
  identity `MISMATCH`, not by trusting a stale label in a report.
- A fresh GPT-5.6 Luna `resume-router` makes the routing decision from normal
  persisted project evidence only. The helper may score that actual decision
  against the hidden expected route after the child returns.
- The router never receives probe ID, expected stage, checkpoint label, prior
  probe result, scoring output, or stage-specific `CONTEXT_PATHS`.
- Access to `docs/verification/smoke/**` is denied mechanically for
  `read`, `glob`, and `grep`; general `git status` is not exposed because
  it could leak smoke-ledger/snapshot filenames.
- Before scoring, the helper proves the prepared repository snapshot is
  unchanged so the routing child cannot mutate its own evidence.
- Six probes are routing-only and restore immediately after scoring.
- The approved-Spec probe alone may perform one bounded DeepSeek
  `WORKFLOW: /implement` handoff with `HANDOFF_PROBE_ONLY: true`.
  That handoff validates the exact persisted Spec/project context but must not
  edit source/tests/config, run implementation/test commands, or continue into
  verification/review.
- The handoff result is accepted only if the prepared snapshot remains
  unchanged.
- Every probe restores the complete clean snapshot and must reproduce the
  declared Contract-v1 checkpoint exactly.
- Final H05 status is PASS only after all seven opaque probes are both PASS and
  restored.
- The static release gate protects the resume-router route, no-leak permissions,
  resume helper presence/mechanics, and Scenario-C handoff contract.
- Normal non-smoke resume behavior is unchanged; deterministic helpers do not
  replace real resume-routing judgment.

### Current hardening boundary

H06 is the only current implementation target.

Do not pull H07+ work into H06 merely because neighboring blocked-state
preparation problems look similar. In particular:

- H07 owns human waiver waiting/authorization versus the 30-minute clock.
- H08 owns the real FULL invocation/runtime budget reconciliation.
- H09/H10 own containment/target-identity strengthening.
- H11 owns the dry orchestration/contract validator.
- H12 is the final deterministic/system consistency gate.
- H13 is the small real Kilo integration probe.
- H14 is the next release-qualifying FULL.

Existing ceremony-bypass support for valid pre-existing upstream authority
remains deferred and must not be pulled into Stable-v0.1 hardening merely to
make smoke easier.

## Audit baseline

The systematic audit that created this tracker inspected branch
`harden/v0.1-full-smoke` at source HEAD:

`38f2a08d3bf40f404782ec43a72a4640388ce4b1`

The audit found that the current smoke harness should not run another FULL
qualification until the blocking items below are addressed.

## Tracker

| ID | Issue | Priority | Acceptance gate | Status | Closing commit |
| --- | --- | --- | --- | --- | --- |
| H01 | Smoke child execution is rooted in the wrong Kilo workspace; task children inherit the parent project/worktree instead of the sibling disposable clone | CRITICAL | Model-bearing smoke execution is actually rooted in the disposable repository; a representative planning child writes only there; the SubhForge source checkout remains unchanged; isolation does not depend on prompt-only path discipline | DONE — real Kilo probe `SMOKE-FULL-full-minimal-api-20260928T172150Z-9f874862` proved `ROOTED` parent handoff, real `planning-worker` delegation, denied source-checkout read, child sentinel written in the disposable repo, and unchanged source checkout | `9b5bfe0d034d41252fecd9b5ba5b787a5e73c778` |
| H02 | Interrupted/failed child invocation can leave an active `stage-start` record and make RESUME impossible | CRITICAL | Deterministic abort/recovery semantics exist; normal end, failure, interruption, post-child guard failure, duplicate end/abort, and resume are covered; no dangling active invocation prevents continuation | DONE — explicit ACTIVE/COMPLETED/ABORTED/INTERRUPTED lifecycle, persisted pre-child source fingerprint, atomic recover+source-revalidation, restart-safe continuation blockers, and no fabricated interrupted runtime; verified on Windows with 21 focused tests, 87 forge-script tests (2 skipped), 7 tooling tests, clean diff check, and clean worktree | `4841eb16ca43753db8352e475916192f3b6189ac` |
| H03 | Canonical `smoke_state` remains too permissive for model-generated updates | CRITICAL | Mutable fields are whitelisted; unknown/typo fields fail closed; states/scenarios are validated; completed/pending/current-stage invariants are enforced; protected identity/bootstrap context cannot be silently corrupted | DONE — exact top-level schema; immutable identity; selected-profile scenario validation; unique/disjoint scenario lists; static-release-gate ordering; bootstrap-only protected context; terminal-state/final-result consistency; atomic fail-closed load/set validation; stale handoff fixture corrected without weakening production invariants; verified on Windows with 27 state tests, 9 static-gate tests, 3 bootstrap tests, 25 handoff tests, 105 forge-script tests (2 skipped), 7 tooling tests, clean diff check, and clean worktree | `f7164215b7d6fafa87025360de0a7795bf7d2134` |
| H04 | Required `verification-mutation` scenario lacks a deterministic verification-time mutation primitive | CRITICAL | A registered mutation occurs deterministically during `/verify`; post-check identity becomes `MISMATCH`/blocked as required; restoration reproduces the exact checkpoint | DONE — deterministic ARMED→APPLIED→RESTORED verification-mutation hook fires after checks and before the post-check Contract-v1 manifest, proves `MISMATCH`, preserves zero-reviewer behavior, restores the exact checkpoint, and is protected by the static release gate; verified on Windows with 3 bootstrap tests, 9 mechanics tests plus 1 expected Windows mode skip, 11 static-gate tests, 112 forge-script tests (2 skipped), 7 tooling tests, clean diff check, and clean worktree | `139bf4212d4e2ab9467803fb561657ce6600d3f1` |
| H05 | `arbitrary-stage-resume` lacks deterministic preparation/restoration of its seven persisted-state probes | CRITICAL | All seven resume states can be constructed, validated, isolated, scored, and restored deterministically without leaking the expected routing answer to the reasoning context | DONE — seven opaque persisted-state probes use deterministic snapshot/prepare/validate/score/restore mechanics while fresh Luna routing remains probabilistic; stale verification is a real Contract-v1 `MISMATCH`; smoke-ledger access is mechanically denied to the router; Scenario C proves bounded DeepSeek `/implement` handoff acceptance without implementation replay; all requested focused, static, bootstrap, full forge-script, tooling, diff-check, and clean-worktree verification passed locally on Windows | `1d78d1df4bec2abb11f92ea42c722486bd1cc072` |
| H06 | `upstream-rerouting` lacks deterministic blocked-state preparation/restoration | CRITICAL | Required PRD/architecture/project-init/spec/fix authority-boundary cases have reproducible setup, scoring, and restoration without agent-invented fixture state | TODO — NEXT | — |
| H07 | Required human waiver interaction conflicts with the continuously running 30-minute qualification clock | DESIGN BLOCKER | Human authorization, waiting, resume, and qualification-time semantics are explicitly agreed; command/orchestrator/runbook/budget implementation and tests all describe the same behavior; authorization is never fabricated | TODO | — |
| H08 | FULL runtime/invocation budget does not match the authoritative required scenario matrix | DESIGN BLOCKER | Derive the real minimum/expected invocation plan from all required scenarios; runtime target/ceiling and invocation matrix become mutually consistent and realistically executable; no timeout is silently raised | TODO | — |
| H09 | Workspace locate/resume path handling is weaker than create/destroy containment | HIGH | Malformed/traversal run IDs are rejected; create/locate/destroy remain confined to the smoke-run root; negative path-containment tests pass | TODO | — |
| H10 | Mutating deterministic helpers need stronger proof that they target only the disposable smoke repository | HIGH | Every mutating helper fails closed when pointed at the source checkout/wrong branch/wrong repository identity where applicable; valid `smoke-run` behavior remains unchanged | TODO | — |
| H11 | No design-time workflow contract validator / dry orchestration simulator exists | CRITICAL | A cheap deterministic validator walks FAST/FULL contracts and detects missing helper references, invalid state transitions, model/owner mismatch, missing handoff fields, invalid checkpoint/restoration plans, scenario budget violations, zero-reviewer rule violations, and contradictory orchestration instructions before model execution | TODO | — |
| H12 | Final cross-file/system consistency validation is missing | RELEASE GATE | Commands, agents, profiles, fixtures, failure recipes, runbook, helpers, and tests agree; all deterministic/unit/integration gates are green; `git diff --check` is clean; dry FAST/FULL plans are green | BLOCKED by H01–H11 | — |
| H13 | Small real Kilo integration probe is required before another FULL | RELEASE GATE | Minimal model-bearing probe proves real disposable-workspace rooting, child handoff, source isolation, state/timing lifecycle, and interruption-safe cleanup with minimal model spend | BLOCKED by H01–H12 | — |
| H14 | Fresh release-qualifying FULL smoke | FINAL | All required FULL scenarios complete under the agreed qualification contract with no harness defect and with evidence/state consistency intact | BLOCKED by H13 | — |

## Existing deferred work not pulled into this tracker

The following existing item remains intentionally separate unless a tracker
issue proves it must be changed:

- ceremony-bypass support for valid existing upstream authority

Do not expand the current Stable-v0.1 hardening effort into that deferred
feature merely to make FULL smoke easier.

## Status definitions

- `TODO — NEXT` — the only item that should receive implementation work now.
- `TODO` — known work, not yet started.
- `IN PROGRESS` — acceptance gate is fixed and implementation is underway.
- `BLOCKED` — cannot start until the named predecessor/gate is closed.
- `DONE` — invariant demonstrated, tests/review complete, and closing commit
  recorded.
- `DEFERRED` — intentionally postponed with an explicit rationale recorded
  here.

## Next action

Start with **H06 only**.

H01 is closed by merged implementation commit
`9b5bfe0d034d41252fecd9b5ba5b787a5e73c778` and real Kilo probe
`SMOKE-FULL-full-minimal-api-20260928T172150Z-9f874862`.

H02 is closed by merged implementation commit
`4841eb16ca43753db8352e475916192f3b6189ac` after deterministic Windows
verification: 21 focused timing/recovery tests, 87 forge-script tests
(2 skipped), 7 tooling tests, clean diff check, and clean working tree.

H03 is closed by merged implementation commit
`f7164215b7d6fafa87025360de0a7795bf7d2134` after deterministic Windows
verification: 27 state tests, 9 static-gate tests, 3 bootstrap tests, 25
handoff tests, 105 forge-script tests (2 skipped), 7 tooling tests, clean diff
check, and clean working tree.

H04 is closed by merged implementation commit
`139bf4212d4e2ab9467803fb561657ce6600d3f1` after deterministic Windows
verification: 3 bootstrap tests, 9 mechanics tests plus 1 expected Windows
mode skip, 11 static-gate tests, 112 forge-script tests (2 skipped), 7 tooling
tests, clean diff check, and clean working tree.

H05 is closed by merged implementation commit
`1d78d1df4bec2abb11f92ea42c722486bd1cc072` after deterministic Windows
verification: the 13 focused resume-probe tests, static release-gate tests,
bootstrap tests, full forge-script regression suite, tooling suite, diff check,
and clean working tree all passed. GitHub review confirmed one commit ahead,
zero behind, clean/rebaseable merge state, and no review threads before merge.

Do not make H07+ implementation changes in the H06 commit unless they are
strictly necessary to make H06 correct; if such coupling is discovered, record
it before changing scope.
