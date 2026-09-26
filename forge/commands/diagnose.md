---
description: Diagnose difficult runtime, integration, concurrency, intermittent, or performance defects without guessing
agent: debugger
model: deepseek/deepseek-flash
---

# Diagnostic Workflow

Diagnose the reported defect and produce evidence that can drive a safe repair.

This command does not own intended product behavior and does not perform broad redesign.

Load and follow the global `diagnosing-bugs` skill.

## How the User Should Invoke This Command

The user should provide the symptom and whatever evidence is already known. They do not need to identify the root cause.

Prefer including:

- what is going wrong
- what was expected instead
- where it happens
- whether it is intermittent or deterministic
- any known reproduction steps
- relevant error/log text with secrets removed
- a related spec, issue, endpoint, event, test, or recent change when known

Example — concurrency/race issue:

```text
/diagnose

We have a concurrency bug in the create-customer flow.

Observed:
Three POST requests arriving almost simultaneously sometimes create three different customer partition keys even though only one customer should be created.

Expected:
All concurrent requests for the same logical customer should converge on one record according to the existing specification.

Environment:
.NET API using DynamoDB.

Known clue:
Each request appears to perform a read/check first, and all three can observe "not found" before writing.

Please do not jump straight to a fix.
First build the tightest reproducible test or harness for the exact race, minimize it, generate falsifiable hypotheses, and establish the root cause.
```

Example — intermittent integration failure:

```text
/diagnose

Our integration test for order submission fails around 1 in 20 runs.

Observed:
The API returns 202, but the expected downstream event is occasionally not visible before the test times out.

Expected:
The event should be observable within the contractually defined timeout.

I do not know whether the problem is the application, test synchronization, queue/eventual consistency, or environment.

Use the existing spec and repository to establish expected behavior.
Build a red-capable repro before proposing a fix.
```

Example — minimal invocation:

```text
/diagnose

GET /orders/{id} occasionally returns stale status for several seconds after an update.
Expected behavior is defined in SPEC-014.
Please reproduce and establish the root cause before /fix.
```

If the user provides incomplete context, first inspect the repository and relevant artifacts. Ask only for evidence or environment access that cannot be obtained locally.

## Stage 1 — Establish the Symptom Contract

Capture:

- exact user-visible or system-visible symptom
- expected behavior from the spec, contract, existing tests, or established system behavior
- environment/version where observed
- frequency/reproduction clues
- sensitive artifacts that must be redacted

If expected behavior is itself ambiguous, stop and route to the appropriate product/specification authority.

## Stage 2 — Build the Feedback Loop

Create the fastest practical command/harness that can go red on this exact defect.

Prefer:

1. failing automated test
2. focused HTTP/CLI repro
3. browser/E2E repro
4. replayed request/event fixture
5. minimal harness
6. stress/fuzz loop for intermittent failures
7. differential or bisection harness

Run it at least once.

A generic "does not crash" check is not enough; it must detect the reported symptom.

## Stage 3 — Reproduce and Minimize

Confirm the loop reproduces the same defect.

Shrink input, setup, and code path until the remaining parts are load-bearing where practical.

For flaky bugs, improve the reproduction rate enough to make hypothesis testing useful.

## Stage 4 — Hypothesize

Generate 3–5 ranked hypotheses.

Each must be falsifiable:

`If X is the cause, changing/observing Y should produce Z.`

Test one variable at a time.

Use targeted, uniquely tagged temporary instrumentation when needed.

## Stage 5 — Establish Root Cause

A root cause is established only when evidence distinguishes it from the competing hypotheses.

Do not promote correlation or a plausible code smell into a root-cause claim.

## Stage 6 — Regression Strategy

Identify the correct observable seam for a regression test.

If a meaningful regression test can be written, define the failing case that `/fix` should preserve.

If no correct seam exists, record that architectural testability limitation explicitly.

## Stage 7 — Cleanup

Remove temporary instrumentation and throwaway diagnostic changes before finishing unless the user explicitly asks to keep a diagnostic harness.

## Storage

For non-trivial diagnoses, store a concise report under:

`docs/diagnostics/`

Use an ID such as:

`DIAG-001-<short-name>.md`

Include symptom, repro command, minimized case, hypotheses tested, root cause/evidence, regression strategy, and next action.

Never store secrets or unredacted sensitive captures.

## Output

If root cause and repair direction are sufficiently established:

### Next Action

`/fix`

Finish with exactly:

`DIAGNOSIS_READY`

If diagnosis cannot proceed because required environment access, artifacts, or intended behavior are missing, state the minimum blocker and action.

Finish with exactly:

`DIAGNOSIS_BLOCKED`

Do not output anything after the final status token.
