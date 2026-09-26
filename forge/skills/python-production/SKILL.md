---
name: python-production
description: Production Python engineering guidance. Use for Python services, libraries, data/automation code, async code, packaging, typing, logging, error handling, resource management, and pytest-based testing.
metadata:
  source_type: official-doc-grounded
  vendor: Python/PyPA
---

# Python Production Engineering

## Authority

Follow the project's approved Python version, framework, dependency manager, type checker, linter, architecture, and repository instructions.

## Core rules

- Use `pyproject.toml` and the project's approved packaging/dependency workflow.
- Use isolated environments. Do not depend on globally installed packages.
- Add type hints to public and important internal boundaries; use the configured type checker rather than inventing one.
- Prefer small explicit data models over unstructured nested dictionaries when domain structure matters.
- Use context managers for files, locks, sessions, transactions, and other resources.
- Use `asyncio` only when the surrounding stack is asynchronous and the workload benefits from concurrency. Never call blocking I/O in the event loop without an approved offloading strategy.
- Propagate cancellation/timeouts deliberately across async and network boundaries.
- Catch specific exceptions. Do not use broad `except Exception` unless at a top-level boundary with deliberate logging/recovery.
- Preserve exception causality with `raise ... from ...` when translating errors.
- Use the standard logging framework or the project-approved wrapper; never log secrets.
- Avoid mutable default arguments and hidden module-level mutable state.
- Make retries bounded, jittered where relevant, and limited to transient failures.
- Treat serialization, timestamps, decimal precision, encodings, and timezone behavior explicitly.
- Keep import-time side effects minimal.
- Avoid dynamic execution (`eval`, `exec`) and unsafe deserialization for untrusted input.
- Use parameterized database queries.

## Tests and verification

- Use pytest when it is the approved test framework.
- Test behavior and boundaries rather than implementation trivia.
- Cover negative/error cases and important edge conditions.
- Use temporary directories/resources and deterministic fixtures.
- Run the repository-defined formatter, linter, type checker, tests, dependency/security checks, and package build.

## Version-sensitive decisions

Verify Python-version features, packaging metadata, async behavior, framework defaults, and security recommendations against current official Python/PyPA documentation.
