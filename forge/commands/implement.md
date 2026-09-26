---
description: Implement an approved specification on its dedicated branch
agent: builder
model: deepseek/deepseek-flash
---

# Implementation Workflow

Implement the requested specification.

This workflow performs implementation work only.

It must follow the approved specification, architecture, ADRs, project instructions, and technology stack.

Do not silently redesign the system.

Do not declare the specification complete.

Completion is determined only by `/verify`.

## Stage 1 — Load Implementation Context

Before modifying code, read only the context required for the requested specification.

Use, in priority order:

1. project-level `AGENTS.md`
2. the requested specification
3. referenced architecture documents
4. referenced ADRs
5. relevant project rules
6. relevant project skills
7. relevant existing source files
8. relevant tests and conventions

Do not scan unrelated parts of the repository.

Do not reload the entire PRD or architecture unless the specification explicitly requires it.

## Stage 2 — Confirm Specification Readiness

Confirm that the requested specification is an approved implementation specification produced from the ready architecture and initialized project context.

If the requested specification is missing, explicitly blocked, materially ambiguous, or not implementation-ready:

STOP.

Return:

`IMPLEMENTATION_BLOCKED`

Do not infer missing scope or acceptance criteria.

## Stage 3 — Confirm Technology Baseline

The implementation must use the approved technology stack recorded by `/architect` and `/project-init`.

Do not independently choose or replace any major technology.

If a required technology decision is missing or conflicts with the specification:

STOP.

Return:

`IMPLEMENTATION_BLOCKED`

Explain:

- the missing or conflicting decision
- why implementation depends on it
- the minimum architecture/specification clarification required

Do not guess.

## Stage 4 — Branch Safety

Before modifying source code:

1. determine the current Git branch
2. inspect working-tree status
3. confirm the requested specification has a dedicated implementation branch

Do not implement directly on:

- `main`
- `master`
- `develop`
- `release`
- any repository-defined protected integration branch

Preferred branch naming:

`spec/<spec-id>-<short-description>`

If the current branch is protected and the required implementation branch does not exist:

create the dedicated specification branch before implementation.

If an appropriate specification branch already exists:

switch to and use that branch.

Do not create multiple branches for the same implementation unnecessarily.

### Uncommitted Changes

If unrelated uncommitted changes would be mixed into the requested implementation:

STOP.

Do not:

- stash unrelated work automatically
- discard unrelated changes
- reset the repository
- overwrite unrelated files

without explicit user approval.

Return:

`IMPLEMENTATION_BLOCKED`

and explain the conflicting working-tree state.

### Parallel Implementation

When multiple specifications are being implemented concurrently:

- use a separate branch for each specification
- use a separate Git worktree for each concurrently mutating implementation
- do not allow multiple implementation agents to edit the same files concurrently

Do not create a worktree when the implementation is not actually running in parallel unless project policy requires it.

## Stage 5 — Confirm Specification Scope

Extract the implementation scope from the requested specification.

Do not implement requirements outside the approved specification.

If the specification conflicts with architecture or ADRs:

STOP.

Return:

`IMPLEMENTATION_BLOCKED`

Describe the conflict rather than silently choosing one interpretation.

## Stage 6 — Plan the Minimal Implementation

Before editing, determine the smallest production-grade change that satisfies the specification.

Prefer:

- existing project patterns
- existing abstractions
- existing dependencies
- incremental changes
- reversible changes
- simple designs

Avoid:

- speculative abstractions
- premature extensibility
- unnecessary new services
- unnecessary new dependencies
- unrelated refactoring
- broad repository cleanup
- architecture changes disguised as implementation

## Stage 7 — Select Test-First Mode

Read the specification's testing strategy and test seams.

If the specification states `TDD: APPLICABLE`, load the global `tdd` skill and implement behavior in thin red → green vertical slices:

1. write one failing behavioral test at an approved seam
2. run it and confirm it fails for the intended missing behavior
3. implement only enough production code to make that test pass
4. repeat for the next behavior
5. refactor only while keeping the suite green

Do not write a large imagined test suite up front.

If the specification states `TDD: NOT_APPLICABLE`, follow the reason given and still implement all required deterministic tests/checks.

If behavior-bearing code has no TDD decision and a stable test seam is obvious, prefer TDD. If the specification explicitly requires TDD but does not define a usable seam, return `IMPLEMENTATION_BLOCKED` with owner `SPECIFICATION` and next command `/spec` rather than inventing brittle private-method tests. If TDD was not required, proceed with the specification's normal testing requirements.

## Stage 8 — Implement the Specification

Implement only the requested specification.

Follow:

- project-level `AGENTS.md`
- approved architecture
- ADRs
- project rules
- applicable skills
- existing repository conventions

Where applicable:

- validate inputs
- handle expected failures
- preserve security boundaries
- preserve public contracts
- preserve backward compatibility when required
- use project logging/observability conventions
- handle cancellation/timeouts where relevant
- handle retries/idempotency where required
- use safe concurrency patterns where required

## Stage 9 — Dependencies

Reuse existing dependencies whenever practical.

If implementation requires a new major dependency not covered by the approved design:

STOP and request approval.

## Stage 10 — Implement Required Tests

Add the tests required by the specification.

Use the appropriate combination of:

- unit tests
- integration tests
- contract tests
- E2E tests
- negative tests
- boundary tests
- security tests

Do not weaken existing tests, assertions, quality thresholds, analyzers, or security gates to obtain a pass.

## Stage 11 — Focused Implementation Validation

During implementation, run focused checks as needed.

These checks are for implementation feedback only.

Do not treat them as final verification.

The authoritative verification workflow is `/verify`.

## Stage 12 — Handle Local Failures

If focused checks fail because of an implementation defect:

attempt a minimal corrective change.

Do not repeatedly perform speculative repair loops inside `/implement`.

If the implementation appears complete, return control to `/verify`.

If `/verify` later returns `NOT_DONE`, repair belongs to `/fix`.

## Stage 13 — Architecture and Specification Guardrail

STOP if implementation would require:

- changing the approved technology stack
- changing persistence strategy
- changing public API contracts outside the specification
- changing architecture boundaries
- changing approved consistency guarantees
- changing reliability guarantees
- weakening security requirements
- changing an ADR
- changing acceptance criteria
- introducing materially different infrastructure

Return:

`IMPLEMENTATION_BLOCKED`

Do not silently redesign the system.

## Stage 14 — Implementation Completion

When implementation work for the requested specification is finished:

do not return `DONE`.

The next authoritative step is:

`/verify`

Return:

`IMPLEMENTATION_READY_FOR_VERIFY`

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

Explain why this stage cannot safely continue without the decision or correction.

### Required action

State the minimum action, clarification, or correction required to unblock the workflow.

### Next command

State the exact next workflow command to run after the blocker is resolved.

Use only one of:

- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`

If a user clarification or repository cleanup must happen first, say so in `Required action`, then name the command to rerun in `Next command`.

The final line must be the workflow's blocked status token and nothing may appear after it.

## Output Format

### Specification

State the specification implemented.

### Branch

Report:

- current branch
- whether a new specification branch was created
- worktree used, if applicable

### Files Changed

List only files changed for the requested specification.

### Tests Added or Changed

List applicable tests.

### Implementation Summary

Briefly explain:

- what was implemented
- important design choices
- relevant architecture/ADR constraints followed

### Commands Executed

List focused commands run during implementation.

### Unresolved Issues

List unresolved issues.

If none:

`None.`

### Next Action

Return:

`RUN_VERIFY`

The final line must be exactly:

`RUN_VERIFY`

Do not output anything after it.

## Blocked Output

If implementation cannot safely continue, use the Blocked Output Contract.

Routing rules:

- use owner `REPOSITORY` and next command `/implement` when the blocker is branch, worktree, unrelated uncommitted changes, missing local tooling, or other repository/environment state
- use owner `SPECIFICATION` and next command `/spec` when the specification is missing, ambiguous, internally inconsistent, or conflicts with its own acceptance criteria
- use owner `ARCHITECTURE` and next command `/architect` when implementation would require changing the approved stack, architecture boundaries, persistence strategy, public contracts outside the spec, reliability/security guarantees, or an ADR
- use owner `USER_APPROVAL` and next command `/implement` when an otherwise valid implementation requires explicit approval, such as an unapproved new dependency

When the blocker requires an upstream architecture change, make clear in `Required action` that the normal downstream path after architecture is:

`/architect → /project-init → /spec → /implement`

When the blocker is specification-only, the normal path is:

`/spec → /implement`

When the blocker is repository state or user approval, resolve it and rerun:

`/implement`

The final line must be exactly:

`IMPLEMENTATION_BLOCKED`

Do not output anything after it.
