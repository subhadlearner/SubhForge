---
name: diagnosing-bugs
description: Evidence-first diagnosis for difficult runtime, integration, concurrency, intermittent, and performance defects. Build a tight red-capable feedback loop before root-cause theorizing.
metadata:
  source_type: community-grounded-adaptation
  source: Matt Pocock
---

# Diagnosing Bugs

## Core rule

No red-capable feedback loop, no confident root-cause theory.

The loop must detect the user's exact symptom, not merely show that the system runs.

## Build the loop

Prefer the fastest practical signal:

1. failing test
2. focused HTTP/CLI command
3. browser/E2E assertion
4. captured request/event replay
5. minimal harness
6. stress/fuzz loop for flaky defects
7. differential comparison
8. automated bisection

Run the loop before theorizing.

Tighten it for speed, determinism, and specificity.

## Reproduce and minimize

Confirm the reported symptom.

Remove inputs/setup one at a time until the remaining scenario is close to minimal.

For intermittent bugs, raise the reproduction rate enough to test hypotheses.

## Hypotheses

Generate 3–5 ranked, falsifiable hypotheses.

Each hypothesis must predict an observation:

`If X is the cause, then observing/changing Y should produce Z.`

Change one variable at a time.

Prefer debugger/REPL inspection, then targeted uniquely tagged logs. Do not "log everything".

## Regression

When a correct test seam exists:

1. convert the minimized repro into a failing regression test
2. prove it fails before the fix
3. fix the defect
4. prove the regression test passes
5. rerun the original repro

If no correct seam exists, document the testability limitation rather than adding a shallow false-confidence test.

## Cleanup

Before handing off:

- remove tagged temporary instrumentation
- delete throwaway artifacts unless intentionally kept
- state the evidence establishing root cause
- keep the regression case
