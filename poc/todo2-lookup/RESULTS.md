# TODO-2 — Lookup & resume reliability (Markdown/Git only)

**Date:** 2026-09-26 · **Decision input for:** V0.2.1 §6 / TODO-2 (closed)

## Setup

- `gen_fixture.py` builds a deterministic synthetic LARGE project at two scales:
  - **scale 1:** 8 Epics, 51 Features, 201 Spec files, 20 ADRs, 6.5 MB;
  - **scale 2:** 16 Epics, 101 Features, 401 Spec files, 40 ADRs, 13 MB.
- The artifact bodies deliberately mention other IDs to create realistic grep noise. Records (REC, VERIFY, applicability, ESC, BLK) reference artifacts as a real project would.
- Seeded anomalies: 1 dependency cycle, 1 dangling reference, 1 duplicate ID, lifecycle Case A and Case B, and a `PENDING:` entry whose owner is missing.
- `evaluate.py` compares every approach against a **ground-truth oracle** that parses front matter directly:
  - the **anchored grep** procedure an agent would follow, with answers derived only from grep output;
  - a **naive grep** (`git grep -l <ID>` then reading each hit);
  - the proposed **`kilo_graph.py`** helper.
- Model-input tokens are estimated as stdout characters ÷ 4 (TODO-4 covers exact counts).

## Results (scale 1 → scale 2)

| Task | Approach | Correct | Tool calls (median / max) | Model tokens (median / max) | Latency (median) |
|---|---|---|---|---|---|
| Reverse-dependency lookup (40 samples) | anchored grep | 40/40 → 40/40 | 1 / 1 | 17 / 166 → 22 / 119 | 13 → 24 ms |
| | naive grep | 40/40 → 40/40 | 24 → 22.5 | **2,794 / 4,875 → 2,758 / 5,393** | 32 ms |
| Reconcile closure (20 roots: Specs, Features, ADRs) | anchored grep, agent-driven BFS | 20/20 (see note) | **21 / 210 → 35 / 633** | 184 / 2,778 → 372 / 8,240 | 168 → 560 ms |
| | `kilo_graph closure` | 20/20 → 20/20 | **1 / 1** | 27 / 280 → 52 / 759 | 27 → 35 ms |
| Cycle + integrity scan | raw front-matter scan for the LLM to analyze | n/a (the LLM must compute) | 1 | **19,019 → 37,980** | 10 → 19 ms |
| | `kilo_graph integrity` | all 7 seeded anomaly classes found | 1 | 150 → 150 | 26 → 35 ms |
| Resume `/feature` (artifact + records + children + owed) | anchored grep | — | 4 | 2,316 → 2,372 | 10 → 13 ms |
| Resume `/reconcile` (read the REC package) | read one file | remaining = closure − dispositions | 1 | 853 (99 candidates) → 2,269 (265 candidates) | — |

**Note on grep closure "correctness".** The procedure is logically sufficient, but when its path passes through the duplicate ID it silently walks one of the two files. It scored 20/20 only because the evaluator subtracted the duplicate afterwards. An agent would not notice unless it re-validated identity at every hop. The helper **fails closed**: it returns `blocked: DUPLICATE_ARTIFACT_ID`. This behaviour was added after the first run found 1/20 closures silently incomplete.

## Findings

1. **Single-hop lookups need nothing extra.** Front-matter-anchored `git grep` is exact, takes one call and costs about 20 tokens. This only works because the lists are **single-line flow style** (`depends_on: [A, B]`), so that becomes a locked format rule. Naive grep is 100–150× more expensive, so anchored patterns are mandatory.
2. **Multi-hop queries are the problem, and it is not tokens — it is steps.** Closure BFS needs up to 210–633 tool calls. The planner agent's step budget is 30 (`agents/planner.md`), and every extra step is a chance for an LLM bookkeeping error. Cycle and integrity analysis would mean an LLM reasoning over 19–38k tokens of raw edges, which is unreliable and expensive.
3. **Resume is cheap and needs no store.** `/feature` resume costs about 2.3k tokens in 4 calls at both scales. `/reconcile` resume is one package read (about 0.9–2.3k tokens) and gives the remaining work deterministically. **No checkpoint store or SQLite is justified.**
4. **A tiny read-only calculator solves finding 2.** `kilo_graph.py` (stdlib Python, about 200 lines) takes 1 call, returns 20–760 tokens, runs in about 30 ms, is correct at both scales, and fails closed. It stores nothing and authority stays in Markdown/Git, so none of SQLite's refresh, rebuild or recovery surface applies.
5. **Scaling.** Doubling the project roughly doubles grep BFS calls and scan tokens. Helper cost stays flat in calls and grows only with the answer size.

## Decision (applied to V0.2.1 §6)

- **SQLite: not needed.** There is no measured lookup or resume problem that a store would solve.
- **Adopt `kilo_graph.py`**: a read-only, deterministic calculator for multi-hop queries (`closure`, `cycles`, `integrity`, `order`, `owed`), used by `/reconcile` and `/status`.
- **Single-hop lookups** use the documented anchored `git grep` patterns.
- **Format rule:** `depends_on`, `governed_by` and `exemptions` are single-line flow-style lists.

## Reproduce

```bash
python3 gen_fixture.py /tmp/fx1 1 && python3 evaluate.py /tmp/fx1
python3 gen_fixture.py /tmp/fx2 2 && python3 evaluate.py /tmp/fx2
```
