# SubhForge Stable v0.1 — H08 Consolidated Design v6

- **Title:** Segmented FULL qualification, H08/H08b delivery split, policy-first waiver behavior, deterministic early-probe scoring, and auditable provisional budgeting
- **Date:** 30 September 2026
- **Status:** AGREED DESIGN AUTHORITY — committed for H08/H08b delivery; implementation not started
- **Supersedes:** Earlier off-repository design drafts v1–v5; this v6 is the only working H08 design authority
- **Repository audited:** `subhadlearner/SubhForge`, integration snapshot `2568372b675b1ed309dc636e619fb0c31d427424`
- **Primary authorities:** `forge/smoke/profiles.json`, `forge/smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md`, `forge/smoke/STABLE-V0.1-FULL-HARDENING-TRACKER.md`, H01–H07 helpers, `forge/commands/grill.md`, `forge/commands/waive.md`, `forge/scripts/project_init_mechanics.py`, and `forge/smoke/failure-recipes.json`. Existing command behavior is distinguished from agreed H08b changes throughout.

> **Reading rule:** Complete replacement, not an appendix. **AGREED** means decided in the design discussion; **PROVISIONAL** means a concrete implementable initial hypothesis requiring recorded validation; **CONDITIONAL** means its stated prerequisite must be demonstrated before claiming its cheaper call count. This document does not assert that v6 has already been implemented, update GitHub, authorize a PR merge, or certify empirical runtime feasibility.

---

## 1. Objective, final scope split, and controlling principles

The former FULL contract targeted 25 minutes with a 30-minute hard continuous active-time ceiling. Its original planning summary counted 21 calls; the later authoritative matrix already requires 45 on a successful material-reconciliation path, before three additional early-lifecycle calls and two missing Luna behavioral checks. Direct history shows the old continuous target was untenable for the previously tested execution shape.

**AGREED:** Keep **one logical FULL qualification** with **six sequential, checkpoint-bound, independently timed segments**, with all **24 required scenario IDs** preserved. The qualification's configured per-segment limits and actual charged time have a derived aggregate total. Exclude only validated H07 authorization waits *within* a segment, and explicit restricted gaps *between* committed segments. A segment timeout disqualifies the entire qualification; no failed-segment retry can later produce PASS for the same qualification.

### 1.1 Two coherent implementation items

| Item | Responsibility | Does not own |
|---|---|---|
| **H08 — Segmented qualification infrastructure** | Six-segment configuration, versioned invocation specification, exact H03 canonical lifecycle and pinned-by-value budget contract, H02/H07 integration, ledger/evidence digests, helper-enforced open/close and clocks, boundary-gap enforcement, basic configuration validation, worksheet-derived positive PROVISIONAL limits and corresponding deterministic tests | Building the new model-bearing behavioral probes; full H11 validation; executing a release FULL |
| **H08b — Missing behavioral acceptance probes and narrow command corrections** | Real evidence/access-blocked-and-resumed `/grill`, blocked/resumed PRD, user-selected clear-intent PRD *without* discovery, real Luna project-init blocked behavior, normal `/grill` output with stable per-decision IDs, hidden deterministic scoring against protected expectations, fixed-from-bootstrap fixture waiver policy, live Luna non-waivable refusal, and the explicit `/waive` policy-before-authorization **plus persisted machine-readable blocked-reason** correction; static-gate and behavioral protection. Demonstrate S2 failed-report reuse before closing H08b. | General segment infrastructure, full workflow validator, changing H07 risk-authorization rules |

H08 declares *all* H08b calls, the S1 evidence/access blocker and normal-command decision-ID contract, the S2 machine-readable waiver-refusal record, the fixed-policy S2 report-reuse prerequisite, and the updated authoritative direct-fix matrix sequence *in advance*, so H08b executes an existing contract rather than redefining the budget. H08 and H08b are independently reviewable PRs; both are required before H11 validation. The tracker requires two rows and an explicit H08b dependency. H09/H10 stay separate, H11 owns the comprehensive validator, H12 the final deterministic system gate, H13 the small integration/calibration probe, and H14 the release-qualifying FULL.

### 1.2 Scope and terminology

- **Substantive call:** one real delegated child-model invocation, not an orchestration decision or deterministic helper. Orchestrator work still consumes active segment time.
- **One-pass working baseline:** model calls planned on the declared successful path, excluding interrupted/recovered reattempts and optional paid Claude.
- **Conditional call:** allowed only under a machine-readable documented condition; a segment budget must reserve for *every permitted applicable branch*, not just the cheapest one.
- **Checkpoint:** a label plus exact Git/worktree identity, applicable Contract-v1 implementation-state manifest/fingerprint, and separately protected accepted historical evidence. Equal labels alone are not equality.
- **Segment timeout:** terminal qualification failure. An already-running child is allowed to return but cannot rehabilitate the exceeded limit.

**Explicit exclusions:** parallel fan-out, general timing-framework construction, changing H05/H06 hidden scoring, bypassing real model decisions, extra paid Claude by default, broad H09–H14 implementation, or assuming an unverified checkpoint/evidence restore is valid.

---

## 2. Direct historical evidence and how to use it

A previous console transcript for `SMOKE-FULL-full-minimal-api-20260927T053841Z-2f955f11` recorded approximately:

| Cumulative milestone | Time |
|---|---:|
| Discovery ready | 4m00s |
| PRD ready | 6m21s |
| Architecture and project initialization ready | 11m15s |
| Spec ready | 15m07s |
| Implementation ready | 18m41s |
| First verification ready | 22m48s |
| Pre-review ready | 27m26s |
| Senior reviewer returned / budget exhausted | About 30m30s |

These are **cumulative wall-clock intervals between reported budget checks**. They contain model work **and** orchestrator/tool/mechanics overhead. The senior reviewer apparently returned before the overrun was reported, but its exact completed `stage_invocations` duration has not been independently recovered. Treat roughly 3 minutes as a historical **combined interval**, not a verified model-only measurement.

An earlier run reportedly exceeded 66 minutes. Its original ledger has not been located; record that as **historically reported / raw timing pending**, not as calibrated evidence.

The accepted deterministic regression-suite baseline after H07 is **238.704 seconds**. It measures developer tests, **not** FULL qualification execution and must not be inserted into the FULL budget calculation.

**Calibration policy:** Reuse any available raw `stage_invocations` data first. For transcript-derived durations, treat the interval as inclusive of observed mechanics; **do not add the same mechanics a second time**. Derive inter-call gaps from existing start/end timestamps. Missing class measurements remain declared assumptions until calibrated.

---

## 3. Complete call-count reconciliation

### 3.1 Legacy 21 → authoritative matrix 45

| Legacy workstream | Sol | Luna | DeepSeek | Total |
|---|---:|---:|---:|---:|
| Initial discovery → first ready senior review | 5 | 1 | 3 | 9 |
| Direct repair before later review was specified | 0 | 0 | 3 | 3 |
| Diagnosis recovery before later review was specified | 0 | 0 | 4 | 4 |
| Safe waiver through pre-review | 0 | 1 | 2 | 3 |
| Material adversarial challenge and reconciliation | 1 | 0 | 1 | 2 |
| **Original one-pass summary** | **6** | **2** | **13** | **21** |

| Work added by the later authoritative matrix | Sol | Luna | DeepSeek | Added |
|---|---:|---:|---:|---:|
| Direct-fix pre-review and ready senior | 1 | 0 | 1 | 2 |
| Diagnosis pre-review and ready senior | 1 | 0 | 1 | 2 |
| Waiver ready senior review | 1 | 0 | 0 | 1 |
| Independent verification-time mutation | 0 | 0 | 1 | 1 |
| Independent pre-review blocker | 0 | 0 | 1 | 1 |
| H05 seven fresh resume decisions plus bounded handoff | 0 | 7 | 1 | 8 |
| H06 three planning/five fix classifications plus bounded handoff | 4 | 0 | 5 | 9 |
| **Matrix additions** | **7** | **7** | **10** | **24** |

**Authoritative matrix one-pass path: 45 = 13 Sol + 9 Luna + 23 DeepSeek.** It includes all four ready senior reviews (initial, direct fix, diagnosis and waiver), real material finding/reconciliation, seven H05 classifications/one handoff, eight H06 classifications/one handoff. The optional adversarial recheck adds one DeepSeek, producing 46 when actually permitted. These are successful-path counts, not unconditional mandatory reviewer calls when an earlier gate is blocked.

### 3.2 Additional acceptance obligations: +3 Sol and +2 Luna

| Additional test within existing scenario | Placement | Extra call | Precisely scored evidence |
|---|---|---|---|
| First **evidence/access-blocked** `/grill`, then resumed ready discovery | S1 / `grill` | **+1 Sol AUTHOR** | Mainline discovery requires two calls. Mechanically withhold a required referenced fact/artifact or access to it, **not** an unanswered product decision. Bootstrap seeds an approved partially settled `DISC-001` containing genuine settled decisions with stable IDs **before** the first `/grill`. The first run must return `DISCOVERY_BLOCKED` specifically for missing evidence/access; score the seeded decisions for preservation **after both the blocked call and the resumed call**, whether or not the blocked call writes anything. Restore only the missing approved evidence and resume once. |
| **User-selected clear-intent PRD with no discovery artifact** | S1 / `grill` skip-eligibility subprobe | **+1 Sol AUTHOR `/prd`** | Explicit fixture/user instructions direct a separate clear-intent path immediately to PRD. Score real PRD success **with no discovery artifact**, never a supposed autonomous model decision to skip. |
| First blocked `/prd`, then resumed ready PRD | S1 / `prd` | **+1 Sol AUTHOR** | Mainline PRD requires two calls rather than one. The first returns `PRD_BLOCKED`; reveal only the approved withheld answer, then validate resumed readiness. |
| Unavailable evidence contract, real project-init owner stops | S1 / `project-init-contract-propagation` | **+1 Luna PROJECT_INIT** | Mechanical `ProjectInitError` and independent Luna `PROJECT_INIT_BLOCKED`; Luna must not invent a substitute contract. |
| Existing behavioral-test failure is prohibited by fixed project policy | S2 / direct-fix negative subprobe | **+1 Luna WAIVER_NEGATIVE** | Luna reads the **unchanged bootstrap/project-init policy** and the genuine `NOT_DONE` behavioral/unit-test failure report already created by S2. The corrected normal `/waive` command rejects it *before* authorization, persists a blocked record with `reason_code=POLICY_INELIGIBLE` and exact report/policy identity, and ends in the existing bare `WAIVER_BLOCKED` status. A rejection for `AUTHORIZATION_MISSING` does **not** pass this probe. |
| **Total new calls** | | **3 Sol + 2 Luna** | |

**AGREED one-pass baseline: 50 = 16 Sol + 11 Luna + 23 DeepSeek.** The single permitted optional adversarial recheck yields **51 = 16 Sol + 11 Luna + 24 DeepSeek**. There is **no planned separate waiver verification** or alternate invocation branch.

**Mandatory prerequisite rather than conditional hidden spend:** Before H08b declares success, it must demonstrate that the S2 direct-fix `NOT_DONE` verification report documents a failing behavioral/unit check classified by the project's already-effective non-waivable *failure-type* policy. The same policy must be present in the bootstrap fixture, installed/recorded by project-init, and unchanged before, during and after verification. If this prerequisite fails, H08b fails closed and raises a recorded scenario-design/configuration revision; the orchestrator cannot add an undeclared verification call or edit policy after verification to make the test pass.

**Accepted normal-command coupling:** H08b changes normal `/grill`, `/verify`, `/project-init`, `/waive`, and `/review` only as required by the accepted probes. `/grill` persists stable decision IDs/states; `/verify` persists factual bounded failure types; `/project-init` preserves the fixed waiver-policy identity and canonical-contract/refusal setup; `/waive` moves exact failed-evidence/policy eligibility before authorization and persists reason-coded refusals; `/review` excludes refusal history from active-waiver discovery. An ineligible failure persists `POLICY_INELIGIBLE` and returns `WAIVER_BLOCKED` without authorization; missing authorization for an otherwise eligible request records `AUTHORIZATION_MISSING`, and unavailable failure-type evidence records its own distinct reason. Static and focused tests protect these contracts, while fresh scorer-hidden Luna children prove actual project-init/waive behavior. H07's accepted human receipt and wait semantics remain unchanged for *eligible* S4 waiver requests.

### 3.3 Count boundaries and other zero-call cases

- `project_init_mechanics.prepare()` raising `ProjectInitError` proves helper behavior only, not Luna's `PROJECT_INIT_BLOCKED`; hence +1 real Luna.
- The S2 behavioral-test report is independently generated by the **already budgeted direct-fix verification**. Its genuine non-waivability is established by immutable failure-type policy set before that verification, so its Luna policy refusal adds exactly one Luna and zero extra DeepSeek calls.
- Policy eligibility is determined **before** authorization. The S2 negative is scored against the persisted `POLICY_INELIGIBLE` record, not against the ambiguous terminal status alone. `AUTHORIZATION_MISSING` is a failing outcome for this test, and no H07 human wait may open for an ineligible failure.
- Deterministic freshness, malformed-evidence and restoration probes add zero reviewers under the later authoritative runbook §3.5.
- The separate pre-review-blocker scenario uses one DeepSeek and **zero** senior calls; the normal direct-fix scenario independently demonstrates a repaired-and-reviewed path.
- H06's accepted eight classifications and one bounded handoff meet the routing-focused contract, not eight full downstream regenerations.
- Genuine interrupted/recovered invocations remain individually recorded and consume the same segment clock; they are not included in one-pass 50/51 arithmetic.
- Optional paid Claude requires separate explicit permission and is excluded from 50/51.

## 4. Canonical 24-scenario invocation ledger and six-segment totals

The FULL profile's existing 24 required IDs are preserved. Additional checks below are *subprobes*, not new top-level IDs. Exactly eight top-level scenarios remain zero-substantive-call scenarios; the other sixteen contain the model-bearing plan.

| Seg. | Required FULL scenario | Sol | Luna | DeepSeek | Baseline calls | Required detail |
|---|---|---:|---:|---:|---:|---|
| S1 | `static-release-gate` | 0 | 0 | 0 | 0 | Deterministic; S1 clock already active |
| S1 | `grill` | 3 | 0 | 0 | 3 | **Evidence/access-blocked** then resumed discovery = 2 Sol; normal `/grill` artifacts use stable per-decision IDs; hidden scorer verifies previously settled decisions remain settled. Separate user-directed no-discovery `/prd` branch = 1 Sol; never score autonomous skipping |
| S1 | `prd` | 2 | 0 | 0 | 2 | Blocked/resumed main PRD; skip-branch PRD counted above exactly once |
| S1 | `architect` | 1 | 0 | 0 | 1 | Original authoring; authority blocker tested by H06 |
| S1 | `project-init-contract-propagation` | 0 | 2 | 0 | 2 | Successful Luna init records fixed failure-type waiver policy and synchronizes contract; independent unavailable-contract Luna rejection and deterministic `prepare()` failure also required |
| S1 | `spec` | 1 | 0 | 0 | 1 | Original authoring; upstream blocker tested by H06 |
| S1 | `implement` | 0 | 0 | 1 | 1 | Real DeepSeek implementation |
| S1 | `first-uncommitted-verify` | 0 | 0 | 1 | 1 | Real uncommitted verification |
| S1 | `review-before-commit` | 1 | 0 | 1 | 2 | Ready DeepSeek pre-review plus Sol senior |
| S2 | `identical-commit-freshness` | 0 | 0 | 0 | 0 | Reversible isolated commit and retained historical evidence |
| S2 | `content-mutation-stale-evidence` | 0 | 0 | 0 | 0 | Deterministic copied/restored negative |
| S2 | `mode-type-identity` | 0 | 0 | 0 | 0 | Deterministic/platform-qualified negative |
| S2 | `verification-mutation` | 0 | 0 | 1 | 1 | One DeepSeek verify and exact restoration |
| S2 | `direct-fix-loop` | 1 | 1 | 4 | 6 | **Updated authoritative matrix sequence:** DeepSeek failed `/verify` → real Luna negative `/waive` with protected `POLICY_INELIGIBLE` blocked record → DeepSeek `/fix` → DeepSeek fresh `/verify` → DeepSeek pre-review → ready Sol senior. Same pre-existing failure-type policy throughout; zero H07 wait and no fallback verify. |
| S2 | `malformed-evidence` | 0 | 0 | 0 | 0 | Deterministic copied-evidence negative |
| S2 | `evidence-exclusion` | 0 | 0 | 0 | 0 | Deterministic exact identity exclusions |
| S3 | `diagnose-fix-loop` | 1 | 0 | 5 | 6 | Verify, diagnose, fix, verify, pre-review, ready senior |
| S4 | `waive-review-loop` | 1 | 1 | 2 | 4 | Safe human-authorized waiver, pre-review and ready senior |
| S4 | `stale-waiver` | 0 | 0 | 0 | 0 | Directly consumes preceding waiver state; no model reviewer |
| S4 | `adversarial-reconcile-only` | 1 | 0 | 1 | 2 | Material adversary and real Sol reconciliation; **conditional +1 DeepSeek recheck** |
| S4 | `pre-review-blocker` | 0 | 0 | 1 | 1 | DeepSeek blocker; **zero senior review** |
| S4 | `static-claude-routing` | 0 | 0 | 0 | 0 | Deterministic; default zero paid Claude |
| S5 | `arbitrary-stage-resume` | 0 | 7 | 1 | 8 | Seven fresh Luna routing decisions plus one DeepSeek handoff |
| S6 | `upstream-rerouting` | 4 | 0 | 5 | 9 | Three Sol classifiers, one Sol handoff, five DeepSeek classifiers |
| **TOTAL** | **24 unique required IDs** | **16** | **11** | **23** | **50** | **Only permitted addition: +1 DeepSeek for optional S4 adversarial recheck** |

### 4.1 Six-segment reconciliation

| Seg. | Scenarios | Sol | Luna | DeepSeek | Baseline calls | Declared branch maximum |
|---|---:|---:|---:|---:|---:|---:|
| S1 — lifecycle and added early probes | 9 | 8 | 2 | 3 | **13** | 13 |
| S2 — deterministic negatives/direct fix/non-waivable | 7 | 1 | 1 | 5 | **7** | 7 (same pre-existing report and policy) |
| S3 — diagnosis | 1 | 1 | 0 | 5 | **6** | 6 |
| S4 — safe waiver/staleness/adversarial/blocker | 5 | 2 | 1 | 4 | **7** | 8 (if adversarial recheck allowed) |
| S5 — H05 resume | 1 | 0 | 7 | 1 | **8** | 8 |
| S6 — H06 reroute | 1 | 4 | 0 | 5 | **9** | 9 |
| **Total** | **24** | **16** | **11** | **23** | **50** | **51 only if permitted adversarial recheck occurs** |

The optional S4 adversarial recheck is the **only** declared additional one-pass invocation. H08 declares that conditional call in the invocation specification and reserves for it in S4. S2 report reuse is a **mandatory H08b acceptance prerequisite**, not an optional fallback. A failure to prove it requires a recorded design amendment before another qualifying bootstrap; it does not authorize extra calls or a policy mutation.

---

## 5. All 28 required acceptance criteria and legacy-precedence decisions

Scenario membership (24 IDs) and runbook §31 behavior (28 criteria) are both required. A command name in a plan is not evidence of the behavior.

| §31 criterion | Required proof / owning scenario |
|---:|---|
| 1 | Real discovery works; **separate explicit user-directed** clear-intent `/prd` succeeds with **no** discovery artifact. Do not score a purported model decision to skip. S1. |
| 2 | Genuine first `DISCOVERY_BLOCKED` **because a required referenced fact/artifact or its access is unavailable**. Restore that approved evidence only; resumed `/grill` returns READY. Normal discovery artifacts carry stable per-decision IDs. Deterministic scorer compares them with hidden settled-ID/value-hash expectations and fails if any settled decision is reopened or changed. The withheld *product decision* belongs only to the PRD test. S1. |
| 3 | Genuine first `PRD_BLOCKED` on withheld approved product answer; resumed ready PRD after reveal. S1. |
| 4 | Real S1 architecture retains required operating-cost rationale. |
| 5 | H06 `u01` real Sol owner classification routes the product blocker to PRD. |
| 6 | Successful S1 project-init sync plus deterministic helper failure **and live Luna `PROJECT_INIT_BLOCKED`** when canonical contract unavailable; Luna invents no substitute. |
| 7 | H06 `u02` real Sol classification and bounded `/architect` upstream handoff prove correct spec/upstream authority routing. |
| 8 | S1 approved-spec dedicated branch and real implementation evidence. |
| 9 | S1 original implementation remains uncommitted through initial review. |
| 10 | S1 fresh real DeepSeek verify against uncommitted implementation. |
| 11 | S1 ready pre-review and senior review before implementation commit. |
| 12 | S2 reversible isolated identical commit retains `MATCH`; original HEAD/worktree restored and `CP-COMMITTED` proof retained. |
| 13 | S2 identity-bearing content mutation gives `MISMATCH`, no reviewers, exact restore. |
| 14 | S2 mode/type mutation fails closed with `MISMATCH` or legitimate platform `UNRECONSTRUCTABLE`. |
| 15 | S2 exactly one real DeepSeek verification-time mutation probe blocks delivery, restores precisely. |
| 16 | S2 genuine behavioral-test `NOT_DONE`, early Luna policy-based refusal with persisted `POLICY_INELIGIBLE` blocked reason and no authorization wait, then direct fix, fresh verify, pre-review and ready senior; unchanged bootstrap policy and exact report identity protect this path. |
| 17 | S3 real diagnosis, repair, verification, review and persisted diagnosis evidence. |
| 18 | S4 factual failed `NOT_DONE` report is never rewritten by waiver. |
| 19 | S4 explicitly human-authorized safe waiver results only in `CLEAR_WITH_EXCEPTION` and valid review. |
| 20 | S4 stale-waiver immediately consumes the exact S4 waiver state; rejects changed identity before reviewers. |
| 21 | S2 copied malformed evidence yields `UNRECONSTRUCTABLE` and no reviewers. |
| 22 | S2 evidence-only mutation preserves `MATCH`, identity-bearing mutation gives `MISMATCH`. |
| 23 | S4 genuine material adversarial finding, accepted Sol `RECONCILE_ONLY`, optional bounded recheck; preserve history during restoration. |
| 24 | S4 independent blocking DeepSeek pre-review persists `CHANGES_REQUIRED`, explicitly zero senior invocations. |
| 25 | S5 all seven fresh-context H05 routing cases plus one accepted real handoff. |
| 26 | S6 accepted H06 scope: eight distinct live classifications, mechanically derived affected-chain and **one** executable upstream handoff. Does not imply eight full downstream regenerations. |
| 27 | Static Claude routing proves no mandatory paid Claude call. |
| 28 | S5 fresh independent contexts and only persisted repository evidence, never previous chat memory or leaked expected answers. |

### 5.1 Resolved old narrative conflicts

The later explicitly **authoritative** runbook §3.5 post-first-review matrix controls invocation permissions. Update legacy narrative passages to refer to it and retain the *behavioral result*, without silently inventing extra calls:

| Old instruction / apparent extra work | Agreed interpretation | Extra calls |
|---|---|---:|
| Content-mutation narrative directs `/verify` after negative test | Scored negative stops before reviewers; exact restore; separate real S2 fix path provides fresh verified state for its own review | 0 |
| Malformed-evidence narrative directs `/verify` after bad copy | Corrupt/discard evidence **copy**; original report stays authoritative; no model reviewer | 0 |
| Verification-time mutation could leave stale evidence | Exact restore; no second verify solely for negative. Later S2 direct fix has its own required fresh verification | 0 |
| Stale-waiver narrative requests eventual remediation | Preserve historical waiver and stale proof; restore an independently verified clean checkpoint and retain historical failure record. Do not carry the old waiver into new state. If this is impossible without a new live fix/verify, fail closed and classify a scenario-design defect before changing the plan | 0 on the accepted isolated matrix |
| Older standalone review-blocker prose requests repair chain | Restore isolated blocker; S2 real direct-fix independently demonstrates repair/re-review. S4 blocker must have zero senior reviewer | 0 |
| Project-init helper failure alone | Insufficient to prove actual Luna `PROJECT_INIT_BLOCKED`; add real Luna negative | **+1 Luna**, counted above |
| Non-waivable failure refused by policy | Change `/waive` order: read exact failed report, classify immutable failure-type policy and persist `POLICY_INELIGIBLE` **before** asking for human approval. Its existing bare `WAIVER_BLOCKED` token alone is insufficient because `AUTHORIZATION_MISSING` produces the same token. S2 report is genuinely prohibited by bootstrap policy; scorer checks exact report and policy identity plus blocked-record reason. No new generic waiver helper. | **+1 Luna**, counted above; **0** extra verify |
| S6 upstream rerouting should regenerate all downstream artifacts | H06 closure accepted routing-focused proof with one representative bounded handoff; update loose §31 wording to match that bounded contract | 0 |

The two added negative Luna tests cannot be reclassified as zero-cost deterministic checks. The clear-intent direct-to-PRD case is a **user-selected path test**; testing its output does not claim an autonomous skip decision.

---

## 6. Exact checkpoints, segment assignment and transitions

The following checkpoint refinements must be added to runbook §3.5 and declared by H08 as exact typed states. The old matrix currently uses `CP-VERIFIED`, `CP-REVIEWED`, `CP-COMMITTED` and generic `CP-REPAIRED`; the refined labels below are new definitions, not existing facts.

| Seg. | Start checkpoint | Required committed close | Preconditions |
|---|---|---|---|
| S1 | `BOOTSTRAP` | `CP-REVIEWED` | Nine assigned scenarios **and every H08b S1 subprobe** scored; original `CP-VERIFIED` implementation uncommitted; successful first review; project-init negative test isolated |
| S2 | Exact `CP-REVIEWED` | `CP-REPAIRED-V1` | All S2 negative tests isolated/restored; historical `CP-COMMITTED` proof retained; direct-fix verification/review complete; live non-waivable refusal scored, with genuinely valid report |
| S3 | Exact `CP-REPAIRED-V1` | `CP-REPAIRED-V2` | Real ambiguous failure, diagnostic artifact, repair and fresh successful verification/review |
| S4 | Exact `CP-REPAIRED-V2` | `CP-REPAIRED-STABLE` | Positive waiver immediately followed by stale-waiver; material adversarial reconciliation and review-blocker proof preserved; primary checkpoint properly restored |
| S5 | Exact `CP-REPAIRED-STABLE` | Same exact checkpoint | Seven independently prepared/scored/restored H05 probes plus accepted handoff |
| S6 | Exact `CP-REPAIRED-STABLE` | `QUALIFICATION_EVIDENCE_READY` | Eight independently prepared/scored/restored H06 probes plus real Sol handoff; entire accepted scenario/evidence set complete |

### 6.1 S1 sequencing, genuine discovery blocking, stable decision IDs and non-leakage

**`/grill` command semantics must not be widened.** The current normal command returns `DISCOVERY_BLOCKED` when a decision cannot be resolved because **required evidence or access is missing**. An unanswered user decision belongs to interactive questioning and confirmation, not this blocked status. Use two distinct fixture mechanisms: missing referenced evidence for `/grill`, and a withheld approved *product decision* for `/prd`.

1. **Normal `/grill` product-command output change (H08b):** Persist stable per-decision IDs in normal discovery artifacts, for real projects and smoke alike. At a minimum, each recorded decision has a stable ID, status, decision/value where settled, and references to prerequisite evidence where applicable. Preserve the same ID across blocked/resumed runs; no cosmetic rename or regeneration of accepted IDs. The normal command exposes enough structured decision/status/request information for deterministic scoring; **do not** add a smoke-only field that ordinary discovery never produces.
2. **Scorer-only expected record:** At bootstrap, store immutable expected `settled_decision_ids` and canonical accepted-value hashes **under the already-denied `docs/verification/smoke/**` path**. These records are test-control data, not ordinary discovery content. Apply the existing H05 read, glob and grep denial to every S1 probed child, including derived tools. Never place the hidden record, its expected verdicts, its filename or answer-key path in child prompts, normal discovery artifacts, AGENTS instructions, task handoff or readable scoring output. The legitimate discovery artifact may show the actual user-approved decisions and stable IDs; the **hidden expected answer set** remains inaccessible. Validate denial with negative tests.
3. **Preseed and first `/grill` call:** Before the first model invocation, fixture setup MUST seed a legitimate, approved **partially settled `docs/discovery/DISC-001` artifact** containing pre-existing settled decision IDs, accepted values/statuses and an unresolved decision requiring a referenced fact/artifact. This simulates real resumed discovery, not a smoke-only output. Commit its expected settled-ID/value hashes into the scorer-only hidden record and capture the baseline artifact state. Mechanically withhold **that required evidence or its access**; do **not** withhold a user answer. Invoke `/grill` and require `DISCOVERY_BLOCKED` with the correct missing-evidence reason, owner and minimum next action. **The blocked run need not write a new discovery artifact:** immediately score the still-present `DISC-001` against the baseline, failing any reopened, missing, renamed or changed settled decision. Restore no evidence other than the approved withheld fact/artifact.
4. **Resume `/grill` once:** Supply exactly the missing approved evidence/access, with no fabricated product decision and no other fixture mutation. Require `DISCOVERY_READY`. **Score a second independent checkpoint** after the resumed call against the same hidden, preseeded accepted-ID/value baseline. The original settled IDs must remain present and settled, their canonical values/hashes must be unchanged, and the structured requested/reopened decision-ID set must have **no intersection** with `settled_decision_ids`. Reject missing, duplicated, renamed, unparseable or silently dropped identifiers, or reopened questions referring semantically to a previously settled ID. Reject unverifiable free-form follow-ups as `NOT_SCORED`/fail-closed rather than awarding an invented pass. Preserve the two separately scored checkpoints and private score evidence without leaking expected answers to any child.
5. **Isolated explicit skip branch:** The user/fixture selects clear approved intent and directs a real Sol `/prd` call **without any** discovery artifact under `docs/discovery/`. Score genuine PRD completion and correct authority, **never** a scripted orchestrator or model's supposedly independent decision to skip discovery. Restore exact mainline fixture and checkpoint after the branch.
6. **Mainline PRD blocked/resumed branch:** Withhold a *different*, preapproved product decision that prevents safe PRD progress. Require the first mainline `/prd` to return `PRD_BLOCKED` for the correct authority, reveal only that approved decision, then resume once and require `PRD_READY` without losing already accepted PRD content. This is the only test here that intentionally withholds a user product answer.
7. **Fixed waiver policy and project-init negative:** From bootstrap the fixture's failure-type waiver policy marks failed behavioral/unit tests non-waivable and a separately approved low-risk documentation/lint failure waivable. First, a fresh successful Luna project-init records/preserves that policy in normal project instructions and synchronizes canonical Contract-v1. Then snapshot the clean state, remove only the project canonical-contract copy for the isolated negative, prove real `ProjectInitError` plus fresh Luna `PROJECT_INIT_BLOCKED` with owner `REPOSITORY`, canonical-contract cause, and next command `/project-init`, and reject any invented substitute. Restore the snapshot byte-identically before continuing.

S1 closes only after all nine assigned scenarios, every declared required subprobe and the first ready senior review have valid evidence. The evidence/access blocker and scorer key remain isolated from normal user-decision semantics and later segments.

### 6.2 S2 sequencing, reversible commit, and policy-first negative waiver

All `CP-REVIEWED`-dependent negative tests start from independent exact clean snapshots. The `identical-commit-freshness` probe commits a **copied/forked uncommitted** implementation, proves `MATCH`, records protected historical `CP-COMMITTED` evidence, and restores the original HEAD, tracked/untracked state, canonical manifest and review applicability before other probes. The committed historical evidence survives restoration.

Run deterministic freshness/mutation probes before the genuine direct-fix path changes the primary checkpoint. S2's direct-fix fixture introduces the existing `obvious-deterministic-defect`: a real behavioral/unit-test failure that the **pre-existing failure-type policy** explicitly makes non-waivable. Run the already budgeted DeepSeek `/verify` to produce `NOT_DONE / BLOCKED / MATCH` against that exact policy and implementation state. Do not alter policy or implementation between this report and the Luna policy-refusal call.

The independent Luna `/waive` negative subprobe consumes that exact persisted failed report. After the command's **new eligibility preflight**, it must persist a blocked record with `reason_code=POLICY_INELIGIBLE`, exact failed-report identity and digest, prohibited failure type and unchanged policy reference/digest, then end with the existing exact `WAIVER_BLOCKED` terminal token **before** requesting authorization. No fabricated user approval, H07 receipt, or H07 wait interval is created. Deterministic scoring checks this **record's reason and source identities**, rather than interpreting the ambiguous terminal token. `AUTHORIZATION_MISSING`, an absent/invalid blocked record, or a changed policy fails the probe. Preserve the failed report, blocked record and policy as historical scored evidence.

After scoring the negative refusal, continue the normal direct repair path: DeepSeek `/fix`, fresh DeepSeek `/verify`, DeepSeek pre-review, ready Sol senior. This completes `CP-REPAIRED-V1`. All isolated negatives and reversible commit probes must be restored before the segment closes.

**No independent verification fallback is declared or budgeted.** If the report/policy relationship or the policy-first real Luna refusal cannot be demonstrated, H08b is blocked: preserve failure evidence and explicitly amend the design/spec/config only by a separate reviewed decision, not by executing a surprise model call.

### 6.2a Explicit H08b `/waive` product-command and blocked-record changes

The current normal `/waive` command asks for authorization in Stage 2, performs the policy-category check in Stage 3, and emits the same bare final `WAIVER_BLOCKED` token for missing authorization, missing evidence and prohibited policy. Therefore a live negative cannot prove **policy-based refusal** under the current command. H08b must correct **both** the order and the missing observable reason; this is an explicit product-command change, not a smoke-only workaround.

**Required revised normal workflow:**

1. **Load exact failure evidence:** Read the actual `NOT_DONE` report, relevant spec, exact requested failures and current project waiver/security policy. Persist a blocked record with an appropriate distinct invalid-evidence reason if the referenced report/failure is unavailable or unsupported; never invent a failed check.
2. **Pre-authorization eligibility:** Classify the *actual reported failure types* against the policy present from bootstrap/project-init. If a requested failure is non-waivable, **before any authorization interaction or H07 wait**, persist a terminal blocked record with `POLICY_INELIGIBLE` and finish with exactly `WAIVER_BLOCKED`. No waiver/receipt is created. Generic classification labels alone do not override a more specific failure-type prohibition.
3. **Only for eligible requests, obtain explicit human authorization:** Retain H07's unchanged exact report-byte SHA-256, failure set, classification, binding, receipt, required decision fields, single-open-wait semantics and invalid-resume no-op. For an eligible request without authorization, persist a blocked record with `AUTHORIZATION_MISSING` and end with exactly `WAIVER_BLOCKED`; it must be distinguishable from Step 2 in persisted evidence.
4. **Revalidate freshness and policy before persistence:** An eligible, properly authorized request still passes the original normal scope, expiry, freshness and policy checks. A policy change may block an old request but never retroactively authorize it. Keep factual `NOT_DONE` untouched and retain all downstream review gates.

**Machine-readable blocked-record contract for normal runs:** Persist an immutable record in a designated normal waiver evidence location, the fixed sibling directory `docs/verification/waiver-refusals/` (not a smoke-only output and **never** a child of the active `waivers/` directory). It must have a deterministic documented schema with at least: status `WAIVER_BLOCKED`, reason code (`POLICY_INELIGIBLE`, `AUTHORIZATION_MISSING` and distinct codes for other supported block reasons), requested failure IDs/types, exact verification-report path and byte digest when available, implementation fingerprint when available, classification when known, applicable policy reference and digest, decision timestamp and whether authorization was requested or a receipt existed. Unsupported/unavailable fields must be explicitly null and validated; never manufacture an identity to fill a missing field. Unique blocked-attempt identity must prevent overwriting a prior historical denial. The terminal command status remains the **existing bare token**, while the persisted record conveys why. A blocked record **is not** a waiver authorization or a new qualifying reviewer result. Active-waiver discovery must never treat files in the sibling `waiver-refusals/` directory as candidate waivers, even when using broad verification-path searches. The segment evidence manifest includes these historical refusals and protects their exact bytes/path during checkpoint restoration and all later segment openings.

**Static and behavioral protections:** H08b couples the five normal commands listed above and updates `smoke_static.py` to protect their new contracts, fresh-child scorer isolation, and S1/S2 score-at-close binding. Add deterministic schema/order checks for `POLICY_INELIGIBLE` versus normal alternate blocked reasons, exact report/policy binding, factual failure-type persistence, canonical-contract project-init blocking, refusal-history exclusion from active review, and no H07 wait on ineligible requests. The real S2 Luna probe is indispensable: it must produce actual `WAIVER_BLOCKED` with `POLICY_INELIGIBLE` for the **existing** failed behavioral/unit-test report against unchanged policy; a blocked token alone is insufficient. The S4 waivable documentation/lint path must retain real explicit H07 authorization and accepted positive review semantics. Do not create a generic waiver-policy helper or weaken H07's previously accepted rules solely for the probe.

### 6.3 S4 waiver continuity and material adversarial evidence

S4's **positive** waiver uses the already accepted H07 explicit authorization/receipt. Immediately run `stale-waiver` against that *exact* state without restoring or pausing at a segment boundary. Preserve the failed report, approval, review, and stale proof even after the primary checkpoint is restored.

Material adversarial review runs on an authorized isolated authority snapshot. Persist its genuine findings and real `RECONCILE_ONLY` report, with at most one condition-triggered follow-up adversarial call. If material reconciliation makes the primary checkpoint legitimately stale and isolation cannot preserve genuine semantics, fail closed instead of manufacturing `CP-REPAIRED-STABLE`. The independent review blocker uses exactly one DeepSeek pre-review and zero senior calls.

### 6.4 H05/H06 stable checkpoint carry-forward

The S2 policy-refusal record remains immutable historical evidence in the sibling `docs/verification/waiver-refusals/` location and is included in the cumulative evidence manifest through `CP-REPAIRED-STABLE`. It must never be interpreted as an approved or active waiver. H08b reruns H05 focused routing tests **with this refusal present** and retains the S4 positive-waiver/stale-waiver tests to prove both directions of waiver lookup. H08's generic all-accepted-evidence hashing includes the new location without special-casing the segment clock or checkpoint identity.

S5's close reproduces the *exact* source/checkpoint identity from its S4 start. Only a committed S5 close with protected ledger/evidence permits S6 opening. Each H05/H06 probe is independent, hidden-expected, scored and restored before the next. S6 adds the final evidence-ready marker **only after** all 24 required scenarios and required subprobes have valid evidence.

---

## 7. Auditable provisional timing worksheet and H13 calibration

### 7.1 Measured evidence versus assumptions

Historical cumulative elapsed-time checkpoints (including mechanics and gaps) are in §2. They **do not** establish pure child-model latency percentiles. The current worksheet defines **inclusive per-call execution slots**: a class estimate covers the child and its *ordinary associated per-call orchestration* once. The separate residual-mechanics column below covers only **additional segment-only deterministic setup, isolation, restoration, protected hashing and checkpoint transitions not allocated to a call slot**. The worksheet and H13 must not count the same work twice.

| Class | PROVISIONAL inclusive minutes/call | Basis / measurement status |
|---|---:|---|
| `SOL_AUTHOR` | 4.00 | Historical discovery/PRD/spec intervals roughly 2.35–4 min, inclusive; assumption that 4.00 represents this fixture's one-pass slot |
| `SOL_SENIOR` | 3.50 | Senior appears to have returned in roughly 3-minute inclusive interval; exact ledger duration not recovered |
| `SOL_RECONCILE` | 3.00 | Unmeasured assumption, not a guaranteed bound |
| `SOL_ROUTE` | 2.50 | Unmeasured H06 planning-classification assumption; **H13 targeted** |
| `SOL_HANDOFF` | 2.50 | Unmeasured H06 bounded handoff assumption; **H13 targeted** |
| `LUNA_PROJECT_INIT` | 2.00 | Separate Luna duration not isolated from earlier combined architect+init interval; assumption; includes negative path as one separate slot |
| `LUNA_WAIVE` / `LUNA_WAIVER_NEGATIVE` | 2.50 | Unmeasured assumptions; safe/negative contexts may differ and retain separate ledger observations |
| `LUNA_RESUME_ROUTE` | 2.50 | Unmeasured H05 routing assumption; **H13 targeted** |
| `DS_IMPLEMENT` | 3.75 | Historical implementation-inclusive interval near 3.57 min |
| `DS_VERIFY` | 4.25 | Historical verification-inclusive interval near 4.11 min; S2 contains only its already-required verification calls, with no separately permitted waiver fallback |
| `DS_PRE_REVIEW` | 4.75 | Historical pre-review-inclusive interval near 4.64 min |
| `DS_FIX` | 3.00 | Unmeasured assumption |
| `DS_DIAGNOSE` | 3.00 | Unmeasured assumption |
| `DS_ADVERSARY` | 3.00 | Unmeasured assumption; use for conditional recheck too |
| `DS_ROUTE` | 2.50 | Unmeasured H06 fix-origin routing assumption; **H13 targeted** |
| `DS_HANDOFF` | 2.50 | Unmeasured H05 bounded handoff assumption; **H13 targeted** |

No assumption above asserts that an unmeasured routing task *must* run faster than the fastest historic authoring call. **All unmeasured classes remain labelled assumptions even after the initial PROVISIONAL configuration is installed.** One H13 observation is a calibration input, not a statistical guarantee.

### 7.2 Fixed formula and segment calculation

Budget every declared one-pass invocation, including the permitted S4 adversarial recheck. S2 report reuse is a **required fixed-fixture property**, not a conditional cost path. Use distinct segment-only residual work without double-counting per-call inclusive class slots:

`segment_limit_minutes = ceil(1.5 × (Σ [permitted_call_count × inclusive_class_slot_minutes] + residual_segment_only_minutes))`

The residual figures are explicitly **assumed, not measured**, and represent only setup/isolation/restoration/protected-checkpoint work outside class slots. Do not double-count historic per-call orchestration; H13 provides additional targeted observations.

| Segment and baseline class makeup | Inclusive baseline call slots | Extra permitted slots | Residual segment-only mechanics (assumption) | Budget calculation basis | Positive PROVISIONAL limit |
|---|---:|---:|---:|---:|---:|
| S1: 7 Sol author, 1 Sol senior, 2 Luna project-init, 1 DS implement, 1 DS verify, 1 DS pre-review | 48.25 | 0 | 5.00 | 53.25 | **80 min** |
| S2: 1 Sol senior, 1 Luna negative waive, 3 DS verify, 1 DS fix, 1 DS pre-review | 26.50 | **0** | 5.00 | **31.50** | **48 min** |
| S3: 1 Sol senior, 2 DS verify, 1 DS diagnose, 1 DS fix, 1 DS pre-review | 22.75 | 0 | 2.00 | 24.75 | **38 min** |
| S4: 1 Sol senior, 1 Sol reconcile, 1 Luna waive, 1 DS verify, 2 DS pre-review, 1 DS adversary | 25.75 | **3.00 DS adversary recheck** | 6.00 | 34.75 | **53 min** |
| S5: 7 Luna routes, 1 DS handoff | 20.00 | 0 | 4.00 | 24.00 | **36 min** |
| S6: 3 Sol routes, 1 Sol handoff, 5 DS routes | 22.50 | 0 | 4.00 | 26.50 | **40 min** |
| **TOTAL** | **165.75 min** | **3.00 min** | **26.00 min** | **194.75 min** | **295 min derived** |

**Arithmetic audit:** S1 `ceil(1.5×53.25)=80`; S2 `ceil(1.5×31.50)=48`; S3 `ceil(1.5×24.75)=38`; S4 `ceil(1.5×34.75)=53`; S5 `ceil(1.5×24)=36`; S6 `ceil(1.5×26.5)=40`. The **derived sum is 295 minutes (4h55m)** if the optional S4 adversarial recheck occurs, not a separately configured ceiling or an empirical prediction.

**Important arithmetic correction to the preceding discussion:** dropping the 4.25-minute fallback from v4's S2 worksheet leaves `26.50 + 5.00 = 31.50`; applying the agreed `ceil(1.5×...)` gives **48 minutes, not 47**. Reducing it to 47 without changing evidence-backed slot/residual assumptions would break the fixed formula.

The **50-call normal-path estimate is 191.75 minutes** (`165.75` baseline class slots + `26.00` residual), before headroom. The permitted 51st adversarial call makes the corresponding estimate **194.75 minutes**. These are declared worksheet assumptions, not completed-run measurements.

**Acceptance consequence:** H08 ships the positive 80/48/38/53/36/40 configuration. H08b must demonstrate the fixed-policy direct-fix report reuse without adding calls. If it fails, the contract must be deliberately revised before qualification; no fallback is silently revived. H13 then supplies mandatory targeted calibration and an explicitly recorded new configuration decision before H14 if the observed data warrants revision.

### 7.3 H08 must ship real numerical PROVISIONAL configuration

A helper that rejects missing/`null` limits cannot ship with string placeholders or promise to defer all numbers until H13. **H08's closing gate requires a positive integer limit for every active FULL segment and the applicable FAST profile budget, derived from an audited assumptions worksheet and labelled `PROVISIONAL`.** These are initial enforceable limits, not empirically certified bounds. Preserve the calculation and selected revision, and reject any silently altered limit.

H08 cannot claim completion if its default config cannot bootstrap safely. H08b cannot exceed the H08 invocation contract to make a behavioral probe pass; successful direct-fix report reuse against unchanged fixed policy is part of its acceptance gate. Any failure requires a recorded design/spec/config decision before a new qualifying bootstrap.

### 7.4 Narrow mandatory H13 calibration; H14 proves full timing

H13 remains a **small** real Kilo integration probe, not another FULL or a demand for observations of every unmeasured class (particularly a second human-authorized waiver). Its **mandatory targeted timing evidence** is the five unmeasured classes that drive S5/S6 budget risk: `LUNA_RESUME_ROUTE` (H05), `DS_HANDOFF` (H05), `SOL_ROUTE`, `DS_ROUTE` and `SOL_HANDOFF` (H06). One genuinely bounded, representative observation per critical class is required **unless a matching completed prior stage-ledger observation is recovered**. In addition, H13 must execute exactly one bounded fresh `h08b-luna-probe` `/waive` call against a deterministic non-waivable fixture to prove the real child can invoke `file_digest.py`, persist exact report/policy digests, and return a scorer-valid refusal without reading hidden smoke evidence. This is an integration proof, not a second H08 qualification call or a human-authorized waiver. Reuse existing mini-fixtures and collect the usual stage timestamps plus derived gaps; do not create a general measurement system.

Other classes keep clearly labelled assumptions and 1.5× margin; H13 may opportunistically use genuine existing ledgers, but must not fabricate unsupported measurements or a waiver receipt. If targeted probes uncover materially different timings, **explicitly record the changed worksheet and accept a new configuration revision before H14**. If a mandatory targeted observation cannot be safely obtained inside H13's small scope, record a calibration blocker and make an explicit budget/design decision; do not make H14 an undisclosed first measurement.

H14 is the first assembled, release-qualifying six-segment FULL. It reports real per-class timings, gaps, attempted/accepted calls, wait exclusions, segment boundaries and charged/aggregate time under the pinned configuration. Neither H13 nor H14 is allowed to raise an active qualification's pinned limits.

---

## 8. One invocation specification; one pinned budget source

H08 creates a versioned, machine-readable `forge/smoke/FULL-INVOCATION-SPEC.json` declaring all 24 scenario IDs, their ordered subprobes and owners, required and conditional model calls, hidden-vs-visible test data boundaries, prerequisite/restored checkpoints, factual evidence and zero-reviewer restrictions. It expressly declares the five gap-filling model calls in §3.2, the deterministic unavailable-contract helper check, the S1 **evidence/access-blocked** discovery and normal-output decision-ID contract with scorer expectations hidden under `docs/verification/smoke/**`, the required S2 fixed-policy report reuse and reason-coded policy-first refusal, the **updated authoritative `direct-fix-loop` call sequence**, and the optional S4 adversarial recheck. **No S2 fallback verification is permitted**. This file contains **no duplicate numerical segment limits**.

`forge/smoke/profiles.json` is the **sole source of numerical limits**, ordered six-segment membership, start/close checkpoint declarations and FAST profile budget. Its FULL segment objects have `{id, scenarios, limit_minutes, start_checkpoint, close_checkpoint, limit_status}`; `limit_minutes` is a **positive integer**, not `null` or a placeholder. `limit_status` is `PROVISIONAL` until post-H13 evidence warrants an explicitly accepted revision. The initial FULL numerical proposal is the **80/48/38/53/36/40** worksheet from §7; its S2 entry requires genuine already-budgeted report reuse, not a silent extra call or change to the old 30-minute ceiling.

**Mandatory runbook §3.5 `direct-fix-loop` matrix update (H08 declares, H08b executes):** The authoritative sequence becomes:

`DeepSeek /verify (real behavioral-test NOT_DONE) → Luna /waive (early POLICY_INELIGIBLE, persisted WAIVER_BLOCKED, no authorization/wait) → DeepSeek /fix → DeepSeek /verify → DeepSeek pre-review → Sol senior only when ready`.

The row's allowed model count becomes **6**, not 5. Its negative Luna call is within the existing `direct-fix-loop` scenario, **not** an added top-level scenario. Require exact already-budgeted failed-report reuse and unchanged bootstrap policy. Update the invocation specification and this runbook matrix **together**, so the orchestrator does not violate the old `MUST NOT exceed` rule. H11 later verifies exact sequence/owner/zero-wait and blocked-record requirements; H08 must provide a consistent declared contract rather than waiting for H11 to discover a contradiction.

**Basic H08 static checks:** Six unique ordered IDs; all required FULL scenarios exactly once, no optional/FAST substitution; declared scenario order and checkpoint adjacency; complete dependency of `waive-review-loop`→`stale-waiver`; valid positive integers; declared conditional calls reflected in worksheets; hashable canonical schema. These are the minimal safety checks needed to execute H08. **H11** independently consumes the same spec and performs the complete dry orchestration/owner/evidence/hand-off validator; do not build a competing general validator in H08.

At bootstrap, copy selected profile **by value** into exact canonical state with ordered segments, numerical limits, status, invocation-spec digest, canonical schema version and a canonical SHA-256 of the complete snapshot. The snapshot and hash are write-once, analogous to H03 `contract_parity`. Subsequent `check` reads the pinned snapshot, never editable live `profiles.json`. Invalid hash, missing or `null` limit, changed live config during an active run, or incomplete legacy FULL state fail closed; no automatic migration into a qualifying segmented run.

Reject both CLI `--limit-minutes` and programmatic numeric overrides. Remove old literal `30` assumptions from `smoke_budget.check`, `smoke_static.py` budget labels, `smoke.md`, orchestrator and runbook; use the pinned active segment's limit. Preserve FAST's own positive profile budget without silently broadening its scenarios.

---

## 9. Exact segment-state and crash-recovery contract

Canonical state is authoritative for **segment lifecycle**. The existing budget ledger retains authority for **individual stage timing and H07 human-wait facts**; neither an orchestrator statement nor an independent ledger-only write may close a segment.

**States:** `NOT_STARTED → ACTIVE → COMPLETED`, with terminal `BUDGET_EXCEEDED` for an active segment. Canonical run state may remain `IN_PROGRESS` during a typed `BETWEEN_SEGMENTS` interval; being between segments is not a human-authorization wait.

### 9.1 Opening a segment

S1 opens mechanically as part of bootstrap **before** its `static-release-gate` scenario runs. There is no unmetered S1 static phase. Subsequent segment openings require the preceding segment's atomic committed closing record, intact pinned configuration, no active child/no open H07 wait, the protected source-checkout fingerprint, the exact required checkpoint identity and the protected closing evidence/ledger digests. The helper derives the new committed start timestamp; a caller cannot choose it.

Opening a segment requires a single valid canonical state transition. If opening crashes before commit, the next segment never became ACTIVE and the gap remains open; if commit succeeded but its acknowledgment was lost, recovery recognizes the original committed start. No second start time may be chosen.

### 9.2 Closing a segment

The helper alone may commit closure. Before committing it must mechanically confirm:

1. Every scenario assigned to the current segment appears in `completed_scenarios`, and every required subprobe/conditional-path obligation has its scored evidence.
2. All required historical evidence files exist and match their expected content; any applicable checkpoint restores reproduce exact identity.
3. The segment remains inside its **pinned** time budget.
4. No model child invocation and no H07 authorization interval remains open.
5. Protected source identity has not drifted.
6. The evidence-file manifest and segment ledger projection are collected, canonicalized and hashed; the manifest includes the complete accepted evidence path set, not just a chosen few reports.

Commit the complete closing record, its immutable timestamp, original opening timestamp, charged elapsed time, excluded H07 wait duration, configured limit, assigned/completed scenario IDs, exact closing checkpoint, evidence-manifest digest and ledger-prefix/projection digest in **one atomic canonical-state update**. The ledger is validated as an input to this transaction, not used as a second independently committed close authority.

**Crash resolution:** Absent a fully committed closing record, the segment remains **ACTIVE** and its original clock **keeps running**. An interrupted write never creates free time. If a complete committed close exists but the response was lost, return the existing immutable close instead of writing a new one. A timed-out segment cannot be closed into a qualifying COMPLETED state.

### 9.3 Protected accepted evidence

Contract-v1 deliberately excludes `docs/verification/**`, `docs/reviews/**` and `docs/diagnostics/**` from implementation identity. Consequently **checkpoint `MATCH` alone cannot protect accepted reports during a gap**.

At segment close, enumerate all evidence accepted to satisfy that segment, including applicable verification/review/waiver/**reason-coded policy-refusal blocked records**/diagnosis artifacts, adversarial findings/reconciliation reports, actual scored probe results, hidden answer-key/scorer artifacts used for acceptance and the canonical scenario-evidence index. Persist a sorted canonical manifest of **normalized repository-relative paths, content SHA-256 digests and a complete membership set**; prohibit path traversal, duplicate normalized paths and symlink escape. Hash the manifest itself and protect that digest in the closing record. Evidence files may live outside the implementation identity set, but their exact bytes and paths remain protected. Historical adversarial and waiver evidence must survive legitimate fixture restoration.

The **ledger digest** is over a canonical, immutable projection of all segment-owned `stage_invocations` and H07 intervals, with identity, order, status, timestamps, elapsed values and applicable gate bindings. Include counts/entry identities so replacing or deleting a historical entry is detected. Later segments may append their own new ledger records, but must never mutate a closed segment's projection.

**At the next segment open**, recompute and verify: pinned config hash; source fingerprint; exact checkpoint; previous close's complete evidence manifest and every underlying file hash; and its stored ledger projection/hash. For S3–S6 also verify the cumulative retained closed-segment evidence/ledger chain, not only the immediately preceding record; an old report edited after a later segment opened must still be detected at subsequent validation/final report. A failed check blocks or disqualifies qualification; it is not a cue to reconstruct accepted evidence with a model.

### 9.4 Entire-qualification terminal rule

Each segment has one qualification attempt. H02 interruption/recovery resumes within the same ACTIVE segment, subject to its unchanged original clock and original source guard. If a segment times out, **the entire qualification becomes ineligible for PASS**; completed evidence remains available for diagnosis but cannot be promoted by rerunning only the failed segment. A new qualifying attempt requires a new qualification ID and all required evidence again. At the hard limit, no new stage launches; an already-running child is not forcibly killed, but cannot rehabilitate the overrun.

---

## 10. Final boundary-gap and aggregate-time rules

**The boundary-gap rule is deliberately asymmetric:** no unaccounted time **within** a segment; explicit, recorded and restricted downtime **between** committed segments.

1. An inter-segment gap **starts only on the atomic committed close timestamp**. Completing the last call, hitting a checkpoint or exiting Kilo does not start a gap.
2. During the gap: operator rest/inactivity, read-only status, and bounded read-only source/checkpoint/ledger/evidence preflight are permitted. **No substantive model call, scenario scoring, fixture mutation, evidence repair, source-checkout change or other qualifying execution** is permitted. Gap activities and failed preflights are logged with timestamps.
3. The gap **ends only when the next segment's ACTIVE record is atomically committed** after full preflight. Preflight time belongs to the explicitly recorded gap because it is restricted to read-only validation; it is not a hidden unmetered stage.
4. Transient failed read-only preflight may be recorded and retried while remaining in the gap. Proven source/checkpoint/evidence/ledger/configuration drift makes that qualification ineligible for PASS; repairing evidence during the gap and then continuing is forbidden.
5. No intentionally scheduled stop **inside** ACTIVE. Ordinary inactivity, crashes, recoveries, transport delays and debugging inside ACTIVE burn its original clock. H07's validated `WAIVER_AUTHORIZATION` interval is the only Stable-v0.1 eligible exclusion inside a segment; a mere `WAITING_FOR_USER` state does not pause anything.
6. An open H07 wait is never allowed to cross a segment close. No scenario may launch while such a wait is open. Invalid RESUME/authorization remains a pure no-op on the open wait.

Aggregate configured allowance is **derived** as the sum of pinned segment limits. Aggregate actual active time is the sum of the six individually charged segment durations. Report both plus all excluded H07 waits, inter-segment gaps and total wall-clock time. **Do not configure a second aggregate hard limit**: every individually passing segment already bounds the sum.

---

## 11. Explicit H02/H03/H07 coupling and implementation ownership

| Current file / authority | H08 extension; invariant to preserve |
|---|---|
| H03 / `smoke_state.py` | Exact canonical schema for write-once snapshot/hash and immutable per-segment start/close/evidence/ledger references; atomic validated transitions; retain immutable run/profile/fixture/source/baseline identity and write-once `budget_started_at_utc` as original qualification anchor. |
| `smoke_bootstrap.py` | Validate, snapshot and hash selected configuration and register S1 ACTIVE **before** the static gate; reject partial bootstrap rather than fabricating a new S1 start. |
| H02 / `smoke_budget.py` | Retain ACTIVE/COMPLETED/ABORTED/INTERRUPTED invocation behavior and source-root recovery; derive current segment from canonical state, validate scenario membership, tag every invocation, enforce its pinned limit. |
| H07 authorization ledger | Bind each interval to its actual ACTIVE segment, preserve original gate/report bytes/identity, single-open-interval, invalid-RESUME no-op, append-only completed waits; only valid `WAIVER_AUTHORIZATION` pauses that segment. |
| Evidence/ledger integrity | Close records commit evidence manifest (complete membership and exact paths/hashes) **and** immutable segment ledger projection digest in one canonical state transaction; every subsequent open revalidates prior committed chain and underlying bytes. |
| `smoke_static.py` and FAST config | Basic schema/coverage, dynamic budget label, no default numeric override; FAST still works under explicit pinned FAST budget. |
| `smoke.md`, orchestrator, runbook | Align one segment state machine and source of limits; add exact `CP-REPAIRED-V1/-V2/-STABLE` refinements; remove contradicted legacy model replays. |
| H08b normal-command coupling + `smoke_static.py` | Add declared S1/S2 probes and deterministic scoring. Normal `/grill` gains stable decision IDs/states; `/verify` persists factual failure types needed by waiver policy; `/project-init` uses deterministic helper-owned waiver-policy SHA/type traceability plus refusal/canonical-contract setup; `/waive` uses repository-confined deterministic report/policy hashing, performs policy eligibility before authorization and persists reason-coded refusals; `/review` excludes refusal history from active-waiver lookup. Fresh Luna behavioral probes are scorer-hidden; S1/S2 close requires matching H08b PASS scores. Preserve all H07 receipt/wait invariants. |
| H09/H10, H11, H12, H13/H14 | Do not preempt containment/identity items; H11 independently validates declarative workflow, H12 enforces final system/runtime cleanup, H13 samples targeted missing call classes, H14 performs full qualification. |

**Required tests:** Atomic close absent ⇒ original segment remains ACTIVE and its clock runs; close requires every assigned scenario **and every declared required subprobe**; no open child/H07 wait; exact restored checkpoint; valid source fingerprint; verified complete evidence/ledger digests. N+1 cannot open before a committed N close. Later append-only ledger work must not mutate a closed projection. Protect *all* previously closed segment evidence across every subsequent open and final report, not only the immediately preceding segment.

H03/H07 coupling is explicitly authorized for *design scope* under H08, not a license for unrelated changes to those completed items. No repo change or PR merge follows from approval of this document alone.

---

## 12. Deterministic/regression tests and PR-level performance containment

Reuse H05/H06 `setUpClass` seeded Git fixtures with per-test snapshot copies. Most H08 budget and segment tests must use injected timestamps/source guards, not repeatedly initialize new repositories. Give genuine state/checkpoint integration tests a limited set of seeded disposable Git fixtures. H08b may reuse those facilities rather than constructing a second parallel harness.

**H08 focused assertions:** all 24 IDs exactly once; updated authoritative direct-fix row contains the declared Luna negative in correct sequence; exact six-segment adjacency; 50/51 working arithmetic with **only** the permitted optional adversarial recheck; positive limit and tamper rejection; no caller override; immutable pinned snapshot despite live registry changes; atomic close and original clock on crash; no premature next open; valid multi-day gap; read-only preflight only; checkpoint/source/evidence/ledger cumulative revalidation; H07 wait ownership; H02 interrupted retry; terminal timeout; valid FAST behavior; deterministic static gate independent of a literal 30 label.

**H08b focused assertions:** genuine **evidence/access-blocked** `/grill` and resumed discovery starting from a **preseeded approved `DISC-001`**, with stable per-decision IDs preserved by the **normal** `/grill` command and scored at **both post-block and post-resume checkpoints**, deterministic hidden settled-ID/value-hash scoring using the already-denied `docs/verification/smoke/**` answer-key location, and approved missing-artifact restoration; unanswered user decisions must not be mis-scored as `DISCOVERY_BLOCKED`; no self-scored skip-intelligence claim; actual no-discovery PRD artifact; actual `ProjectInitError` **and** independent Luna `PROJECT_INIT_BLOCKED`; fixture waiver-policy type mapping fixed at bootstrap and installed by project-init; `waive.md` policy eligibility **before** human authorization **and normal persisted machine-readable blocked-reason records only under the sibling `docs/verification/waiver-refusals/` path**, with order/schema/static-gate tests and a real Luna refusal on the existing S2 failed report; verify `POLICY_INELIGIBLE` record/report/policy bindings and **no H07 wait/receipt** on that rejection, distinguish it from `AUTHORIZATION_MISSING`, and separately preserve S4 safe-waiver authorization behavior; no leaks into H05/H06 or mainline states; **rerun H05 focused routing tests with the persisted S2 refusal file present in `CP-REPAIRED-STABLE` and demonstrate that it is not treated as an active waiver; also preserve S4 positive-waiver/stale-waiver lookup behavior**; exact S2 restored checkpoint and historical evidence. If genuine report reuse fails, block H08b for an explicit design revision—do not inject an unbudgeted verify call.

**Windows regression contract (against accepted H07 reference host):** full `forge/scripts` baseline 238.704s, **>10% regression** (greater than 262.5744s, approximately 262.6s) blocks merging, and temporary full-suite ceiling remains 300s. Focused item-suite target ≤60s, hard ceiling 90s; tooling target ≤30s, hard ceiling 60s. H12's eventual targets remain full suite ≤180s and tooling ≤30s. Assess **each PR and cumulative H08+H08b runtime**; an apparently harmless second PR must not hide the combined regression. Do not remove or weaken tests to satisfy the gate.

H08 closes on deterministic proof of infrastructure; H08b closes on its independent real behavioral evidence. Neither item runs a new FULL qualification just to estimate duration. Reviews/test completion do not imply permission to merge either PR.

---

## 13. Acceptance gates and release handoff

### 13.1 H08 infrastructure gate

> All 24 required FULL scenario IDs and their approved required/conditional subprobes are represented by a complete machine-readable, checkpoint-consistent six-segment sequential plan. H08 ships a worksheet-derived, valid-positive-integer **PROVISIONAL** budget configuration, pinned by value/hash and enforced by the helper without caller overrides. Atomic closing, original-clock interruptions, fail-whole-qualification timeouts, restricted recorded inter-segment gaps, source/checkpoint/evidence/ledger integrity, and explicitly scoped H02/H03/H07 coupling are deterministic and regression-tested. H08 declares—but does not yet claim passing live behavioral evidence for—the H08b probes. Limits are coherent auditable assumptions, **not** a claim of measured assembled feasibility.

### 13.2 H08b behavioral acceptance gate

> The user-selected isolated clear-intent branch demonstrates real PRD success with *no discovery artifact*, not a scripted model skip decision. The genuine `/grill` blocker is missing **required referenced evidence/access**, not a withheld user product answer; after supplying exactly that evidence, resumed normal `/grill` output uses stable per-decision IDs and is deterministically scored against hidden ID/value-hash expectations protected under the existing H05-denied `docs/verification/smoke/**` path. Stable decision IDs and structured status are **normal `/grill` product-command outputs**, not smoke-only fields. Separately, blocked/resumed PRD uses withheld approved *product decisions*. One real Luna project-init child returns `PROJECT_INIT_BLOCKED` for unavailable contract evidence, independently backed by mechanical `ProjectInitError`. Fixed failure-type waiver policy is installed at bootstrap/project-init and unchanged when S2's existing direct-fix verification creates a genuine behavioral-test `NOT_DONE` report. H08b **reorders normal `/waive` to check failure-type policy before requesting authorization and persist a machine-readable blocked record**; real Luna must produce `POLICY_INELIGIBLE` bound to that exact report and unchanged policy, ending with `WAIVER_BLOCKED` without any H07 wait or fabricated authorization. Eligible requests missing approval persist `AUTHORIZATION_MISSING` instead. The static gate protects ordering and blocked-record behavior; S4 safe-waiver and H07 authorization still function. The runbook §3.5 `direct-fix-loop` row and H08 invocation spec expressly authorize the extra Luna between failed verify and repair. Exactly **50 ordinary / 51 with the optional adversarial recheck** are declared and scored; failed report reuse or blocked-reason ambiguity blocks H08b pending explicit design revision. Focused, full and cumulative regression gates pass.

### 13.3 H11–H14 ownership

- **H11:** Read the existing H08 spec/profile and validate complete FAST/FULL owners, **direct-fix Luna-negative placement**, normal `/grill` decision-ID and hidden-answer-key boundaries, `/waive` reason-code records and pre-authorization policy order, call sequencing, hidden scoring, prerequisites, checkpoint transitions, evidence, zero-reviewer restrictions and costs. Do not invent an alternate runtime contract.
- **H12:** Achieve agreed final deterministic consistency and reference-host runtime gates with H08/H08b both merged through *separately authorized PRs*.
- **H13:** Small real Kilo integration plus mandatory bounded observations **only of five S5/S6-critical classes** (`LUNA_RESUME_ROUTE`, `DS_HANDOFF`, `SOL_ROUTE`, `DS_ROUTE`, `SOL_HANDOFF`) unless matching historical ledgers are recovered. Keep remaining assumptions labelled. Recalculate and obtain a recorded accepted numeric config revision **before H14**, with no waiver simulation or mini-FULL.
- **H14:** Execute one complete real six-segment FULL against pinned configuration, report all expected/actual model attempts, elapsed class slots, overhead/gaps and qualification evidence, and establish or refute actual budget feasibility. A failed segment cannot be retried within the same qualification to obtain PASS.

---

## 14. Ready-to-paste tracker entries (no numerical limits in tracker)

*The Git tracker in this draft PR now contains separate H08 and H08b rows while preserving the original H09–H14 IDs. H08b remains blocked by H08, and the narrowed command/static-gate coupling does not reopen H07 authorization semantics.*

| ID | Issue | Priority | Acceptance gate | Status | Closing commit |
|---|---|---|---|---|---|
| **H08** | Continuous FULL runtime and invocation budget conflicts with required matrix/checkpoint integrity; requires segmented qualification infrastructure | DESIGN BLOCKER | Declare complete 24-scenario and required/conditional subprobe invocation spec; ship six sequential segments with positive worksheet-derived **PROVISIONAL** limits exclusively in `profiles.json` and pinned by value/hash at bootstrap; helper-owned budget, atomic close/open, interruption's original clock, fail-whole-run timeout, verified checkpoint/source/evidence/ledger continuity, restricted recorded boundary gaps, explicit H02/H03/H07 coupling and applicable deterministic/performance gates. Declare H08b's behavioral calls, normal `/grill` stable-ID requirement, required unchanged-policy S2 report reuse and machine-readable blocked-reason contract **and update the authoritative direct-fix matrix** without implementing its live probes. H11 validates the assembled workflow; H13/H14 assess runtime. | TODO — NEXT | — |
| **H08b** | Missing genuine early lifecycle behavioral probes and narrow normal-command coupling across `/grill`, `/verify`, `/project-init`, `/waive`, and `/review` | **CRITICAL** | Against H08's fixed spec: genuine evidence/access-blocked then resumed `/grill`, with a **preseeded partially settled `DISC-001`** carrying stable per-decision IDs in **normal** discovery output, two deterministic checkpoints (**after blocked and after resumed**), and a hidden scoring record under already-denied `docs/verification/smoke/**`; user-selected clear-intent PRD succeeds without discovery and mainline PRD blocks/resumes on a withheld product decision; both helper and real Luna project-init reject an unavailable canonical contract; fixed failure-type policy persists from bootstrap. Reorder normal `/waive` policy eligibility before authorization **and persist a machine-readable refusal record in the sibling `docs/verification/waiver-refusals/` location, distinguishing `POLICY_INELIGIBLE` from `AUTHORIZATION_MISSING`**. Static gate protects new command outputs/order/blocked-record contract; a real Luna call denies the existing S2 failed behavioral-test report for the recorded policy reason, with no H07 wait. S4 safe human-authorized waiver remains valid; S5/H05 resume scoring remains correct with the historical refusal present; no extra verify or untracked model call; focused and cumulative regression gates pass. | **BLOCKED BY H08** | — |

**Required tracker coupling notes:** H08 extends H03's exact state/write-once `budget_started_at_utc` contract, H02's rooted interrupted invocation lifecycle, and H07's allow-listed authorization-wait accounting; segment closes protect *all* accepted evidence bytes/paths plus a verifiable immutable ledger projection, revalidated at every later opening. **H08b additionally couples normal `grill.md` stable per-decision IDs, `verify.md` factual failure types, `project-init.md` pinned waiver-policy/canonical-contract behavior, `waive.md` policy-first reason-coded refusals, and `review.md` refusal-history exclusion; static-gate checks protect all five command contracts. The `/grill` fixture seeds partially settled `DISC-001` **before its first call** and scores both blocked and resumed artifact checkpoints; the block is missing evidence/access, not an unanswered user decision. Hidden scoring expectations stay under the pre-existing H05-denied `docs/verification/smoke/**` path. Ineligible waiver requests stop with a persisted `POLICY_INELIGIBLE` refusal under `docs/verification/waiver-refusals/` before H07 authorization; active-waiver lookup ignores this sibling location and H05 focused regression proves that behavior; eligible requests retain H07 semantics and `AUTHORIZATION_MISSING` is a different blocked reason. H08b includes the scorer and unchanged bootstrap/project-init failure-type policy. H08 updates §3.5 direct-fix permission to declare the extra negative Luna call before H08b runs it. Both PRs are reviewed independently; **explicit PR-specific authorization is required before either merge**, and cumulative same-host regression remains guarded. The historical >66-minute attempt remains **reported; original ledger not recovered**. Numerical limits stay in the worksheet and versioned `profiles.json`, **not tracker rows**.

**Downstream dependency:** H11 waits for both H08 and H08b plus H09/H10; H12 waits for the completed H01–H11 set including H08b; H13 is a small real Kilo probe plus five targeted S5/S6 timings (reuse matching historical ledgers where possible); H14 follows H13 and any explicitly recorded, approved recalibration. No renumbering or premature work on downstream items. Execute H08, then H08b, one active coherent change at a time.

## 15. Final design status, exact decisions and implementation sequence

**Agreed and reconciled:** Six sequential checkpoint-bound segments; one logical qualification; unchanged 24 FULL scenario IDs; later authoritative 45-call matrix plus **three Sol** early acceptance calls and **two Luna** independent behavioral negatives = **50** planned successful calls. The *only* declared optional model invocation is one DeepSeek adversarial recheck, yielding **51** if its condition occurs. The non-waivable test **must reuse S2's existing direct-fix failed behavioral/unit-test report** against its policy already fixed at bootstrap and preserved by project-init; there is no planned or silently permitted fallback verification.

**New required H08b normal-command coupling:** Normal `/grill` must preserve preseeded stable per-decision IDs and structured states across blocked/resumed discovery, with **independent scoring after both real invocations**; its existing `DISCOVERY_BLOCKED` semantics remain restricted to missing evidence/access. Normal `/verify` must persist one factual bounded `Failure Type` for each blocking failure; it does **not** decide waiver eligibility. Normal `/project-init` must preserve the fixed bootstrap-approved waiver-policy source/hash/type mappings in project `AGENTS.md`, with the deterministic project-init helper—not the model—computing and writing the exact policy digest/type trace lines; it also provisions the refusal directory and fails closed when canonical Contract-v1 input is unavailable rather than inventing a substitute. Normal `/waive` must read exact failure evidence, use a repository-confined deterministic digest helper for persisted report/policy SHA-256 values, check failure-type policy before authorization, and **persist reason-coded `WAIVER_BLOCKED` records only in sibling `docs/verification/waiver-refusals/`**. The S2 release probe requires `POLICY_INELIGIBLE`; `AUTHORIZATION_MISSING` and `FAILURE_TYPE_UNAVAILABLE` remain distinct normal blocked reasons but do not satisfy that probe. Normal `/review` must search active waivers only under `docs/verification/waivers/` and never treat refusal history as active authorization. Static gates protect these coupled contracts. All H08b Luna-owned project-init/waive calls run in fresh scorer-hidden children; in particular both negative probes are independent of the parent orchestrator. S1/S2 segment close independently requires the matching immutable H08b score files to be schema-valid `PASS`. Continued S4/H07 positive authorization behavior remains an acceptance requirement.

**New required behavioral-scoring contract:** Preseed approved, partially settled normal `DISC-001` **before the first `/grill`**, and precommit immutable settled-ID/expected-value hashes in scorer-only data under `docs/verification/smoke/**`, which child permissions mechanically deny. Each scorer runs only after the corresponding completed `smoke_budget` invocation is present and receives the **actual parsed child status**, never an expected literal substituted by the orchestrator. The first `/grill` is deliberately blocked by a **withheld required referenced fact/artifact or its access**, not a withheld product answer; restore exactly that evidence and score the resumed normal `/grill` artifact against the unchanged hidden baseline. Whitespace-only formatting differences in settled text are canonicalized, while semantic value changes still fail. The separate main PRD probe withholds an approved product decision; resumed PRD scoring requires the prior blocked PASS, the revealed normal decision artifact, and a stable `PROD-DEC-001` reference in the PRD. The scorer does not require verbatim reproduction of the approved sentence, so faithful paraphrase remains valid. The user-selected direct-to-PRD branch runs with no discovery artifact; before restoration the scorer retains immutable bytes/hash of the actual direct PRD so segment evidence does not collapse to a bare hash. Project-init negative proof runs in an isolated snapshot with the project canonical Contract-v1 file absent and is restored byte-identically afterward.

**Initial enforceable PROVISIONAL limits:** S1 **80**, S2 **48**, S3 **38**, S4 **53**, S5 **36**, S6 **40** minutes, summing to **295** minutes. S2's **48** follows the agreed fixed formula; **47 is not arithmetically consistent** with unchanged 26.50-minute class slots, 5.00-minute residual and 1.5× headroom. The normal 50-call worksheet estimates **191.75** active minutes before headroom; one optional adversary makes **194.75**. These remain planning assumptions, not measured release-qualification results.

**Legacy precedence and evidence integrity:** The later authoritative §3.5 post-first-review matrix governs bounded negative restoration; H06 closure governs eight routing classifications and one representative real upstream handoff without eight lifecycle replays. All accepted historical evidence, including reports under Contract-v1-excluded paths, remains cryptographically protected across checkpoint restores and between-segment gaps. Atomic closure and H02/H03/H07 coupling remain unchanged. If any required behavior cannot pass within the specified 50/51 calls, block the relevant item and explicitly amend the controlled design instead of silently adding calls or weakening acceptance.

**Delivery sequence:** (1) approve this complete v6 design; (2) H08 segmented infrastructure in its own independently reviewed PR, **no merge without explicit authorization for that PR**; (3) H08b missing-evidence discovery and blocked/resumed PRD probes, stable normal `/grill` decision IDs with protected scorer, fixed fixture policy and `/waive` ordering plus machine-readable blocked-reason repair in a separate reviewed PR under the same rule; (4) original H09/H10 then H11/H12 dependency work; (5) targeted H13 timing for five S5/S6 classes and explicit config revision if warranted; (6) H14 real segmented FULL under the newly pinned configuration. Do not change an active run's pinned limits.

**Repository status:** Committed as the H08/H08b design authority on the H08 feature branch with tracker updates in the same draft PR. H08 implementation has not started; H08b remains blocked by H08. This document does not authorize any merge.
