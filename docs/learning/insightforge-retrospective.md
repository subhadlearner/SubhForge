# InsightForge → SubhForge: final capstone retrospective

**Recorded:** 2026-10-22. **Source:** [InsightForge](https://github.com/subhadlearner/insightforge-agent), submitted CodeBasics Cohort #3 capstone. **Destination:** SubhForge v0.2 candidate learning only.

This synthesizes [IF-L001–IF-L012](insightforge-learning-ledger.md). It does **not** amend SubhForge requirements, establish qualification gates or imply that all InsightForge acceptance checks passed.

## What was demonstrated

- An integrated multi-agent Brief-to-Report application was implemented with LangGraph/DeepAgents, FastAPI, Next.js, scheduled Watchlists/Diffs/Alerts, stored evidence, export/share and a reproducible offline test harness. [Merged integration PR #77](https://github.com/subhadlearner/insightforge-agent/pull/77), [README PR #78](https://github.com/subhadlearner/insightforge-agent/pull/78), and [restructure PR #79](https://github.com/subhadlearner/insightforge-agent/pull/79) record the release work.
- The final restructuring verification reported 2,554 passing default backend tests (41 deselected), 19 passing integration tests (12 skipped for unavailable external T18 records), 205 frontend tests, 23 passing browser tests, five import contracts and a package wheel importable in a clean virtual environment. These are mostly offline/scripted checks; warm caches and unavailable historical records limit what the results prove. [T17 verification](https://github.com/subhadlearner/insightforge-agent/blob/main/docs/t17-verification.md).
- A real-model Run from the UI completed and produced a Report and video. This demonstrates a working end-to-end path, *not* reliable answer completeness or passing formal evaluation. [README live runs](https://github.com/subhadlearner/insightforge-agent#live-end-to-end-runs-after-adr-0006).

## What did not qualify

- The five-Brief Anthropic baseline sampled fact-check rate was **20/30 (66.7%)**; formal B-1 and Stage C **FAILED**, and Stage D was **NOT RUN**. The later real UI Run reported 6/11 requirements and did not establish its recommendation despite successful technical completion. [T18 verification](https://github.com/subhadlearner/insightforge-agent/blob/main/docs/t18-verification.md), [T18 issue #19](https://github.com/subhadlearner/insightforge-agent/issues/19).
- Compaction execution was proven under forced offline conditions using the actual dependency middleware, but no live provider compaction was observed. [IF-L009](insightforge-learning-ledger.md#if-l009--prove-framework-managed-behavior-at-its-completion-and-persistence-boundary).
- Some operational behaviors remain deliberately limited or unverified: whole-Run timeout/cost envelope, extraction truncation recovery, local-service test isolation and certain concurrency edges. Retired or deferred work remains tracked in [T20 #49](https://github.com/subhadlearner/insightforge-agent/issues/49) and [post-submission #75](https://github.com/subhadlearner/insightforge-agent/issues/75)/[#76](https://github.com/subhadlearner/insightforge-agent/issues/76).

## Transferable engineering principles

1. **Prove the riskiest user outcome early.** Prefer a small, representative end-to-end slice; add targeted real-provider/semantic evidence if the claim depends on it. Keep the boundary between deterministic orchestration tests and semantic acceptance explicit. [IF-L001, IF-L002, IF-L007, IF-L008]
2. **Challenge alternatives before committing to the architecture.** Freeze the actual correctness criterion and adverse examples before selecting an LLM, deterministic rule or specialized classifier. No untested alternative is presumed superior. [IF-L010]
3. **Treat fixes as changes to invariants, not only changed lines.** Re-check the adjacent state, authority, projection and recovery boundary; preserve durable rediscovery and framework behavior evidence. [IF-L003, IF-L005, IF-L006, IF-L009]
4. **Budget the whole workflow and defend qualification from hidden dependencies.** Count calls, elapsed time, incompleteness and unmeasured cost; distinguish declared test services from incidental localhost state. [IF-L011, IF-L012]
5. **Separate completed, failed, waived and submitted.** An owner may submit a working project with known deficiencies; a submission/issue closure must not retrospectively turn a failed acceptance gate into PASS. Classify accepted limits, deferred risks and missing evidence before growing the backlog. [IF-L004, IF-L008]

## Review when SubhForge work resumes

- At the next v0.2 design/reconciliation checkpoint, **review** (do not automatically implement) IF-L002 and IF-L010 for decomposition/architecture, IF-L003 for the repair loop, and IF-L007/008/011/012 for qualification scope, resource evidence and isolation.
- Select only a few high-risk dogfood scenarios capable of proving or falsifying the proposed improvements. Record observed runtime and coordination burden, and reject additions that create disproportionate ceremony.
- Retain existing SubhForge human authority, artifact immutability and qualification gates. A proposed lesson becomes a requirement only through the normal approved design/reconciliation process.

## Evidence boundary

Claims about local runs, costs and live provider behavior are taken from InsightForge's committed verification records and owner-reported runs; they were not reproduced for this retrospective. Root-cause explanations and SubhForge applications remain proposals. The retrospective is *knowledge capital*, not a claim that SubhForge's implementation has changed.
