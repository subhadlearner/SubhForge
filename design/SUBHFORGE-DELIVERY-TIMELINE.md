# SubhForge v0.2.0 — Delivery Timeline

**Status:** Active delivery plan  
**Updated:** 2026-10-06  
**Hard target:** `stable_v0.2.0` by **December 31, 2026**  
**Next product:** VidyaBeacon begins **January 2027**

> Schedule is a delivery constraint, not permission to weaken correctness, recovery, required dogfood, or release evidence.

---

## 1. Delivery Objective

SubhForge v0.2.0 must be complete enough by December 31, 2026 to become trusted delivery infrastructure for VidyaBeacon.

“Complete” means more than feature implementation. The release must include:

- accepted PRD, Architecture, Workflow and Qualification authorities;
- all blocking Discovery decisions resolved and promoted;
- a working LARGE lifecycle from Discovery through Epic acceptance;
- reliable status, resume, dependency and evidence behavior;
- safe change triage and reconciliation;
- required greenfield, reconciliation and scale/context dogfood;
- STANDARD compatibility protection;
- acceptable runtime, context and provider cost;
- install/bootstrap/doctor/release readiness;
- sufficient diagnostics and recovery;
- no dependency on temporary construction/review scaffolding.

After stable v0.2.0, only genuinely blocking SubhForge defects should interrupt VidyaBeacon delivery. Non-blocking improvements move to later SubhForge releases.

---

## 2. Delivery Plan

| Period | Objective | Required Exit |
|---|---|---|
| **Oct 6–12** | Review the clean PRD, Discovery, Architecture, Workflow and Qualification set; correct contradictions and remove stale assumptions | Core design set accepted for continued design closure |
| **Oct 13–20** | Resolve the blocking Discovery questions needed for implementation: operational backend, mode discovery, minimum backend schema, consistency model, reconciliation representation, trace/evidence representation, protected-invariant representation, physical agent/capability mapping, interaction-mode implementation, baseline observability and STANDARD boundary | Blocking architectural decisions closed and promoted |
| **Oct 21–25** | Freeze v0.2 scope/Definition of Done; finalize walking skeleton, verification strategy, dogfood path and implementation work plan | **Pre-code gate passed** |
| **Oct 26–Nov 8** | Implement foundation + walking skeleton: project/mode bootstrap, authority planes, work backend, FR/NFR identity/traceability, core lifecycle, dependency DAG, status/work-plan/resume | End-to-end skeleton operational |
| **Nov 9–22** | Implement LARGE planning and delivery: Ideation/document intake, optional Research, PRD/Architecture admission, Epic/Feature/Spec grooming/readiness, implement/verify/review, Feature/Epic verification and acceptance | Greenfield LARGE lifecycle implementation complete |
| **Nov 23–Dec 6** | Implement change triage, production-feedback routing, reconciliation analysis/holds/apply/idempotency/evidence invalidation/re-verification; complete bounded observability/recovery | Reconciliation implementation complete |
| **Dec 7–13** | MediBot greenfield LARGE dogfood; repair framework defects discovered by real delivery | Greenfield dogfood accepted |
| **Dec 14–20** | MediBot Evaluation Guardrails reconciliation dogfood and adversarial recovery scenarios | Reconciliation dogfood accepted |
| **Dec 21–24** | Scale/context dogfood, STANDARD regression, behavior-drift canary, runtime/token/provider-cost checks | Release-candidate evidence complete |
| **Dec 25–28** | Install/bootstrap/doctor/release checks, documentation consistency, cleanup of temporary/superseded scaffolding | Stable candidate ready |
| **Dec 29–31** | **Protected stabilization buffer** — defect correction and required requalification only; no planned new scope | `stable_v0.2.0` |
| **January 2027** | Begin VidyaBeacon using the pinned tested SubhForge release | SubhForge becomes delivery infrastructure |

---

## 3. Milestone Sequence

```text
Clean design review
→ Blocking Discovery closure
→ Scope / DoD freeze
→ Pre-code gate
→ Walking skeleton
→ LARGE delivery lifecycle
→ Reconciliation
→ Greenfield dogfood
→ Reconciliation dogfood
→ Scale / regression qualification
→ Stable v0.2.0
→ VidyaBeacon
```

---

## 4. Schedule Protection Rules

1. **December 31 is the hard delivery target**, but correctness and required release evidence are not silently weakened to preserve it.
2. New scope after scope freeze requires an explicit trade-off: remove/defer something of comparable cost or move the plan deliberately.
3. A Discovery question becomes schedule-critical only when implementation cannot proceed safely without it.
4. Dogfood is release work, not optional polish.
5. Synthetic smoke does not substitute for real-project dogfood.
6. The Dec 29–31 window is a **stabilization buffer**, not planned feature-development capacity.
7. Any material risk to the December 31 target must be surfaced when discovered rather than hidden until release week.

---

## 5. Delivery Checkpoints

| Checkpoint | Target | Question |
|---|---|---|
| **Design review accepted** | Oct 12 | Are PRD, Discovery, Architecture, Workflow and Qualification internally coherent enough to close remaining decisions? |
| **Blocking Discovery closed** | Oct 20 | Are all decisions required for the implementation foundation resolved and promoted to their authority homes? |
| **Pre-code gate** | Oct 25 | Is scope frozen, DoD explicit, walking skeleton designed, qualification path defined and implementation plan ready? |
| **Walking skeleton checkpoint** | Nov 8 | Can a minimal real project traverse the core authority/work lifecycle and resume from durable state? |
| **LARGE lifecycle checkpoint** | Nov 22 | Can normal greenfield work progress through Spec implementation/review and Feature/Epic verification without hidden chat dependence? |
| **Reconciliation checkpoint** | Dec 6 | Can material authority change be analysed, approved, safely applied, resumed and re-verified against the real work/evidence model? |
| **Greenfield dogfood checkpoint** | Dec 13 | Has MediBot exposed and survived the real end-to-end LARGE workflow? |
| **Reconciliation dogfood checkpoint** | Dec 20 | Has Evaluation Guardrails proven the real reconciliation path and required adversarial cases? |
| **Release-candidate checkpoint** | Dec 28 | Are scale/context, STANDARD regression, behavioral canary, cost/runtime, install/doctor and cleanup evidence acceptable? |
| **Stable release** | Dec 31 | Is SubhForge trustworthy enough to pin for VidyaBeacon? |

---

## 6. Explicitly Superseded Schedule

The former plan targeting:

- stable v0.1.1;
- Architecture Fitness Review;
- v0.1.1-driven v0.2 implementation;
- `/specbypassceremony`;
- stable v0.2.0 around November 24; and
- VidyaBeacon on December 1, 2026

is **superseded**.

The current authoritative delivery direction is:

> **Clean-build SubhForge v0.2.0, fully dogfooded and qualified by December 31, 2026; begin VidyaBeacon in January 2027.**
