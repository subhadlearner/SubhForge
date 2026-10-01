# SubhForge Delivery Timeline --- Sep 29 to Nov 30, 2026

> **Normative-home rule:** this file owns dates, milestones and schedule checkpoints only. Architecture rules live in `V0.2-ARCHITECTURE.md`, workflow semantics in `V0.2-WORKFLOW-CONTRACTS.md`, review evidence in `V0.2-ARCHITECTURE-REVIEW.md`, and qualification definitions in `V0.2-QUALIFICATION.md`.

## Fixed Objective

**Target: VidyaBeacon starts on December 1, 2026. Architecture correctness and required dogfood evidence are not sacrificed to force this date.**

December 1 may move only through an explicit decision at a defined
checkpoint (see Decision Checkpoints); it must never drift silently.

SubhForge work after the final release is limited to defects that
genuinely block VidyaBeacon. Non-blocking improvements move to later
releases.

## Delivery Plan

| Period | Working Sessions | Objective | Target Exit |
|---|---|---|---|
| Sep 29 -- Oct 4 | 5--6 | Complete planned v0.1.0 hardening | `stable_v0.1.0` |
| Oct 5 -- Oct 10 | 5--6 | Develop and harden the two already-defined v0.1.1 items | `stable_v0.1.1` |
| Oct 11 -- Oct 17 | 5--7 | Architecture Fitness Review for v0.2.0 | Architecture decision report |
| Oct 18 -- Oct 22 | 4--5 | Reconcile accepted architecture changes into the consolidated v0.2 architecture plan; freeze RC1--RC3 exit criteria | Revised v0.2 architecture plan and RC exit criteria accepted and frozen |
| Oct 23 -- Nov 5 | 11--12 | Use stable v0.1.1 to implement and harden revised LARGE workflow; build behavioural canary baseline | `v0.2.0-rc1` |
| Nov 6 -- Nov 12 | 5--6 | MediBot greenfield LARGE dogfood and resilience qualification | `v0.2.0-rc2` |
| Nov 13 -- Nov 18 | 4--5 | MediBot Evaluation Guardrails reconciliation/re-verification dogfood | `v0.2.0-rc3` |
| Nov 19 -- Nov 24 | 5--6 | Autonomous Market Intelligence scale/context qualification; final STANDARD + LARGE regression; docs/install/doctor/release qualification | `stable_v0.2.0` desired |
| Nov 25 -- Nov 30 | Protected buffer | Emergency stabilization only; no planned features | Protect Dec 1 |
| Dec 1 | --- | Begin VidyaBeacon | SubhForge becomes delivery infrastructure |

> **v0.1.1 scope is intentionally singular:** Ceremony Bypass for valid existing upstream authority. Design-time workflow contract validation + dry orchestration simulation remains wholly in v0.1.0 hardening (H11).

## Milestone Sequence

`stable_v0.1.0 → stable_v0.1.1 → Architecture Review → v0.2 Design Freeze → rc1 → rc2 → rc3 → stable_v0.2.0 → VidyaBeacon`

## Decision Checkpoints

At each checkpoint, explicitly decide: **hold December 1** or **move the
VidyaBeacon start date**. Weakening architecture, adversarial testing, or
dogfood evidence is not an option.

| Checkpoint | Date | Fires when |
|---|---|---|
| Review outcome | Oct 17 | Review returns `REWORK` and the correction materially consumes the v0.2 implementation/dogfood window |
| RC1 checkpoint | Nov 8 | `v0.2.0-rc1` has not met its frozen exit criteria **or reconciliation implementation is not far enough along to run the shared fixture** |
| Reconciliation readiness | Nov 12 | `V0.2-QUALIFICATION.md` §30.2 scenarios **6, 7 and 10** do not pass end to end |
| RC3 checkpoint | Nov 18 | `v0.2.0-rc3` has not met its frozen exit criteria, or dogfooding produced an accepted `ADD`/`MODIFY` not yet implemented |

Checkpoints judge against the RC exit criteria frozen on October 22.

## Hard Deadline

**November 24:** desired `stable_v0.2.0` release.

**November 25--30:** protected contingency buffer only.

**December 1:** VidyaBeacon target start, unless moved by an explicit
checkpoint decision. VidyaBeacon is pinned to the tested SubhForge release;
only genuinely blocking SubhForge defects may interrupt product work.
