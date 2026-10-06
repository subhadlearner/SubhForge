# SubhForge v0.2.0 — Discovery and Open Decisions

**Status:** Active pre-code discovery  
**Date:** 2026-10-06  
**Purpose:** Maintain only the still-valid decision frontier for SubhForge v0.2.0.

> This document is working discovery context, not product or architecture authority. Resolved decisions are promoted to the PRD, Architecture, Workflow Contracts or other owning authority and then closed here.

---

## 1. Confirmed Product Decisions

The following product-level decisions are already represented in the v0.2 PRD and are not open questions:

- SubhForge is a personal AI-assisted delivery system for Subhadeep, not a generic engineering product.
- LARGE flow covers Discovery → PRD → Architecture → Project → Epic → Feature → Spec → Implement → Verify → Review → Feature/Epic acceptance → Reconciliation.
- Requirement → Spec is core.
- Spec → reviewed implementation is core; automated PR creation is desirable but not a v0.2 release gate.
- PR → production-release orchestration is outside primary v0.2 scope.
- Production/runtime feedback re-enters through Bug/Fix or Change Triage/Reconciliation depending on whether accepted authority changed.
- Ideation may begin from conversation or Subhadeep-supplied documents/notes.
- Ideation may interview Subhadeep and must persist unanswered material questions as durable work items.
- The Research Agent is optional; Subhadeep may perform research directly.
- Discovery, PRD and Architecture are durable Git authority; operational work state lives in one operational work-graph backend.
- Agent responsibility is stable; model and harness assignments are replaceable/configurable.
- Human authority is reserved for consequential product, architecture, acceptance, waiver/risk and exception decisions.
- Routine Spec completion is machine-governed; human acceptance is at Feature/Epic level by default.
- v0.2 is a clean build and does not depend on v0.1.1, `/specbypassceremony`, or temporary `/arch-*` machinery.
- Stable v0.2.0 is targeted by December 31, 2026 so VidyaBeacon can begin in January 2027.

---

## 2. Discovery Rules

Each live question uses a stable `DQ-###` ID.

Every question records:

- **Question**
- **Why it matters**
- **Owner**
- **Blocking status**
- **Evidence/decision method**
- **Outcome** when resolved
- **Promote to** authoritative document when resolved

Statuses:

- **BLOCKING** — implementation/scope freeze cannot proceed safely without the answer.
- **NON_BLOCKING** — can be deferred without causing downstream invention.
- **CLOSED** — resolved and promoted to the owning authority.
- **SUPERSEDED** — no longer relevant because another accepted decision removed the need.

Do not preserve an old architecture-review question merely because it existed. A DQ survives only if it is still required by the current PRD.

---

## 3. Current Decision Frontier

### DQ-001 — Operational work-graph backend

**Question:** Should LARGE projects use Jira or GitHub Issues as the single live operational work-graph backend?

**Why it matters:** The selected backend must support Epics/Features/Specs/Bugs, dependency/governance representation, requirement traces, lifecycle state, reconciliation state, evidence references and low-friction status/next-work queries without creating another truth store.

**Owner:** Architect, with Subhadeep final decision.

**Status:** BLOCKING

**Evidence/decision method:** Compare the same representative work graph against both candidates. Evaluate at least hierarchy fit, dependency modelling, requirement traceability, PR/commit linkage, human usability, API/MCP support, least-privilege mutation, recovery/idempotency, query/context/token cost, export/recovery and vendor lock-in.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DQ-002 — Durable STANDARD/LARGE mode discovery

**Question:** What is the smallest durable mechanism that allows commands to discover a project's selected mode without repeatedly asking Subhadeep?

**Why it matters:** Mode must not silently change or depend on chat/session memory. The previous `PROJECT-001.md` existence rule is not carried forward.

**Owner:** Architect.

**Status:** BLOCKING

**Evidence/decision method:** Prefer a single durable, inspectable project-level marker/configuration that does not create a competing state store and works when Kilo/model tooling is unavailable.

**Outcome:** Open.

**Promote to:** Architecture / project bootstrap contract.

---

### DQ-003 — Minimal operational backend schema

**Question:** After DQ-001 selects the backend, what exact hierarchy, fields, labels/metadata and relationships are required—no more?

**Why it matters:** Over-modeling the backend would recreate the document/state overload v0.2 is trying to remove.

**Owner:** Architect.

**Status:** BLOCKING after DQ-001.

**Evidence/decision method:** Derive fields only from accepted PRD/workflow requirements: identity, parentage, lifecycle, FR/NFR traceability, Contains/Governed-by/Depends-on semantics, blockers/escalations, reconciliation holds/state, suite ownership and evidence/implementation references.

**Outcome:** Open.

**Promote to:** Architecture and Workflow Contracts where semantics apply.

---

### DQ-004 — Git ↔ operational-backend consistency

**Question:** What is the minimum mechanism needed to detect meaningful drift between canonical Git authority and operational work state without creating a second source of truth?

**Why it matters:** Reconciliation, readiness and status become unsafe if work metadata silently refers to stale or missing authority.

**Owner:** Architect.

**Status:** BLOCKING

**Evidence/decision method:** Identify only mechanically provable identity/reference/freshness checks. Avoid a broad synchronization subsystem.

**Outcome:** Open.

**Promote to:** Architecture / verification mechanics.

---

### DQ-005 — Reconciliation physical representation

**Question:** How should reconciliation packages, held scope, partial APPLY state and overlap/conflict detection be represented in the selected backend/Git split?

**Why it matters:** FR-016 requires safe pause, approval, retry/idempotency and unaffected-work preservation, but the PRD intentionally does not prescribe storage details.

**Owner:** Architect.

**Status:** BLOCKING

**Evidence/decision method:** Resolve after DQ-001/DQ-003. Prefer the smallest representation that supports deterministic pre/postconditions, resume and conflict detection.

**Outcome:** Open.

**Promote to:** Architecture + Workflow Contracts.

---

### DQ-006 — Requirement and evidence linkage representation

**Question:** How are stable FR/NFR traces, acceptance criteria, verification evidence references and implementation/PR links represented across Git and the selected operational backend?

**Why it matters:** Traceability must support impact discovery and evidence freshness without copying authoritative requirement text into multiple stores.

**Owner:** Architect.

**Status:** BLOCKING

**Evidence/decision method:** Persist identifiers/references, not duplicated authority. Prove common lookups needed by readiness, reconciliation and status.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DQ-007 — Protected Architecture Invariant representation

**Question:** What is the simplest durable representation for Protected Architecture Invariants and their DETERMINISTIC / SEMANTIC / MIXED enforcement mapping?

**Why it matters:** The PRD requires protected architecture but not a heavyweight fitness-function subsystem.

**Owner:** Architect.

**Status:** BLOCKING

**Evidence/decision method:** Prefer human-readable architecture authority plus a small machine-readable contract only where deterministic verification needs it.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DQ-008 — Logical agent/capability → physical command mapping

**Question:** What exact Kilo commands/agents implement the logical roles in the PRD, and which roles should remain capabilities rather than dedicated agents?

**Why it matters:** The product needs clear ownership without multiplying agents merely to mirror every noun in the design.

**Owner:** Architect.

**Status:** BLOCKING before implementation plan.

**Evidence/decision method:** Minimize physical agents while preserving one owner per responsibility, authority boundaries, interaction contracts and resumability.

**Outcome:** Open.

**Promote to:** Architecture / implementation plan.

---

### DQ-009 — Interaction-mode implementation

**Question:** What is the simplest reliable way for SubhForge to distinguish owning-workflow interview/approval interactions from Subhadeep-initiated explain/challenge conversations without allowing conversation context to expand mutation authority?

**Why it matters:** The PRD defines the behavior but not the physical mechanism.

**Owner:** Architect.

**Status:** BLOCKING before agent implementation.

**Evidence/decision method:** Prefer derivation from invoked command/target/owning workflow and durable target identity over a new conversational state engine.

**Outcome:** Open.

**Promote to:** Architecture / agent contracts.

---

### DQ-010 — Optional PR creation

**Question:** Should v0.2 implement automatic PR creation after reviewed Spec delivery, or leave PR preparation/manual creation as the initial behavior?

**Why it matters:** It improves convenience but is explicitly not a release gate and must not distract from core delivery/reconciliation reliability.

**Owner:** Subhadeep with implementation recommendation from Architect.

**Status:** NON_BLOCKING

**Evidence/decision method:** Implement only if GitHub integration makes it small, safe and low-maintenance after core Spec delivery works.

**Outcome:** Open.

**Promote to:** Architecture/implementation plan if accepted.

---

### DQ-011 — Dry orchestration / contract validation

**Question:** Is any dedicated dry-orchestration/contract validator still necessary in v0.2, and if so what is the smallest useful form?

**Why it matters:** v0.1 showed that validation infrastructure can become another framework requiring its own maintenance.

**Owner:** Architect.

**Status:** NON_BLOCKING until verification design; BLOCKING before qualification freeze.

**Evidence/decision method:** Retain only if it protects an accepted failure mode more cheaply than deterministic tests, focused integration, canary or dogfood.

**Outcome:** Open.

**Promote to:** Qualification/Architecture if retained; otherwise close as unnecessary.

---

### DQ-012 — Minimum observability for handoffs and recovery

**Question:** What minimum durable diagnostics are required for agent handoffs, backend mutations, blockers, reconciliation and recovery so that Subhadeep normally does not have to inspect SubhForge internals?

**Why it matters:** NFR-007 requires diagnosability without building a full observability platform.

**Owner:** Architect.

**Status:** BLOCKING before implementation plan.

**Evidence/decision method:** Define only the fields/events needed to answer what happened, why work stopped, what authority/evidence was used, and what safe next action exists.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DQ-013 — Skills baseline

**Question:** Which reusable engineering skills genuinely deserve global SubhForge scope for v0.2?

**Why it matters:** Skills improve engineering quality but increase context, maintenance and supply-chain/provenance surface.

**Owner:** Architect.

**Status:** NON_BLOCKING for initial skeleton; BLOCKING before final scope freeze for any skill claimed as baseline.

**Evidence/decision method:** Admit only skills with real recurring need, credible provenance, non-duplication, acceptable context/tool cost and removal impact.

**Outcome:** Open.

**Promote to:** Architecture / installation manifest.

---

### DQ-014 — MCP/integration baseline

**Question:** Which integrations are baseline SubhForge dependencies versus project-specific optional tools?

**Why it matters:** The operational work backend and GitHub access are likely core, while cloud/vendor integrations should not become globally privileged by default.

**Owner:** Architect.

**Status:** BLOCKING for baseline integrations only.

**Evidence/decision method:** Apply least privilege, trusted-source preference, bounded action, failure degradation and removability.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DQ-015 — STANDARD compatibility boundary

**Question:** What minimum STANDARD behavior must be frozen and regression-tested while LARGE is rebuilt?

**Why it matters:** The PRD requires that LARGE evolution not silently regress STANDARD, but v0.2 is a clean build and should not drag forward every v0.1 implementation detail.

**Owner:** Architect + qualification design.

**Status:** BLOCKING before scope/DoD freeze.

**Evidence/decision method:** Preserve user-visible capability/invariants that still matter, not obsolete v0.1 internal contracts.

**Outcome:** Open.

**Promote to:** Architecture + Qualification.

---

## 4. Pre-Code Context and Closure Gates

This section replaces the former active `V0.2-PRE-CODE-CHECKLIST.md`. Discovery now owns the live pre-code frontier because unresolved research/decision work and readiness to begin implementation are part of the same decision context.

Dates remain owned by `design/SUBHFORGE-DELIVERY-TIMELINE.md`; accepted product/architecture/workflow/qualification rules remain in their own authority documents.

### 4.1 Completed pre-code context

The following context is already settled and does not need separate active tracking:

- **v0.1 frozen at H10.** H11–H14 were cancelled/superseded; the frozen research baseline remains available through Git history/tag `research_v_0.1_h10`.
- **Temporary cost-controlled construction workflow established.** `design/V0.2-TEMPORARY-BUILD-WORKFLOW.md` governs current build-time cost/provider controls only.
- **One canonical v0.2 pre-code lineage retained:** `feature/v0.2.0`.
- **v0.1 lessons captured** as historical audit input; they are not v0.2 product authority.
- **Clean active design authority created/reconciled:** PRD, Discovery, Architecture, Workflow Contracts and Qualification.
- **README authority map and Delivery Timeline reconciled** to the clean document structure and the Dec 31, 2026 / Jan 2027 delivery direction.

These facts may be revisited only if new evidence materially contradicts them.

### 4.2 Current pre-code state

**Current activity:** joint review of the clean PRD, Discovery, Architecture, Workflow Contracts and Qualification set.

Implementation must not begin merely because the documents exist. Pre-code closes only when the gates below pass.

### 4.3 Pre-code closure gates

| Gate | Requirement | Current state |
|---|---|---|
| **PCG-01 — Clean design review** | Subhadeep accepts the clean PRD/Discovery/Architecture/Workflow/Qualification set as a coherent baseline. | **OPEN** |
| **PCG-02 — Scope cut** | Define what must ship in stable v0.2.0 versus later versions; preserve required safety/dogfood evidence. | **BLOCKED by PCG-01** |
| **PCG-03 — Blocking Discovery closure** | Close/promote every blocking in-scope `DQ-###`; explicitly defer only non-blocking questions that are safe to postpone. | **BLOCKED by PCG-02** |
| **PCG-04 — Scope + Definition of Done freeze** | Reconcile the PRD DoD/non-goals with resolved Discovery decisions and freeze the release boundary. | **BLOCKED by PCG-03** |
| **PCG-05 — Walking skeleton defined** | Define the smallest real end-to-end LARGE slice from idea/document intake through reviewed Spec delivery with durable state/resume. | **BLOCKED by PCG-04** |
| **PCG-06 — Verification strategy frozen** | Map each required failure risk to the cheapest sufficient deterministic/integration/canary/dogfood evidence layer; resolve `DQ-011`. | **BLOCKED by PCG-05** |
| **PCG-07 — Dogfood path frozen** | Accept MediBot greenfield, Evaluation Guardrails reconciliation and scale/context qualification entry/exit evidence. | **BLOCKED by PCG-06** |
| **PCG-08 — Implementation plan ready** | Produce dependency-aware, acceptance-driven work units executable from fresh sessions/durable authority. | **BLOCKED by PCG-04–07** |
| **PCG-09 — Final pre-code approval** | Confirm no known unowned blocker, unacceptable cost/complexity risk or unresolved release-critical assumption remains. | **BLOCKED by prior gates** |
| **PCG-10 — Begin implementation** | Create/use the implementation branch and begin product code only after PCG-01–09 pass. | **BLOCKED** |

### 4.4 Gate operating rules

- A gate closes only with durable evidence in Discovery or the authority document that owns the result.
- Closing a `DQ-###` requires promotion into its owning authority; a chat conclusion is not closure.
- Scope added after PCG-04 requires an explicit trade-off or schedule decision.
- Research/POCs exist only to close named DQs or prove a named gate; prototype code does not automatically become product code.
- Real dogfood is release work, not optional polish.
- If a gate starts expanding into a subsystem whose cost exceeds the failure it protects against, stop and simplify/re-scope before proceeding.
- No separate pre-code tracker should be recreated unless Discovery demonstrably becomes unable to represent the live decision frontier and closure gates cleanly.

---

## 5. Explicitly Closed / Not Carried Forward

These are not discovery questions for v0.2 unless new evidence reopens them:

- Whether v0.2 should be implemented through stable v0.1.1 — **closed: no; clean build**.
- Whether `/specbypassceremony` is the v0.2 admission path — **closed: no**.
- Whether temporary `/arch-*` review commands/agents are required — **closed: no**.
- Whether LARGE operational Epic/Feature/Spec state should be a Markdown repository tree — **closed: no**.
- Whether SQLite should be a second workflow state store — **closed: no**.
- Whether Jira is selected by default — **closed: no; evidence required**.
- Whether an entire Epic must finish before another can progress — **closed: no; use truthful DAG eligibility**.
- Whether Planner may resolve missing upstream product/architecture intent by interviewing Subhadeep directly — **closed: no; route to owning authority**.
- Whether model/provider/harness identity defines SubhForge semantics — **closed: no**.
- Whether post-PR production-release orchestration is required in v0.2 — **closed: no**.
- Whether every production defect requires reconciliation — **closed: no; defects against existing authority use Bug/Fix, authority changes reconcile**.

---

## 6. Closure Rule

A discovery question is closed only when:

1. sufficient evidence exists;
2. Subhadeep decides when human authority is reserved;
3. the accepted result is promoted to its authoritative home;
4. affected questions/requirements are reconciled;
5. this record is marked CLOSED or SUPERSEDED with the destination reference.

Git history preserves prior discovery; this document should remain small and current.
