# Source and provenance

Source class: local synthesis grounded in official Next.js/Vercel guidance.

Primary official sources:
- https://nextjs.org/docs
- https://github.com/vercel/next.js

Official upstream skill reviewed:
- repository: https://github.com/vercel/next.js
- path: skills/next-dev-loop/SKILL.md
- pinned canary commit: 579ff601b441a6dd09eb2502c7c06479e3a09595
- repository license: MIT

Imported/curated: 2026-09-18

Local modifications:
- Created a version-agnostic production skill rather than copying `next-dev-loop`.
- Removed hard dependencies on agent-browser and Next.js-specific MCP endpoints.
- Preserved the principle that runtime verification is required beyond compilation.
