---
description: Record a human-authorized, time-bounded verification waiver without changing factual verification evidence
agent: code
model: openai/gpt-5.6-luna
---

# Verification Waiver Workflow

Apply `kilo/contracts/implementation-state-evidence-v1.md` whenever establishing waiver freshness.

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

Confirm that the verification report is `NOT_DONE`.

Identify the exact failed checks/blockers proposed for waiver.

If the requested failure is not present in the referenced verification report:

STOP.

Return:

`WAIVER_BLOCKED`

## Stage 2 — Require Explicit Human Authorization

A waiver requires an explicit user request to accept the risk.

Do not infer authorization from:

- a previous general statement
- an implementation agent's suggestion
- a reviewer suggestion
- the mere presence of a flaky test
- urgency or schedule pressure

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

## Stage 3 — Classify the Waiver

Use one classification:

- `TEST_FLAKINESS`
- `ENVIRONMENT_FAILURE`
- `NON_CRITICAL_QUALITY_GATE`
- `KNOWN_PRODUCT_DEFECT`
- `SECURITY_EXCEPTION`
- `DATA_INTEGRITY_EXCEPTION`
- `COMPLIANCE_EXCEPTION`

If project policy marks a category non-waivable, STOP with `WAIVER_BLOCKED`.

For `SECURITY_EXCEPTION`, `DATA_INTEGRITY_EXCEPTION`, and `COMPLIANCE_EXCEPTION`:

- require explicit acknowledgement of the specific residual risk
- require concrete compensating controls/evidence
- require a short expiry
- do not describe the result as secure, compliant, or safe
- preserve any reviewer/CI/production approval gates

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
