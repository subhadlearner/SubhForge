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
| H04 | Required `verification-mutation` scenario lacks a deterministic verification-time mutation primitive | CRITICAL | A registered mutation occurs deterministically during `/verify`; post-check identity becomes `MISMATCH`/blocked as required; restoration reproduces the exact checkpoint | IN PROGRESS — deterministic arm/fire/restore identity probe implemented at the smoke `/verify` pre/post-manifest seam; static release gate protects hook/helper presence; local regression execution still required | — |
| H05 | `arbitrary-stage-resume` lacks deterministic preparation/restoration of its seven persisted-state probes | CRITICAL | All seven resume states can be constructed, validated, isolated, scored, and restored deterministically without leaking the expected routing answer to the reasoning context | TODO | — |
| H06 | `upstream-rerouting` lacks deterministic blocked-state preparation/restoration | CRITICAL | Required PRD/architecture/project-init/spec/fix authority-boundary cases have reproducible setup, scoring, and restoration without agent-invented fixture state | TODO | — |
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

Start with **H04 only**.

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

Do not make H05+ implementation changes in the H04 commit unless they are
strictly necessary to make H04 correct; if such coupling is discovered, record
it before changing scope.
