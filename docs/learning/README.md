# Engineering learning

This directory preserves evidence-backed lessons from building other projects that may improve SubhForge.

## Current source

- [InsightForge learning ledger](insightforge-learning-ledger.md) — reviewed after each completed InsightForge delivery ticket.
- InsightForge repository: https://github.com/subhadlearner/insightforge-agent

## Review protocol

1. After an InsightForge ticket closes, review its issue, merged PRs, implementation evidence, tests and any relevant live-run records.
2. Ask whether something learned could materially improve SubhForge's requirements, workflow, qualification, operating cost, maintainability or agent collaboration.
3. If **nothing transferable** is supported by evidence, report **"No transferable learning identified"** and make no ledger change. A routine ticket closure does not require a new entry.
4. If a lesson qualifies, add an individually traceable `IF-Lnnn` entry with evidence links, observed facts, interpretation, SubhForge implications and a way to validate the proposal. Separate evidence from inference.
5. Bring changes via a small documentation-only PR for review. Avoid duplicate entries; update an existing entry when new evidence sharpens the same lesson.
6. At the end of InsightForge, create a retrospective that synthesizes **validated** lessons, unresolved hypotheses and outcomes.

## Authority boundary

The ledger is **knowledge capital, not an approved SubhForge requirement or design amendment**. Any change to SubhForge behavior must pass the relevant design, reconciliation, human decision and qualification gates. Lessons can be rejected, revised or deferred. Do not equate InsightForge's tooling, architecture or conventions with SubhForge requirements.

Keep the learning docs in this repository, not in generated project templates or global Kilo configuration.
