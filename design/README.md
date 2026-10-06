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
| [discovery/SUBHFORGE-V0.2-DISCOVERY.md](discovery/SUBHFORGE-V0.2-DISCOVERY.md) | **Single pre-code Discovery work frontier, not normative product authority** — live `DI-###` research, decisions, design/review work and final pre-code gate, with owners, dependencies, status and promotion destination |
| [architecture/SUBHFORGE-V0.2-ARCHITECTURE.md](architecture/SUBHFORGE-V0.2-ARCHITECTURE.md) | **Structural architecture authority** — authority/execution planes, protected invariants, logical agents, traceability architecture, harness/model/tool boundaries, context and implementation dependency structure |
| [workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md](workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md) | **Lifecycle/workflow authority** — lifecycle states, readiness, grooming, dependencies, delivery, verification, escalation, change triage, reconciliation, status/resume and evidence semantics |
| [qualification/SUBHFORGE-V0.2-QUALIFICATION.md](qualification/SUBHFORGE-V0.2-QUALIFICATION.md) | **Proof/release authority** — validation layers, regressions, dogfood, adversarial cases, release evidence and stable-release qualification |
| [SUBHFORGE-DELIVERY-TIMELINE.md](SUBHFORGE-DELIVERY-TIMELINE.md) | **Schedule authority only** — milestone dates, delivery checkpoints and protected stabilization window |

---

## 2. Supporting / Transitional Documents

These are useful inputs or temporary operating aids. They do **not** override the active authority set.

| Document | Purpose |
|---|---|
| Frozen v0.1 H01–H10 research baseline in Git history | Historical input only; it does not override the active authority set. Archived material is outside the current review scope. |

---

## 3. Superseded / Pending-Cleanup Artifacts

The following files may remain temporarily so the clean documents can be reviewed against them, but they are **not current v0.2 authority**:

- `old/V0.2-PRE-CODE-CHECKLIST.md` — archived historical tracker; live pre-code work now lives in Discovery
- `old/V0.2-TEMPORARY-BUILD-WORKFLOW.md` — archived construction/cost evidence; durable constraints now live in the PRD

- Earlier architecture, workflow, qualification and review/tooling generations, where retained in Git history or the archive.

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
2. **Unresolved pre-code research/decision/design work:** Discovery until resolved; no downstream document may guess or bypass the required outcome.
3. **Structural solution:** Architecture.
4. **Lifecycle/workflow behavior:** Workflow Contracts.
5. **How behavior is proven:** Qualification.
6. **Dates/milestones:** Delivery Timeline.
7. **Pre-code decision frontier / implementation-readiness gates:** Discovery.

A resolved Discovery question must be promoted to its authoritative home before it is considered closed.

Git history preserves earlier wording; do not create parallel “v2/v3” authority documents for normal evolution.

PRD owns goals, agent responsibilities, model-selection requirements and operating policies. Architecture realizes them through components, stores, interfaces, execution paths and enforcement seams; it references those requirements rather than keeping another role-to-model or product-policy table. Concrete model versions/defaults belong in the central execution-configuration map defined by FR-021, not in agent files or architectural prose.

---

## 5. Shared Decision Status Vocabulary

| Status | Meaning |
|---|---|
| **ACCEPTED** | Current agreed rule/direction. Reopen only because of contradiction, implementation limitation, new evidence, dogfood failure, meaningful cost/operational problem or explicit human revision. |
| **REVIEW** | Direction/semantics are partially established but a named `DI-###` or evidence gate must close before implementation/release depends on the unresolved detail. |
| **DEFERRED** | Intentionally outside current v0.2 scope unless evidence reopens it. |
| **NON-GOAL** | Explicitly excluded from v0.2. |

Discovery Items use their own work-status vocabulary:

- **OPEN**
- **ACTIVE**
- **BLOCKED**
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
- `DI-###`
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

---

## 9. Next Steps Before Coding

Use this as a navigation checklist. [Discovery](discovery/SUBHFORGE-V0.2-DISCOVERY.md) remains the single live tracker for owners, dependencies, evidence, status and closure; do not maintain a second completion checklist here. These steps do not themselves accept the design or authorize implementation.

| Order | Step / Discovery items | What Subhadeep should do | Required result |
|---|---|---|---|
| 1 | Accept the design baseline — DI-001 | Review the active documents and pending design PRs (including [PR #26](https://github.com/subhadlearner/SubhForge/pull/26)); approve the coherent baseline and merge accepted changes. | Record explicit baseline acceptance in DI-001 after any corrections are promoted. A PR merge alone does not close the DI. |
| 2 | Set the provisional release boundary — DI-002 | Confirm must-ship versus deferred scope and which DIs are release-blocking. Preserve required safety, STANDARD compatibility and dogfood proof. | Record provisional classification; keep DI-002 open until the later final scope/DoD freeze. |
| 3 | Choose the operational backend — DI-003 | Compare Jira and GitHub Issues against the same small representative graph, then decide using capability, usability, recovery and cost evidence. | One backend and minimum schema; credible pagination/conflict, lost-response, export/restore and discovery-bootstrap evidence. |
| 4 | Settle setup and execution contracts — DI-004, DI-007, DI-008, DI-010, DI-011 | Review the smallest supported Windows setup, mode/templates, protected-invariant representation, harness/agent routing, central model map, admitted skills/MCPs and STANDARD boundary. | Physical choices and authority/permission limits promoted to Architecture/Workflow. Include document-to-Discovery intake and actual model-selection feasibility, not prompt-only claims. Follow each DI's prerequisites; backend-specific decisions use DI-003. |
| 5 | Settle consistency and recovery — DI-005 → DI-006 → DI-009 | Review cross-plane identity, accepted revisions, traces, composed implementation/evidence, human acceptance, reconciliation holds/retry/obligations and useful diagnostics. | Safe mutation/completion and recovery contracts with concrete backend representation; no second live authority store or stale evidence used as success. |
| 6 | Define the first slice, then its proof — DI-014 → DI-013 | Accept the minimal walking skeleton and its necessary foundations. Then accept requirement coverage, realistic execution/cost/context/intervention limits and qualification/dogfood design. | Bounded entry/exit behavior and an executable proof strategy. Plan an uninterrupted positive baseline before expanding expensive failure scenarios; executing release dogfood belongs after implementation. |
| 7 | Freeze scope and prepare work — finalize DI-002, then DI-015 | Freeze the reconciled release scope/DoD after its required design decisions close; review the dependency-aware implementation plan. | Bounded acceptance-driven work in the selected work system, with walking-skeleton work first, test ownership, explicit prerequisites and fresh-session context. |
| 8 | Authorize implementation — DI-016 | Confirm all release-critical DIs are closed/promoted, remaining deferrals are explicitly safe, and the cost, qualification strategy and implementation plan are acceptable. | Record Subhadeep's explicit final pre-code approval. Only then begin production implementation of the first planned slice. |

DI-012 (automatic PR creation) remains optional/non-blocking unless explicitly brought into scope. Assess it once core delivery/GitHub integration is understood; manual PR handoff remains valid.

The order is dependency-led, not a requirement to finish every independent question serially. Our default is to settle one bounded issue at a time; unresolved details remain visible in their existing DIs rather than being guessed during coding. Bounded feasibility research/probes may inform a decision before DI-016, but they are not the production implementation or permission to bypass cost/access constraints.

For each decision, the agent prepares evidence, options, a recommendation and trade-offs; Subhadeep settles consequential intent/cost/authority choices. Promote the accepted outcome to its owning document and update Discovery before moving on. Independent ChatGPT/Claude challenge may support material architecture decisions without requiring both models for routine work.

**Immediate next action:** accept DI-001's baseline and record DI-002's provisional release classification; then evaluate DI-003. **Coding starts after DI-016**, with the walking skeleton and cheap checks, followed by the bounded positive-path proof and incremental delivery.
