---
description: Run cost-controlled two-stage production review after deterministic verification
agent: code
model: deepseek/deepseek-flash
---

# Production Review Workflow

Perform the production review pipeline for the requested change or specification and persist the review evidence.

Do not perform the code review yourself.

## Review evidence invariants

- Every non-trivial `/review` run creates a new history-preserving report under `docs/reviews/`.
- Never overwrite a completed prior review report.
- Pre-review findings must be persisted even when the senior reviewer is not invoked.
- Persist reviewer findings faithfully; do not rewrite blocking findings into softer language.
- The review artifact is the authoritative persisted handoff for `/fix`.
- Verification evidence and waivers remain separate artifacts; reference them rather than duplicating or altering their truth.
- Never review implementation state unless Contract v1 reconstruction is `MATCH`. Canonical-manifest equality is authoritative; fingerprint equality alone is insufficient.

## Stage 1 — Determine Review Context

Read and apply `kilo/contracts/implementation-state-evidence-v1.md` as the normative freshness contract.

Identify:

- the intended scope of the change
- the relevant specification
- relevant architecture and ADRs
- the latest **applicable** persisted verification report under `docs/verification/` for this specification/change and branch
- any waiver under `docs/verification/waivers/` that explicitly references that exact verification report and implementation-state fingerprint
- current branch
- current HEAD commit SHA as provenance
- the current implementation-state manifest reconstructed relative to the verification report's base HEAD

Do not load unrelated project documentation.

### Verification Gate

For implementation changes, validate freshness of the applicable persisted verification report before invoking any reviewer.

A verification report is fresh for review only when all of these are true:

- it belongs to the same specification/change being reviewed
- it was produced for the current branch
- it contains every required Contract v1 evidence field
- the verification base HEAD is available
- the current canonical implementation-state manifest can be reconstructed under Contract v1
- reconstruction outcome is `MATCH`

Reconstruct the current manifest using the exact Contract v1 rules, including effective Git mode/type for every identity-bearing path. Compare the reconstructed canonical manifest byte-for-byte with the persisted canonical manifest.

The persisted fingerprint is a compact checksum/identifier and should be checked for internal consistency when practical, but fingerprint equality never substitutes for canonical-manifest equality.

The current HEAD SHA may differ from the verification-time HEAD when the verified working-tree contents were committed after verification. A HEAD change alone does **not** make evidence stale if the reconstructed effective-content fingerprint is identical.

Conversely, the same HEAD SHA does **not** make evidence fresh when working-tree contents changed.

The only paths excluded from this content-freshness comparison are workflow evidence paths:

- `docs/verification/**`
- `docs/reviews/**`
- `docs/diagnostics/**`

Do not treat a globally newest report for another specification, branch, or implementation fingerprint as applicable.

If no applicable persisted verification report exists:

- STOP the review pipeline
- request `/verify` before continuing

Classify freshness as `MATCH`, `MISMATCH`, or `UNRECONSTRUCTABLE`.

If freshness is `MISMATCH` or `UNRECONSTRUCTABLE` because branch/scope/content differs, the base HEAD is unavailable, required evidence is missing/malformed, or reconstruction cannot be proven reliably:

- STOP the review pipeline
- do not invoke `pre-reviewer`
- report the exact freshness outcome and reason
- require the current implementation state to run `/verify` again

If verification is `DONE` with `Delivery Gate: CLEAR`, proceed normally.

If verification is `NOT_DONE`, proceed only when there is a valid active waiver that:

- references the exact verification report
- references the exact implementation-state fingerprint and immutable verification report whose canonical manifest is authoritative
- current Contract v1 freshness outcome is `MATCH`
- covers every failure being accepted
- is unexpired
- is allowed by project policy
- contains explicit human authorization

When such a waiver exists, treat the effective delivery gate as:

`CLEAR_WITH_EXCEPTION`

Pass both the original `NOT_DONE` verification report and the waiver verbatim to reviewers.

If any failed blocker is unwaived, the waiver is stale/expired, or policy prohibits the waiver:

- STOP the review pipeline
- do not invoke reviewers
- report `Delivery Gate: BLOCKED`
- route to `/fix`, `/diagnose`, or a fresh explicit `/waive` decision as appropriate

Never reinterpret a waived failure as a passing check.

Documentation-only, planning-only, or other non-executable changes may proceed without executable verification when such verification is not applicable.

## Stage 2 — Pre-Review

Delegate the review to `pre-reviewer`.

Provide the pre-reviewer with:

- the requested specification or change scope
- relevant architecture/ADR references where available
- the persisted verification report
- any active waiver, verbatim
- effective delivery gate: `CLEAR` or `CLEAR_WITH_EXCEPTION`

The pre-reviewer must independently inspect the Git changes.

Wait for its result.

### If the result is:

`CHANGES_REQUIRED`

STOP the reviewer pipeline.

Do not invoke the senior reviewer.

Persist the review report as required by Stage 4 with:

- pre-review result: `CHANGES_REQUIRED`
- complete pre-review findings
- senior review: `NOT_RUN`
- reason: blocking pre-review findings
- final AI review decision: `CHANGES_REQUIRED`
- next action: `/fix → /verify → /review`

Return the complete pre-review report and persisted review-report path to the user.

State clearly:

`Senior review skipped because blocking issues remain in pre-review.`

The implementation must be corrected with `/fix`, then verified before `/review` is run again.

### If the result is:

`READY_FOR_SENIOR_REVIEW`

Continue to Stage 3.

## Stage 3 — Senior Review

Delegate to `code-reviewer`.

Provide the senior reviewer with:

- the intended change scope
- the relevant specification
- relevant architecture/ADR references
- the persisted verification report
- any active waiver, verbatim
- effective delivery gate
- the complete pre-review report, verbatim and without summarization

Do not rewrite, summarize, reinterpret, or omit findings from the pre-review before passing them to `code-reviewer`.

The senior reviewer must independently validate the implementation.

The pre-review is evidence, not authority.

Do not perform the senior review yourself.

## Stage 4 — Persist Review Evidence and Final Decision

Create exactly one new review artifact for this review run under:

`docs/reviews/`

Use a stable monotonically increasing name scoped to the specification/change when possible:

`REVIEW-<SPEC-ID>-001.md`
`REVIEW-<SPEC-ID>-002.md`

Never overwrite a completed prior review report.

The report must contain:

### Identity

- review ID
- specification/change
- branch
- current HEAD SHA as provenance
- reviewed implementation-state fingerprint
- date/time when available from the environment

### Verification Input

- persisted verification report path/ID
- verification base HEAD SHA
- verified implementation-state fingerprint
- factual verification result
- effective delivery gate
- evidence contract version
- freshness result: `MATCH`, `MISMATCH`, or `UNRECONSTRUCTABLE`
- canonical-manifest equality result
- active waiver path/ID when applicable

### Pre-Review

- result: `READY_FOR_SENIOR_REVIEW` or `CHANGES_REQUIRED`
- complete pre-review findings
- blocking issues
- non-blocking issues
- residual risks

### Senior Review

If invoked:

- result: `APPROVE` or `REQUEST CHANGES`
- complete senior-review findings
- blocking issues
- non-blocking issues
- residual risks

If not invoked:

- result: `NOT_RUN`
- reason

### Final AI Review Decision

Use exactly one of:

- `CHANGES_REQUIRED` when pre-review blocks and senior review is not run
- `APPROVE` when senior review approves
- `REQUEST CHANGES` when senior review requests changes

### Next Action

- for `CHANGES_REQUIRED`: `/fix → /verify → /review`
- for `REQUEST CHANGES`: `/fix → /verify → /review`
- for `APPROVE`: proceed to CI / PR / merge according to project policy

After the artifact is written, return the final review result and the review-report path.

If:

`APPROVE`

report that the AI review gate has passed.

This does not bypass deterministic CI or human production approval.

If:

`REQUEST CHANGES`

the implementation must return to `/fix`, then `/verify`, then `/review`.

## Cost Control

Never invoke the senior reviewer when the pre-review result is:

`CHANGES_REQUIRED`

Do not repeat either review yourself.

Do not invoke reviewers multiple times unless:

- the implementation changed
- verification results changed
- explicitly requested by the user

A new review run after changes or new verification evidence must create a new review artifact rather than editing the previous completed report.

Do not invoke the senior reviewer solely to confirm obvious blocking issues already identified by the pre-reviewer.

## Review Integrity

Do not treat the pre-review as final authority.

Do not treat the senior review as a substitute for deterministic verification.

Do not treat a waiver as proof that a defect is harmless. Reviewers may still return blocking findings when the waiver is unsafe, stale, misclassified, out of policy, or contradicted by the evidence.

Do not suppress, weaken, or reinterpret blocking findings to obtain an approval.

Do not invent defects merely to force a `REQUEST CHANGES` result.

Use the review agents according to their defined responsibilities.

## Authority

The review hierarchy is:

1. deterministic verification provides factual build/test evidence
2. `pre-reviewer` provides inexpensive first-pass quality filtering
3. `code-reviewer` provides authoritative AI merge review
4. `/review` persists the complete review evidence under `docs/reviews/`
5. CI remains the deterministic merge gate
6. human approval remains required for production deployment
