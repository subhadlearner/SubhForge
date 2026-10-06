# SubhForge v0.2 Design

This directory contains the active design authority and supporting evidence for SubhForge v0.2.0.

The document system follows one rule:

> **Every decision has one authoritative home. Other documents reference it; they do not redefine it.**

The design set is intentionally being simplified. Old review/tooling documents may remain temporarily for comparison/history, but they are not allowed to compete with the clean authority set below.

---

## 1. Active Authority Map

| Document | Authority |
|---|---|
| [prd/SUBHFORGE-V0.2-PRD.md](prd/SUBHFORGE-V0.2-PRD.md) | **Product authority** — what SubhForge v0.2 must do: goals, lifecycle boundary, functional/non-functional requirements, agent responsibilities, handover expectations, guardrails, non-goals and Definition of Done |
| [discovery/SUBHFORGE-V0.2-DISCOVERY.md](discovery/SUBHFORGE-V0.2-DISCOVERY.md) | **Decision frontier, not normative product authority** — confirmed context, live `DQ-###` questions, assumptions, owners, blocking status and closure/promotion destination |
| [architecture/SUBHFORGE-V0.2-ARCHITECTURE.md](architecture/SUBHFORGE-V0.2-ARCHITECTURE.md) | **Structural architecture authority** — authority/execution planes, protected invariants, logical agents, traceability architecture, harness/model/tool boundaries, context and implementation dependency structure |
| [workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md](workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md) | **Lifecycle/workflow authority** — lifecycle states, readiness, grooming, dependencies, delivery, verification, escalation, change triage, reconciliation, status/resume and evidence semantics |
| [qualification/SUBHFORGE-V0.2-QUALIFICATION.md](qualification/SUBHFORGE-V0.2-QUALIFICATION.md) | **Proof/release authority** — validation layers, regressions, dogfood, adversarial cases, release evidence and stable-release qualification |
| [SUBHFORGE-DELIVERY-TIMELINE.md](SUBHFORGE-DELIVERY-TIMELINE.md) | **Schedule authority only** — milestone dates, delivery checkpoints and protected stabilization window |

---

## 2. Supporting / Transitional Documents

These are useful inputs or temporary operating aids. They do **not** override the active authority set.

| Document | Purpose |
|---|---|
| [V0.1-LESSONS-LEARNED.md](V0.1-LESSONS-LEARNED.md) | Historical evidence from the frozen v0.1 H01–H10 research baseline. It informs decisions but is not v0.2 product authority. |
| [V0.2-TEMPORARY-BUILD-WORKFLOW.md](V0.2-TEMPORARY-BUILD-WORKFLOW.md) | Temporary construction workflow covering model/provider cost discipline and build-time operating rules. It must remain removable without changing SubhForge product semantics. |

---

## 3. Superseded / Pending-Cleanup Artifacts

The following files may remain temporarily so the clean documents can be reviewed against them, but they are **not current v0.2 authority**:

- `old/V0.2-PRE-CODE-CHECKLIST.md` — archived historical tracker; live pre-code gates now live in Discovery

- `V0.2-ARCHITECTURE.md`
- `V0.2-WORKFLOW-CONTRACTS.md`
- `V0.2-QUALIFICATION.md`
- `V0.2-ARCHITECTURE-REVIEW.md`
- `V0.2-ARCHITECTURE-REVIEW-TOOLING.md`
- `V0.2-IMPLEMENTATION-TOOLING.md`

They should be removed or archived after the clean authority set is reviewed and accepted and any genuinely unique valid context has been promoted.

In particular, these older artifacts must not reintroduce superseded directions such as:

- v0.1.1 as the implementation bridge for v0.2;
- `/specbypassceremony`;
- temporary `/arch-*` architecture-review machinery;
- the former November 24 stable-release / December 1 VidyaBeacon schedule.

---

## 4. Authority Precedence

When documents appear to conflict, use this order by subject:

1. **Product intent / requirement:** PRD.
2. **Unresolved question:** Discovery until resolved; no downstream document may guess the answer.
3. **Structural solution:** Architecture.
4. **Lifecycle/workflow behavior:** Workflow Contracts.
5. **How behavior is proven:** Qualification.
6. **Dates/milestones:** Delivery Timeline.
7. **Pre-code decision frontier / implementation-readiness gates:** Discovery.

A resolved Discovery question must be promoted to its authoritative home before it is considered closed.

Git history preserves earlier wording; do not create parallel “v2/v3” authority documents for normal evolution.

---

## 5. Shared Decision Status Vocabulary

| Status | Meaning |
|---|---|
| **ACCEPTED** | Current agreed rule/direction. Reopen only because of contradiction, implementation limitation, new evidence, dogfood failure, meaningful cost/operational problem or explicit human revision. |
| **REVIEW** | Direction/semantics are partially established but a named `DQ-###` or evidence gate must close before implementation/release depends on the unresolved detail. |
| **DEFERRED** | Intentionally outside current v0.2 scope unless evidence reopens it. |
| **NON-GOAL** | Explicitly excluded from v0.2. |

Discovery additionally uses:

- **BLOCKING**
- **NON_BLOCKING**
- **CLOSED**
- **SUPERSEDED**

as defined in the Discovery document.

---

## 6. Design Flow

```text
Discovery
   ↓ resolves/promotes
PRD
   ↓
Architecture
   ↓
Workflow Contracts
   ↓
Qualification
   ↓
Implementation / Dogfood / Release
```

This is an **authority relationship**, not a rule that every change must replay every stage.

Existing valid authority may be admitted directly where the Workflow contract allows it. Later material changes use Change Triage/Reconciliation rather than blindly restarting Discovery.

---

## 7. Stable Identity Rule

Stable identities such as:

- `FR-###`
- `NFR-###`
- `DQ-###`
- work-item IDs;
- reconciliation/escalation/blocker IDs

are durable references and should not be renumbered merely for cosmetic organization.

Document section numbers inherited from earlier design work may remain non-contiguous where changing them would create unnecessary reference churn. Section numbering itself is not authority.

---

## 8. Cleanup Rule

Before deleting a superseded artifact:

1. confirm every still-valid unique decision has an authoritative home;
2. confirm no active document still depends on the obsolete artifact;
3. remove or redirect stale cross-references;
4. rely on Git history for obsolete reasoning/history rather than retaining competing live documents.

The end state should be a **small design surface** that Subhadeep and SubhForge can navigate without ambiguity.
