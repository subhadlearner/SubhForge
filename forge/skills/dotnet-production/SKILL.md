---
name: dotnet-production
description: Production engineering guidance for C#/.NET and ASP.NET Core. Use when writing, reviewing, debugging, or designing .NET application code, APIs, background services, dependency injection, configuration, logging, async flows, resilience, or tests.
metadata:
  source_type: official-doc-grounded
  vendor: Microsoft
---

# .NET Production Engineering

Use this skill for implementation-quality decisions in C#/.NET projects.

## Authority

Follow the project's approved runtime, framework, packages, architecture, ADRs, and `AGENTS.md`. This skill does not authorize changing them.

## Core rules

- Enable nullable reference types and treat warnings/analyzer findings according to project policy.
- Prefer clear domain types and explicit contracts over loosely typed dictionaries or magic strings.
- Use asynchronous APIs for I/O. Propagate `CancellationToken` through public async boundaries where cancellation is meaningful.
- Do not wrap naturally asynchronous I/O in `Task.Run`.
- Avoid sync-over-async such as `.Result`, `.Wait()`, and blocking locks around async work.
- Use DI lifetimes deliberately. Never capture scoped services in singletons.
- Use the Options pattern for structured configuration. Validate critical configuration at startup when practical.
- Keep secrets outside source control; use the project's approved secret provider.
- Use `IHttpClientFactory` or an approved typed-client pattern for outbound HTTP; set explicit timeouts and avoid unbounded retries.
- Treat retry, timeout, circuit-breaker, and idempotency behavior as architecture concerns. Retry only transient failures and avoid retry amplification.
- Use structured `ILogger` logging with stable message templates. Do not log secrets, tokens, credentials, or unnecessary personal data.
- Prefer exception handling at meaningful boundaries. Do not catch exceptions only to rethrow without added context or policy.
- Dispose `IDisposable`/`IAsyncDisposable` resources correctly; prefer `using`/`await using`.
- Keep ASP.NET Core composition roots thin. Put business behavior in testable application/domain components.
- Validate external input at the boundary and return deliberate, consistent error responses.
- Preserve thread safety. Avoid shared mutable state unless synchronization and lifecycle are explicit.
- Measure before micro-optimizing; pay attention to allocations only on demonstrated hot paths.

## Tests and verification

- Unit-test deterministic business behavior.
- Use integration tests for framework wiring, persistence, serialization, auth, and external boundaries where applicable.
- Prefer real framework test hosts and lightweight fakes over excessive mocking.
- Run the repository-defined restore, build, test, format, analyzer, and security checks.
- Do not suppress warnings or weaken tests just to obtain a green build.

## Version-sensitive decisions

Before relying on runtime support policy, package behavior, ASP.NET defaults, SDK APIs, trimming/AOT constraints, or security guidance, verify against current Microsoft documentation.
