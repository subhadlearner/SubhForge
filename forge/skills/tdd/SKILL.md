---
name: tdd
description: Test-driven development for behavior-bearing code and bug fixes using approved observable seams and thin red-green-refactor vertical slices.
metadata:
  source_type: community-grounded-adaptation
  sources: Addy Osmani and Matt Pocock
---

# Test-Driven Development

Use TDD when behavior can be proven at a stable observable seam.

## Test seam first

Before writing a test, identify the highest stable public/contract boundary that proves the behavior.

Prefer:

- HTTP/API behavior
- event/message handler contract
- domain/application service contract
- persistence adapter contract
- CLI output/exit behavior
- browser/user journey

Avoid private-method tests and mocks of internal collaborators that make refactors fail while behavior remains correct.

## Red → green → refactor

Work in thin vertical slices:

1. write one behavioral test
2. run it and confirm it fails for the intended missing behavior
3. implement the smallest production change that passes it
4. run the focused tests
5. refactor only while green
6. repeat

Do not write a large horizontal suite for imagined future implementation.

## Test quality

A good test:

- proves externally meaningful behavior
- has an independent expected value/source of truth
- survives reasonable internal refactoring
- fails for a real requirement violation
- is deterministic or deliberately controls nondeterminism

Avoid:

- tautological assertions
- snapshots with no meaningful review signal
- over-mocking the behavior under test
- sleeping instead of synchronizing
- testing implementation call counts unless they are themselves a contract

## Applicability

TDD can be `NOT_APPLICABLE` for pure docs, mechanical configuration, generated scaffolding, or work where no meaningful behavioral red test can precede implementation.

Not applicable does not mean tests/verification are optional.
