---
name: nextjs-production
description: Production Next.js guidance for App Router applications, Server/Client Components, route handlers, data fetching, caching, streaming, runtime verification, security boundaries, and builds. Use only when the approved framework is Next.js.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: Vercel/Next.js
---

# Next.js Production Engineering

## Authority and versioning

Follow the project's approved Next.js version, router mode, deployment target, package manager, and React version. Next.js changes quickly: verify version-sensitive caching, rendering, middleware/proxy, runtime, and build behavior against current official docs.

## Server and client boundaries

- Prefer Server Components by default in the App Router.
- Add `"use client"` only at the smallest boundary that needs browser APIs, client state, effects, or event handlers.
- Never expose server-only credentials or privileged data through client bundles or serialized props.
- Keep server-only modules behind explicit server boundaries.

## Data and rendering

- Fetch data close to the server component or route that owns it.
- Avoid sequential fetch waterfalls when requests are independent.
- Define cache/revalidation behavior explicitly when freshness matters; never assume historical defaults.
- Use streaming/Suspense where it improves user-perceived latency without complicating correctness.
- Design loading, error, not-found, and empty states.

## Routing and APIs

- Use route handlers for HTTP endpoints only when they are part of the approved architecture.
- Validate all external input.
- Authenticate and authorize server actions/route handlers exactly like other server entry points.
- Preserve idempotency and CSRF/origin protections where the interaction model requires them.
- Keep redirects and status codes deliberate.

## Performance

- Minimize the client JavaScript surface.
- Use framework image/font/script facilities when they fit the project.
- Dynamically load genuinely heavy client-only features.
- Avoid sending large objects from Server Components to Client Components.
- Inspect bundle/runtime behavior rather than assuming a successful type check means the app works.

## Verification

After meaningful UI/runtime changes:
- run the repository's type/lint/test/build checks
- start the approved dev or production server when practical
- exercise affected routes in a real browser/test runner
- inspect server and browser errors
- verify behavior, not just compilation

For React-level performance patterns, also load `react-best-practices`.
