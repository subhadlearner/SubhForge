---
description: Record a human-authorized, time-bounded verification waiver without changing factual verification evidence
agent: code
model: openai/gpt-5.6-luna
---

# Verification Waiver Workflow

Apply the installed global `<global-config>/contracts/implementation-state-evidence-v1.md` whenever establishing waiver freshness.

Create a governed exception for a specific failed verification result.

This command never changes verification evidence.

It records a human decision to accept a documented residual risk temporarily.

## Core invariants

- `/verify` remains factual.
- A `NOT_DONE` verification report remains `NOT_DONE`.
- Never edit the verification report to make it green.
- Never delete, skip, quarantine, weaken, or suppress the failed check merely because a waiver exists.
- The failed check should continue to execute in future verification runs.
- A waiver is scoped to an exact verification report, its authoritative canonical implementation-state manifest, implementation-state fingerprint, failure set, and expiry.
- A waiver never authorizes production deployment by itself.
- Human production approval remains separate.
- The agent must not invent the owner's justification or risk acceptance.

## Stage 1 — Load Exact Failure Evidence

Read:

- the latest or explicitly named verification report
- the requested specification
- relevant diagnosis artifact when one exists
- project-level waiver/security policy from `AGENTS.md`
- any authoritative waiver-policy source referenced by `AGENTS.md`, when present

Confirm that the verification report is `NOT_DONE`.

Identify the exact failed checks/blockers proposed for waiver.

If the requested failure is not present in the referenced verification report:

STOP.

Return:

`WAIVER_BLOCKED`

## Stage 2 — Check Failure-Type Policy Eligibility

Before requesting, reading, or waiting for human authorization, read the exact
persisted `Failure Type` for every requested failed check from the loaded verification
report and compare those types against the project waiver policy recorded in `AGENTS.md`
and its referenced authoritative policy source when applicable.

If any requested blocker lacks a persisted `Failure Type`, fail closed before
authorization. Persist a reason-coded blocked record with
`FAILURE_TYPE_UNAVAILABLE` and finish with `WAIVER_BLOCKED`; do not guess the type
from prose or choose waiver eligibility yourself.

If any requested failure type/category is non-waivable:

- do **not** request human authorization
- do **not** start or wait on a `WAIVER_AUTHORIZATION` gate
- persist a reason-coded blocked record under
  `docs/verification/waiver-refusals/`
- use reason code `POLICY_INELIGIBLE`
- finish with `WAIVER_BLOCKED`

This ordering is mandatory. Human willingness to accept risk cannot make a
policy-ineligible failure waivable.

For a policy-eligible request, assign exactly one waiver classification:

- `TEST_FLAKINESS`
- `ENVIRONMENT_FAILURE`
- `NON_CRITICAL_QUALITY_GATE`
- `KNOWN_PRODUCT_DEFECT`
- `SECURITY_EXCEPTION`
- `DATA_INTEGRITY_EXCEPTION`
- `COMPLIANCE_EXCEPTION`

For `SECURITY_EXCEPTION`, `DATA_INTEGRITY_EXCEPTION`, and
`COMPLIANCE_EXCEPTION`, retain the existing stricter treatment:

- require explicit acknowledgement of the specific residual risk
- require concrete compensating controls/evidence
- do not describe the result as secure, compliant, or safe
- preserve reviewer/CI/production approval gates

## Stage 3 — Require Explicit Human Authorization

A policy-eligible waiver requires an explicit user request to accept the risk.
Do not infer authorization from:

- a previous general statement
- an implementation agent's suggestion
- a reviewer suggestion
- the mere presence of a flaky test
- urgency or schedule pressure

### Smoke human-authorization receipt

During a Stable-v0.1 FULL smoke run, live human input cannot cross directly into
the rooted autonomous continuation. The only permitted substitute for a live
Stage-3 user message is the exact persisted authorization attached to a closed
`WAIVER_AUTHORIZATION` interval in that run's deterministic
`<run-id>.budget.json` ledger.

Treat that receipt as explicit human authorization only when all of these hold:

- it was closed by `smoke_budget.py human-wait-authorize`
- its `gate_type` is exactly `WAIVER_AUTHORIZATION`
- its helper-derived `gate_id` still matches the canonical gate identity,
  including the persisted SHA-256 of the exact verification-report bytes
- the current verification-report bytes still match that persisted report digest
- its verification report, Contract-v1 implementation-state fingerprint,
  failure set, and classification exactly match the waiver request being evaluated
- its decision is exactly `ACCEPTED_TEMPORARILY`
- justification, residual risk, compensating control, remediation, and expiry
  are all present
- normal Stage-4 freshness/policy validation still succeeds

Do not treat `WAITING_FOR_USER`, Kilo `--auto`, a smoke blocker, chat history,
or any model-generated prose as authorization. The smoke receipt transports the
human decision; it does not weaken or bypass normal waiver freshness, scope,
classification, expiry, or policy requirements.

Require the human owner to supply or explicitly approve:

- failed verification report ID/path
- exact failure(s) being waived
- failure classification
- justification
- known residual risk
- compensating evidence/control
- remediation action or tracking issue
- expiry date or bounded expiry condition

The agent may help structure these fields, but must not fabricate the owner's justification.

If the requested failures are policy-eligible but explicit authorization is absent,
persist a reason-coded blocked record with `AUTHORIZATION_MISSING` and finish with
`WAIVER_BLOCKED`.

### Machine-readable blocked record

Every blocked waiver attempt that has enough failure evidence to identify the request
must create a new immutable JSON record only under:

`docs/verification/waiver-refusals/`

Never place refusal records under `docs/verification/waivers/`; refusal records are
historical evidence and are never active waivers.

Use a unique attempt filename such as `WAIVER-REFUSAL-<SPEC-ID>-001.json`. Never
overwrite an earlier refusal. The JSON object must contain:

- `schema_version`: `1`
- `status`: `WAIVER_BLOCKED`
- `reason_code`: `POLICY_INELIGIBLE`, `AUTHORIZATION_MISSING`, or another
  documented distinct reason for the actual block
- `requested_failure_ids`: exact requested failed check IDs/names
- `requested_failure_types`: exact failure types/categories when known
- `verification_report`: exact repository-relative report path
- `verification_report_sha256`: SHA-256 of the exact report bytes when available
- `implementation_state_fingerprint`: exact Contract-v1 fingerprint when available
- `classification`: requested waiver classification when known
- `policy_reference`: project policy path/reference when applicable; when
  `AGENTS.md` names an authoritative waiver-policy source, use that exact source
  path rather than `AGENTS.md`
- `policy_sha256`: SHA-256 of the exact bytes at `policy_reference` when applicable
- `authorization_requested`: boolean
- `authorization_receipt_present`: boolean
- `decision_timestamp`: timestamp of this blocked decision

Use JSON `null` for unavailable optional identity values. Never invent a value merely
to fill the schema.

## Stage 4 — Validate Scope and Freshness

The waiver must identify:

- verification report
- specification/change
- branch
- verification base HEAD SHA
- exact implementation-state fingerprint
- exact failed checks
- classification
- approval timestamp/date when available
- expiry
- remediation reference

Before a waiver can be created or reused, reconstruct current implementation state under Contract v1, including Git mode/type identity. Freshness must be `MATCH`. Canonical-manifest equality is authoritative; fingerprint equality alone is insufficient.

If required evidence is missing/malformed, the base HEAD is unavailable, or reconstruction cannot be proven reliably, freshness is `UNRECONSTRUCTABLE` and the waiver must fail closed.

A waiver is stale and invalid when:

- the current branch differs from the referenced verification branch
- Contract v1 freshness is `MISMATCH` or `UNRECONSTRUCTABLE`
- the referenced verification report is not the applicable report for the change under review
- the failed check set changed materially
- the waiver expired
- project policy changed to prohibit it

A commit created after verification does not invalidate the waiver by itself when the effective-content fingerprint remains identical.

A new `/verify` run creates new evidence. Do not silently carry a waiver forward to a new verification report.

## Stage 5 — Persist the Waiver

Create a new artifact under:

`docs/verification/waivers/`

Use a stable name such as:

`WAIVER-<SPEC-ID>-001.md`

Never overwrite a previous waiver.

Required content:

### Identity

- waiver ID
- verification report
- specification/change
- branch
- verification base HEAD SHA
- evidence contract version: `implementation-state-evidence-v1`
- implementation-state fingerprint
- authoritative canonical manifest reference: the immutable verification report

### Failed Check(s)

List the exact failures being accepted.

### Classification

One allowed classification.

### Human Decision

`ACCEPTED_TEMPORARILY`

### Human Justification

Record the user's justification faithfully.

### Residual Risk

State the concrete risk being accepted.

### Compensating Evidence / Controls

Record evidence or controls that reduce, but do not erase, the risk.

### Remediation

Include the required follow-up action or issue.

### Expiry

Record a bounded expiry.

### Scope

State that the waiver applies only to the referenced verification report/canonical implementation-state manifest/implementation-state fingerprint/failure set.

### Verification Truth

Repeat the factual source result:

`Verification Result: NOT_DONE`

### Effective Delivery Gate

When all waiver requirements are satisfied:

`CLEAR_WITH_EXCEPTION`

This means review may proceed with the exception visible.

It does not mean the failed check passed.

## Stage 6 — Review Handoff

Tell the user that `/review` may now consume both:

- the `NOT_DONE` verification report
- the active waiver

The reviewers remain free to identify the accepted risk as a blocking issue when evidence shows the waiver is unsafe, stale, out of policy, or based on an incorrect failure classification.

## Output Status

If a valid waiver is created, finish with exactly:

`WAIVER_APPROVED`

If required human input, evidence, or policy authorization is missing, finish with exactly:

`WAIVER_BLOCKED`

Do not output anything after the status token.
