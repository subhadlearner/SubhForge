# InsightForge → SubhForge learning ledger

Source project: [InsightForge](https://github.com/subhadlearner/insightforge-agent)

Record only individually assessed, evidence-backed candidate lessons from completed InsightForge tickets. Do not add an entry merely because a ticket closed. These entries are **knowledge capital**, not approved SubhForge requirements or design changes.

## Entries

### IF-L001 — Test critical invariants with adversarial counterexamples

- **InsightForge ticket / milestone:** [T6 — Writer, Fact-Checker and citation Passages (#7)](https://github.com/subhadlearner/insightforge-agent/issues/7); [merged PR #28](https://github.com/subhadlearner/insightforge-agent/pull/28).
- **Observation (verified):** The initial T6 implementation passed its reported 679 non-live tests, but independent source review found that the Writer's capitalised-word heuristic skipped sentence-initial words. Replacing the cited Evidence item's subject, `BYD`, with `Tesla` at the beginning of a Claim could therefore evade the named-entity check while preserving the same numbers. The focused correction added sentence-initial checks and regression cases; the owner subsequently ran 681 passing non-live tests, 31 passing T6 acceptance cases, 17 passing pipeline tests, and a clean import-linter check before merging.
- **Evidence:** [Pre-fix Writer at `64609d6`](https://github.com/subhadlearner/insightforge-agent/blob/64609d6443c56d5c34ca7f7cb1af1c444dd4464d/src/insightforge_agent/pipeline/write.py); [fix commit `dc5231f`](https://github.com/subhadlearner/insightforge-agent/commit/dc5231f5e95f4ca20ae164759d0e0114cb7ad782); [regression tests at the fixed commit](https://github.com/subhadlearner/insightforge-agent/blob/dc5231f5e95f4ca20ae164759d0e0114cb7ad782/tests/pipeline/test_t6_writer_fact_check.py). Test counts are from the owner's local verification log, not from an independently reproduced CI run.
- **Interpretation / root cause (hypothesis):** Existing positive and negative cases exercised the known validation rules but missed a simple adversarial subject substitution at a sentence boundary. High test counts alone did not demonstrate that the named-entity invariant held for that case.
- **Transferable lesson:** For important correctness and authorization invariants, pair normal acceptance tests with a few deliberate contract-breaking counterexamples. Reviewers should challenge *how* a rule can be bypassed, not only whether representative inputs pass.
- **Proposed SubhForge application:** Evaluate adding narrowly scoped, deterministic negative probes to existing qualification/smoke scenarios for high-impact contracts, such as unauthorized readiness transitions, invalid artifact/dependency references, or unsupported evidence claims. Do **not** introduce a blanket new test stage or expensive model calls on this evidence alone.
- **How to validate:** Select two or three existing high-risk SubhForge invariants; design one counterexample for each that resembles valid input while violating its contract. Confirm the probe fails before the relevant safeguard (or reliably rejects the injected violation), passes with the safeguard, and measure added runtime and false positives. Adopt only if the defects caught justify the ceremony/cost.
- **Decision status:** **Proposed learning recorded**; no SubhForge workflow, implementation or qualification change approved.
- **Related SubhForge decision:** None identified yet; any adoption requires its normal design/reconciliation and qualification gates.

Assign subsequent entries sequential `IF-Lnnn` IDs. Keep verified observation separate from interpretation, link primary evidence, and update an existing entry rather than duplicating a lesson.
