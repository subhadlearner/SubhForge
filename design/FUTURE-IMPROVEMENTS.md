# Future Improvements

This document captures deliberate follow-up ideas that are **not required for Stable v0.1**, but may become valuable as the Kilo workflow framework evolves.

The goal is to preserve design intent and avoid rediscovering the same ideas later without context.

---

## Why specialized smoke fixtures may be needed later

Stable v0.1 intentionally keeps the smoke-fixture registry small:

- `fast-micro-library`
- `full-minimal-api`
- `full-local-persistence-api`

That is deliberate.

The current fixtures are sufficient to validate the framework's core lifecycle and recovery semantics:

- `/grill`
- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`
- `/verify`
- `/diagnose`
- `/fix`
- `/waive`
- `/review`
- `/adversarial-check`

They also exercise:

- review-before-commit
- implementation-state freshness
- stale-evidence rejection
- Git mode/type identity
- repair loops
- diagnosis loops
- waiver flows
- restart/resume behavior
- cost-controlled model routing

Adding more fixtures now would increase:

- planning tokens
- implementation tokens
- verification/runtime cost
- fixture maintenance
- test infrastructure
- duplicated smoke logic

without materially improving confidence in Stable v0.1.

The preferred rule is:

> Add a new fixture only when a framework change cannot be meaningfully validated by the existing fixture shapes.

The ideas below are therefore **future targeted fixtures**, not default smoke projects.

---

# 1. `full-frontend-app`

## Purpose

Add this fixture when framework changes materially affect:

- frontend architecture guidance
- React/Next.js workflows
- browser behavior
- accessibility
- client-side state
- browser routing
- UI error states
- component testing
- E2E/browser testing policy
- frontend-specific review rules

The fixture should validate the workflow against a real browser-facing application shape without turning every FULL_SMOKE run into an expensive E2E suite.

## Suggested product shape

Keep the fixture intentionally small.

Example:

```text
single-page frontend
one form/input interaction
one validation state
one success state
one error state
no authentication
no external backend dependency unless mocked/in-process
no paid API
```

If Next.js is selected during architecture, a minimal route/page can be used.

If React/Vite or another frontend stack is selected, the same product behavior should remain possible.

The fixture should define product behavior, not force a specific framework.

## Minimum useful test surface

Suggested default:

- 1–2 unit/component tests
- accessibility/static checks where configured
- at most 1 focused browser/E2E scenario

Do not create a large Playwright/Selenium matrix by default.

The point is to validate that the framework can correctly determine when browser-level evidence is applicable.

## Workflow capabilities this fixture should validate

Examples:

- architecture recognizes browser/UI concerns
- `/project-init` records frontend commands and relevant skills
- `/spec` correctly identifies component vs browser test responsibilities
- `/implement` uses frontend conventions and accessibility guidance
- `/verify` executes applicable frontend checks
- review inspects UI state/error/accessibility behavior
- E2E is required only where product behavior genuinely crosses browser boundaries

## Useful failure recipes

Potential future smoke scenarios:

### Frontend behavior defect

Example:

- submit button incorrectly remains enabled for invalid input

Expected path:

```text
/verify
→ NOT_DONE
→ /fix
→ /verify
```

### Browser-only defect

Example:

- client navigation works in unit tests but fails in the focused browser path

Expected:

```text
/verify
→ NOT_DONE
→ /diagnose
→ /fix
→ /verify
```

### Accessibility quality failure

A carefully chosen low-risk accessibility/documentation rule could potentially exercise waiver semantics only if project policy explicitly marks it waivable.

Do not use severe accessibility barriers as casual waiver examples.

## When to introduce this fixture

Introduce `full-frontend-app` only after a framework change materially affects one or more of:

- frontend skill routing
- browser/E2E verification policy
- accessibility verification
- frontend code review
- React/Next.js architecture guidance
- client-side error/reliability behavior

## Why it is deferred

Stable v0.1 does not need a browser runtime to prove the core framework lifecycle.

Adding browser automation now would increase installation/runtime cost and test flakiness without improving confidence in evidence freshness, waiver, fix, diagnosis, or orchestration semantics.

---

# 2. `full-event-worker`

## Purpose

Add this fixture when framework changes materially affect:

- asynchronous/event-driven processing
- queues
- retries
- idempotency
- ordering
- duplicate delivery
- concurrency
- eventual consistency
- poison-message handling
- DLQ behavior
- event contracts
- worker observability

This fixture is particularly valuable for validating the workflow's architecture, adversarial-review, diagnosis, and verification behavior around distributed-systems assumptions.

## Suggested product shape

Keep it local and deterministic where possible.

Example:

```text
one event/command
one worker/handler
one in-memory or local queue abstraction
one idempotency key
one observable processed result
one duplicate-delivery scenario
no external cloud queue by default
```

The fixture should model event semantics without requiring AWS SQS, Azure Service Bus, Kafka, or another paid/external broker unless validating those integrations specifically.

## Minimum useful test surface

Suggested:

- 1 normal worker test
- 1 duplicate-delivery/idempotency test
- optionally 1 retry/failure-path test
- no broad distributed load test
- no long-running soak test

## Workflow capabilities this fixture should validate

Examples:

- `/architect` explicitly decides delivery/ordering/idempotency guarantees
- architecture records failure and recovery assumptions
- adversarial review challenges concurrency/data-integrity claims
- `/spec` turns guarantees into deterministic acceptance criteria
- `/implement` does not invent missing consistency semantics
- `/verify` checks duplicate/retry behavior
- `/diagnose` can isolate non-trivial event-flow failures
- `/review` looks for unsafe retry/idempotency behavior

## Useful failure recipes

### Missing idempotency

Inject duplicate delivery so the worker produces duplicate side effects.

Expected:

```text
/verify
→ NOT_DONE
→ /diagnose
→ /fix
→ /verify
```

### Ordering assumption defect

Provide events in a different order than the implementation implicitly expects.

Expected architecture/spec authority should determine whether ordering is guaranteed.

If the guarantee is missing, implementation must not silently choose one.

Potential route:

```text
/verify
→ NOT_DONE
→ /diagnose
→ FIX_BLOCKED
→ /architect or /spec
```

depending on where the missing authority belongs.

### Adversarial scenario

Use a bounded concurrency/idempotency decision to validate:

```text
/adversarial-check
→ findings
→ RECONCILE_ONLY
```

This fixture would be particularly useful for proving that adversarial reconciliation remains narrow.

## When to introduce this fixture

Introduce `full-event-worker` when framework changes affect:

- async architecture rules
- retry/idempotency guidance
- concurrency diagnosis
- event-driven verification
- event contract review
- worker/cloud-event skills

## Why it is deferred

The current fixtures can validate the workflow mechanics without introducing asynchronous nondeterminism.

An event fixture adds meaningful complexity only when the framework itself starts making or validating event/concurrency-specific decisions.

---

# 3. `full-cloud-iac`

## Purpose

Add this fixture when framework changes materially affect:

- AWS or Azure architecture
- infrastructure-as-code
- IAM/security policy
- deployment topology
- networking
- secret/configuration management
- cloud security verification
- cloud cost controls
- observability infrastructure
- deployment/recovery policy

This should be the most carefully controlled and least frequently executed fixture because it has the highest potential runtime and operational cost.

## Suggested product shape

Prefer static/local IaC validation first.

Example:

```text
minimal serverless or managed-cloud service
one deployment unit
one IAM role/policy
one configuration/secret boundary
one log/metric path
no production deployment
no destructive resource lifecycle
```

The fixture should normally validate templates/plans without creating live paid cloud resources.

## Preferred validation layers

Order of preference:

1. static IaC syntax/validation
2. policy/security scanning
3. architecture/ADR verification
4. local/emulated checks only when useful
5. sandbox cloud deployment only when the framework change specifically requires it

Do not provision real infrastructure merely to prove that `/smoke` can call a cloud command.

## Workflow capabilities this fixture should validate

Examples:

- `/architect` treats cloud cost as first-class
- fixed/variable/network/observability costs are documented
- IAM trust boundaries are explicit
- `/project-init` records approved IaC/security commands
- `/spec` includes infrastructure/security acceptance criteria
- `/verify` executes approved IaC/security checks
- review catches dangerous IAM/network/configuration drift
- waiver policy rejects non-waivable cloud security failures
- production deployment still requires human approval

## Useful failure recipes

### Over-permissive IAM

Introduce an intentionally broad permission in a disposable template.

Expected:

```text
/verify
→ NOT_DONE
```

This should normally be treated as non-waivable.

Expected route:

```text
/fix
→ /verify
```

or upstream architecture correction when the policy itself is wrong.

### Cost regression

Change an architecture/IaC choice from a low-fixed-cost service to an unnecessary always-on resource.

Expected:

- architecture/review flags operating-cost implications
- cost is not treated as an afterthought

### IaC validation defect

Introduce a syntax/configuration failure.

Expected:

```text
/verify
→ NOT_DONE
→ /fix
→ /verify
```

### Trust-boundary adversarial check

Challenge cross-account/cross-service IAM or network assumptions.

Expected:

```text
/adversarial-check
→ RECONCILE_ONLY when correction is needed
```

## Safety requirements

This fixture must never:

- deploy to production
- mutate real production resources
- expose credentials
- create destructive policies
- run against privileged accounts by default
- incur uncontrolled spend

If live validation is ever added, it should use an explicitly approved sandbox account/subscription with strict budget and cleanup controls.

## When to introduce this fixture

Introduce `full-cloud-iac` after material framework changes to:

- AWS/Azure architecture skills
- IAM/security-verification behavior
- IaC verification commands
- cloud deployment/recovery workflows
- cloud cost analysis
- network/security architecture review

## Why it is deferred

Stable v0.1 can validate cloud/cost/security **policy presence and routing** statically without provisioning infrastructure.

Adding cloud runtime behavior now would be expensive, slower, harder to reproduce, and more likely to test provider setup rather than Kilo workflow correctness.

---

# 4. Future fixture admission criteria

Before adding any new fixture to `kilo/smoke/fixtures.json`, require all of the following:

1. A real framework capability cannot be adequately validated with an existing fixture.
2. The new fixture has a clearly different product/runtime shape.
3. The scenario provides meaningful additional confidence.
4. The fixture can remain small and disposable.
5. The default test budget is explicitly bounded.
6. Failure-injection recipes are safe and deterministic where possible.
7. The fixture does not hard-code technology decisions that belong to `/architect`.
8. Expected runtime/token cost is justified.
9. FAST/FULL compatibility is explicit.
10. The fixture has a clear trigger explaining when maintainers should select it.

Avoid fixtures that differ only cosmetically.

For example, separate `full-dotnet-api` and `full-python-api` fixtures would usually be a mistake because the language/framework choice belongs to architecture. Add technology-specific fixtures only when the framework behavior itself is technology-specific.

---

# 5. Possible future fixture metadata enhancements

If the registry grows, consider extending each fixture with structured fields such as:

- `risk_domains`
- `required_capabilities`
- `default_test_budget`
- `estimated_token_band`
- `estimated_runtime_band`
- `platform_requirements`
- `supports_mode_type_test`
- `supports_waiver_test`
- `supports_diagnosis_test`
- `requires_network`
- `requires_container_runtime`
- `requires_cloud_sandbox`

This could allow `/smoke` to recommend an appropriate fixture based on the framework files changed.

Example future behavior:

```text
Changes detected:
- frontend skill
- E2E verification policy

Recommended fixture:
full-frontend-app
```

Such automatic recommendation should remain advisory unless fixture selection has been explicitly automated by policy.

---

# 6. Versioning expectation

These fixture additions should be introduced as deliberate framework changes after Stable v0.1.

A future fixture should be added through:

1. registry change
2. runbook update
3. README update
4. fixture-specific failure recipes
5. static validation
6. FAST/FULL profile decision
7. review
8. subsequent framework release/tag

Do not silently add a fixture directly to a stable release without versioned review.

---

# 7. Summary

Potential future fixtures:

| Fixture | Add when | Primary value |
| --- | --- | --- |
| `full-frontend-app` | frontend/browser/E2E workflow behavior changes | UI, accessibility, browser-level verification |
| `full-event-worker` | async/event/concurrency guidance changes | retries, idempotency, ordering, diagnosis |
| `full-cloud-iac` | AWS/Azure/IaC/security verification changes | IAM, IaC, cloud cost/security/recovery |

These are intentionally deferred until they provide real incremental confidence over the current Stable-v0.1 fixture set.
