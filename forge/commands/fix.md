---
description: Repair verification or review blockers with the smallest safe corrective change
agent: debugger
model: deepseek/deepseek-flash
---

# Corrective Repair Workflow

Repair implementation issues identified by the latest verification or review result for the requested specification.

This workflow is for corrective work only.

Do not redesign the system.
Do not broaden scope.
Do not re-implement unrelated parts of the specification.

## Purpose

Use this workflow after any of the following:

- `/verify` returns `NOT_DONE`
- pre-review returns `CHANGES_REQUIRED`
- senior review returns `REQUEST CHANGES`
- `/diagnose` returns `DIAGNOSIS_READY` for a defect whose intended behavior is already established

The goal is to:

- inspect the latest blocking evidence
- determine the smallest correct fix
- apply only necessary changes
- preserve the approved specification and architecture
- return control to `/verify`

This workflow does NOT decide completion.

Only `/verify` may return `DONE`.

## Stage 1 — Load Repair Context

Read only the minimum context required to repair the blocker.

Use, in priority order:

1. latest **applicable** persisted review report under `docs/reviews/` for the requested specification/change and branch when repairing review findings
2. latest **applicable** persisted verification report under `docs/verification/` for the requested specification/change and branch when repairing verification failures
3. latest **applicable** diagnosis artifact under `docs/diagnostics/` for the requested defect/change when repairing diagnosed failures
4. requested specification when one governs the change
5. established behavior/contract when repairing an existing defect without a dedicated spec
6. relevant project-level `AGENTS.md`
7. relevant source files
8. relevant tests
9. relevant architecture or ADRs only when needed

Do not scan unrelated parts of the repository.

## Stage 2 — Confirm Repair Scope

Extract the concrete blocking findings from the persisted evidence artifact.

Do not select evidence merely because it is the newest file globally. Match the requested specification/change, branch, and originating failure/review.

If the implementation revision has advanced since that evidence was created, treat the artifact as historical input and first confirm that each blocker still exists in the current code before editing.

Do not rely on chat memory when an applicable persisted review, verification, or diagnosis artifact exists.

For each blocker determine:

- affected file(s)
- likely cause
- whether the issue is a local implementation defect
- whether root-cause debugging is required
- whether the issue indicates an architecture/specification conflict

Do not fix non-blocking suggestions unless explicitly requested or directly relevant to a blocker.

## Stage 3 — Select Repair Mode

### Straightforward Repair

Use a minimal localized fix when the failure is obvious.

Examples:

- syntax or compile error
- missing import
- incorrect method signature
- obvious implementation defect
- lint/format issue
- missing validation required by the spec

### Root-Cause Debugging

Load and apply the `diagnosing-bugs` skill when:

- runtime behavior differs from expected behavior
- failure is intermittent
- concurrency/race issues are suspected
- serialization or dependency-injection failures occur
- integration behavior is unclear
- performance regressed without an obvious cause
- a prior repair attempt did not resolve the same blocker

For these failures, establish a red-capable reproduction for the exact symptom before broad edits. Minimize it, form falsifiable hypotheses, test one variable at a time, and create a regression test at the correct seam when possible.

If a usable feedback loop cannot be built because required environment access or evidence is missing, stop and request the minimum artifact/access needed instead of guessing.

### Architecture or Specification Conflict

STOP if the required fix would need:

- changing the approved technology stack
- introducing a new major dependency
- changing public API contracts outside the specification
- changing persistence strategy
- changing architecture boundaries
- weakening an approved security requirement
- changing consistency/reliability guarantees
- contradicting an ADR
- changing an acceptance criterion
- implementing behavior not supported by the approved specification

Return:

`FIX_BLOCKED`

Do not silently redesign the system.

Use the Blocked Output Contract below to identify the owner, required action, and exact next command.

## Stage 4 — Apply Minimal Corrective Changes

When locally repairable:

- change only files necessary to address the blocker
- follow project-level `AGENTS.md`
- follow the approved specification
- follow architecture and ADR constraints
- preserve existing working behavior
- preserve public contracts unless explicitly required otherwise
- reuse project conventions
- avoid speculative refactoring

## Stage 5 — Test Integrity

Never make a blocker disappear by weakening the gate that detected it.

Never:

- delete failing tests
- skip or quarantine failing required tests without approved justification
- weaken assertions
- lower required coverage/performance/security thresholds
- add warning/lint/analyzer suppressions solely to silence the failure
- alter expected behavior merely to make a test pass
- disable lint rules solely to pass verification
- suppress compiler/static-analysis failures without fixing the underlying issue
- disable security checks
- remove validation
- reduce authorization requirements
- bypass error handling
- replace production behavior with test-only shortcuts

If a test or review finding appears incorrect or conflicts with the approved specification:

STOP.

Return:

`FIX_BLOCKED`

Use the Blocked Output Contract below.

## Stage 6 — Dependency and Tooling Changes

Do not install a new package, runtime, testing tool, linter, scanner, or infrastructure dependency unless:

- it is already approved by the specification/architecture, or
- the user explicitly approves it

If the repair requires a new dependency not previously approved:

STOP.

Return:

`FIX_BLOCKED`

Use owner `USER_APPROVAL` unless the dependency requirement itself indicates an architecture/specification gap.

## Stage 7 — Validate the Repair Locally

After making the corrective change, run only the smallest relevant checks needed to confirm that the specific blocker appears resolved.

The authoritative full verification must still be performed by `/verify`.

Do not return `DONE`.

## Stage 8 — Repair Loop Protection

Avoid repeated blind repair attempts.

If the same blocker remains unresolved after two meaningful repair attempts:

perform explicit root-cause debugging.

If it still cannot be resolved without changing architecture/specification:

return:

`FIX_BLOCKED`

Do not continue consuming tokens with repeated speculative fixes.

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

Explain why this repair cannot safely continue without the decision, correction, approval, or repository action.

### Required action

State the minimum action required to unblock the workflow.

Do not hide a multi-stage upstream correction behind a vague instruction.

### Next command

State the exact next workflow command to run after the required action is complete.

Use one of:

- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`
- `/fix`

Routing rules:

- use owner `PRODUCT` and next command `/prd` when the failure exposes an unresolved or contradictory product requirement
- use owner `ARCHITECTURE` and next command `/architect` when repair requires changing the approved stack, architecture boundary, persistence strategy, reliability/security guarantee, public contract outside the specification, or ADR
- use owner `PROJECT_INIT` and next command `/project-init` when repair is blocked because repository initialization no longer matches the approved architecture
- use owner `SPECIFICATION` and next command `/spec` when the specification or acceptance criteria are ambiguous, contradictory, or incorrect
- use owner `REPOSITORY` and next command `/fix` when repository/environment state must be corrected before the same repair can continue
- use owner `USER_APPROVAL` and next command `/fix` when the repair is otherwise valid but requires explicit approval, such as an unapproved dependency

When an upstream correction invalidates downstream artifacts, make the required rerun path explicit:

- product change: `/prd → /architect → /project-init → /spec → /implement → /verify`
- architecture change: `/architect → /project-init → /spec → /implement → /verify`
- project-init change: `/project-init → /spec → /implement → /verify`
- specification change: `/spec → /implement → /verify`

Do not skip required downstream regeneration after an upstream decision changes.

The final line must be exactly:

`FIX_BLOCKED`

Do not output anything after it.

## Output Format

If corrective changes were made successfully, return:

`FIX_APPLIED`

Then report:

### Blockers Addressed

List the blockers targeted.

### Files Changed

List only files changed by the repair.

### Repair Summary

Briefly explain:

- root cause
- corrective change
- why the change is consistent with the specification and architecture

### Focused Validation

List:

- commands run
- results
- whether the original blocker now appears resolved

### Next Action

Return:

`RUN_VERIFY`

The final line must be exactly:

`RUN_VERIFY`

Do not output anything after it.

## Blocked Output

If the issue cannot be repaired safely:

use the Blocked Output Contract.

The final line must be exactly:

`FIX_BLOCKED`

Do not output anything after it.
