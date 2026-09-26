---
name: react-best-practices
description: React performance and correctness guidance. Use when writing or reviewing React components, hooks, client/server boundaries, state/effects, data fetching, rendering performance, bundle size, or React code inside Next.js.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: Vercel
---

# React Best Practices

## Data flow and async work

- Avoid serial request waterfalls when independent work can begin concurrently.
- Start independent asynchronous work early and await it near the point of use.
- Do not move data to the client merely to fetch it again.
- Keep request-scoped data request-scoped; avoid mutable module globals for user/request state.

## Components and state

- Derive values during render when they are pure functions of props/state; do not mirror them into effects unnecessarily.
- Use effects for synchronization with external systems, not as a default state-management mechanism.
- Keep effect dependencies correct rather than suppressing linter warnings.
- Use stable keys based on identity, not array position when order can change.
- Keep state as local as practical; lift it only when multiple consumers truly need shared ownership.
- Use refs for mutable values that should not trigger rendering.

## Rendering and performance

- Fix algorithmic/data-flow problems before adding memoization.
- Use memoization when measurement or clear computational cost justifies it.
- Avoid recreating heavyweight providers, data transforms, or component definitions on every render.
- Split expensive or rarely used client code with framework-approved lazy/dynamic loading.
- Minimize data serialized across server/client boundaries.
- Avoid broad barrel imports when they cause large bundles or tree-shaking problems.

## Events and effects

- Put user-action logic in event handlers rather than effects that observe the action indirectly.
- Clean up subscriptions, timers, observers, and listeners.
- Prefer passive listeners for scroll/touch observation when no cancellation is required.
- Use transitions/deferred rendering for non-urgent expensive UI updates when appropriate.

## Review checklist

- no avoidable fetch waterfall
- no unnecessary client boundary
- no effect-derived state
- no unstable list keys
- no leaked listener/timer
- no obvious oversized import
- no sensitive server data serialized to the browser
- rendering optimization is evidence-driven

When the project is Next.js, also load `nextjs-production`.
