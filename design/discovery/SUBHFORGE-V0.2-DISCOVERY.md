# SubhForge v0.2.0 — Discovery and Open Work

**Status:** Active pre-code discovery  
**Date:** 2026-10-06  
**Purpose:** Maintain the single live frontier of unresolved research, design, review and pre-code work required to build SubhForge v0.2.0.

> This document is working discovery context, not product or architecture authority. A Discovery Item closes only when its accepted result is promoted to the PRD, Architecture, Workflow Contracts, Qualification, Timeline or other owning authority as appropriate.

---

## 1. Confirmed Product Decisions

The following product-level decisions are already represented in the v0.2 PRD and are not open Discovery Items:

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

## 2. Discovery Item Model

All unresolved SubhForge-building work uses one stable identity:

`DI-###` — **Discovery Item**

A Discovery Item may be research, a decision, design work, review work or a final gate. These are different kinds of work, not different tracking systems.

Each DI records:

- **Kind** — `RESEARCH`, `DECISION`, `DESIGN`, `REVIEW`, or `GATE`;
- **Work / Question**;
- **Why it matters**;
- **Owner**;
- **Status**;
- **Depends on**;
- **Release criticality** — release-blocking or explicitly safe to defer, as classified provisionally/finally by DI-002; this is separate from work status;
- **Evidence / completion method**;
- **Outcome**;
- **Promote to**.

Statuses:

- **OPEN** — ready to be taken when its prerequisites allow.
- **ACTIVE** — currently being worked.
- **BLOCKED** — cannot proceed until named prerequisites close.
- **NON_BLOCKING** — useful but safe to defer beyond the v0.2 release if necessary.
- **CLOSED** — completed and the accepted outcome is promoted to its authoritative home.
- **SUPERSEDED** — no longer needed because another accepted result removed the need.

Rules:

1. A DI exists only when it represents distinct work or a distinct consequential decision.
2. Do not create a DI whose only purpose is “all other DIs are closed”; that is derived state.
3. Closely coupled questions that will be researched/decided together should be one DI with explicit sub-decisions.
4. A chat conclusion is not DI closure.
5. A DI closes only after its accepted outcome is durable in the owning authority.
6. Git history preserves earlier Discovery wording; completed historical process does not need a permanent live DI.
7. References to DI-002's provisional classification mean that recorded milestone, not DI-002's final CLOSED status. No release-blocking prerequisite may be silently treated as NON_BLOCKING. Final scope freeze depends on resolved decisions, not vice versa.

---

## 3. Completed Pre-Code Context

The following context is already settled and does not need separate live tracking:

- **v0.1 frozen at H10.** H11–H14 were cancelled/superseded; the frozen research baseline remains available through Git history/tag `research_v_0.1_h10`.
- **Cost-controlled construction constraints established.** Durable budget/fallback/model-harness constraints now live in the PRD; the former temporary build-workflow document is archived as evidence only.
- **One canonical v0.2 lineage retained:** `feature/v0.2.0`.
- **v0.1 lessons captured** as historical audit input; they are not v0.2 product authority.
- **Clean active design authority created/reconciled:** PRD, Discovery, Architecture, Workflow Contracts and Qualification.
- **README authority map and Delivery Timeline reconciled** to the clean document structure and the Dec 31, 2026 / Jan 2027 delivery direction.
- The former active pre-code checklist has been retired; its still-relevant live work is represented by the DIs below.

These facts may be revisited only if new evidence materially contradicts them.

---

## 4. Current Discovery Items

### DI-001 — Accept the clean v0.2 design baseline

**Kind:** REVIEW

**Work:** Jointly review the clean PRD, Discovery, Architecture, Workflow Contracts and Qualification documents and confirm that they form one coherent SubhForge v0.2 baseline.

**Why it matters:** The clean documents were reconciled from multiple older design generations. Implementation should not proceed while contradictions or stale assumptions remain in the active authority set.

**Owner:** Subhadeep, with ChatGPT/Claude as review support where useful.

**Status:** ACTIVE

**Depends on:** None.

**Evidence / completion method:** Review the active set for product scope, lifecycle boundaries, agent authority, dependency/readiness semantics, reconciliation, model/harness portability, qualification and cost/complexity. Any real unresolved issue becomes a new or amended DI rather than being hidden in review comments.

**Outcome:** Open.

**Promote to:** The owning active document(s) for any accepted corrections; close this DI when Subhadeep accepts the set as a coherent baseline.

---

### DI-002 — Confirm and freeze the v0.2 release scope and Definition of Done

**Kind:** DECISION

**Work:** Establish the provisional in/out boundary needed to decide which remaining DIs are release-critical, then finalize/freeze that same scope and DoD after those in-scope decisions close.

**Why it matters:** A separate “scope cut” and later “scope freeze” would duplicate the same release-boundary work. One item should own the boundary from provisional cut through final freeze.

**Owner:** Subhadeep, supported by PRD/Architecture reasoning.

**Status:** BLOCKED until DI-001 closes. After that, DI-002 becomes ACTIVE: it first records a **provisional scope classification**, remains open while release-blocking DIs are resolved, and closes only when the final scope/DoD is frozen.

**Depends on:** DI-001 to begin. Final closure depends on the release-blocking DIs identified by DI-002's provisional scope classification.

**Evidence / completion method:**
- start from PRD goals, non-goals and candidate DoD;
- identify what must ship in stable v0.2.0 versus later versions;
- mark which DIs are release-blocking versus safely deferrable;
- preserve required dogfood/safety evidence;
- after required DIs resolve, reconcile the PRD DoD/non-goals and explicitly freeze the release boundary.

**Outcome:** Open.

**Promote to:** PRD; Timeline only if scope evidence requires a schedule change.

---

### DI-003 — Select the operational work-graph backend and minimal schema

**Kind:** RESEARCH / DECISION

**Work:** Select Jira or GitHub Issues as the single live operational work-graph backend and define the smallest schema/relationship representation required by accepted SubhForge semantics.

**Why it matters:** Backend choice and minimum schema are one coupled decision. Testing a backend without the required minimal graph/schema would not prove suitability, while designing schema before selecting the backend would be speculative.

**Owner:** Architect, with Subhadeep final decision.

**Status:** BLOCKED

**Depends on:** DI-001 and DI-002's provisional scope classification.

**Evidence / completion method:** Use the same representative work graph for both candidates. Evaluate hierarchy/sub-item fit, Contains/Governed-by/Depends-on representation, lifecycle state, blockers/escalations, reconciliation state/holds, FR/NFR traceability, suite ownership, evidence/implementation references, PR/commit linkage, human usability, API/MCP support, least-privilege writes, idempotent recovery, high-frequency status/next-work query cost, export/recovery and vendor lock-in. Define no fields beyond accepted workflow needs.

Review additions: include minimum discovery bootstrap before delivery initialization; complete/paginated reads, version/conflict detection, duplicate-create recovery after a lost response, and the cost/licensing of required fields/API access. Demonstrate restore from a recorded export with stable identity/relationships and matching Git references. A feature list or export button alone is insufficient evidence.

**Outcome:** Open.

**Promote to:** Architecture and Workflow Contracts where physical representation affects workflow contracts.

---

### DI-004 — Define durable STANDARD/LARGE mode discovery

**Kind:** DESIGN / DECISION

**Work:** Define the smallest durable mechanism that lets SubhForge determine a project's selected mode without repeatedly asking Subhadeep.

**Why it matters:** Mode must not silently change or depend on chat/session memory. The old `PROJECT-001.md` existence rule is not carried forward.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-001 and DI-002's provisional scope classification.

**Evidence / completion method:** Prefer a single durable, inspectable project-level marker/configuration that does not create a competing state store and remains understandable if Kilo/model tooling is unavailable.

Review addition: define the supported local execution environment (Subhadeep's Windows/PowerShell setup, Python/tool prerequisites and path/encoding assumptions), bootstrap checks, missing/contradictory-mode behavior and explicit handling of any unsupported mode conversion. Supporting every operating system is not required.

FR-022 closure work: define the short guided project-setup entry, supported prerequisite/version manifest, mode/stage-specific project templates, release/configuration pinning, managed-file ownership/conflict policy and idempotent interrupted-setup recovery. Separate read-only prerequisite/health checking from authorized setup/remediation. Supplied valid authority and existing customizations must survive setup; templates must not fabricate acceptance or a second live work hierarchy. Physical agent/harness setup follows DI-008 and admitted dependencies follow DI-010.

**Outcome:** Open.

**Promote to:** Architecture / project bootstrap contract.

---

### DI-005 — Define Git ↔ operational-backend identity, traceability and consistency

**Kind:** DESIGN

**Work:** Define one coherent cross-plane model for:
- Git authority ↔ operational work-item identity/reference;
- FR/NFR traceability;
- acceptance/evidence references;
- implementation/PR links;
- meaningful stale/missing-reference detection.

**Why it matters:** The former “Git/backend consistency” and “requirement/evidence linkage” questions are the same boundary viewed from two sides. Separate designs could create duplicated metadata or contradictory freshness rules.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-003.

**Evidence / completion method:** Persist identifiers/references rather than copied authority. Define only mechanically provable identity/reference/freshness checks required by readiness, status, reconciliation and evidence freshness. Avoid a synchronization subsystem or second truth store.

Review additions: resolve Architecture §4.4 and Workflow §23.2, including exact accepted revision/approval recognition, authority activation before REC holds exist, stale-context rejection at mutation/completion, composed integration baseline, claim identity/version, immutable run/environment identity, effective gates, waiver boundaries and revision-bound human acceptance. Demonstrate concurrent/manual edit and uncertain-write recovery without requiring a cross-system transaction or a second live store.

Follow-up: define how Workflow §14.2's acceptance packet references the demonstrated revision and records accept/reject/defer using existing work/evidence authority, without a second acceptance store.

**Outcome:** Open.

**Promote to:** Architecture; Workflow/Qualification only for semantics/proof that depend on the representation.

---

### DI-006 — Define reconciliation physical state and recovery representation

**Kind:** DESIGN

**Work:** Define how reconciliation packages, candidate/touched scope, holds, partial APPLY state, operation postconditions and overlap/conflict detection are represented across Git and the selected operational backend.

**Why it matters:** Reconciliation semantics are accepted, but safe pause, approval, retry/idempotency and unaffected-work preservation require a durable physical representation.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-003 and DI-005.

**Evidence / completion method:** Use the smallest representation that supports deterministic pre/postconditions, scope holds, resume, partial APPLY recovery, overlap/conflict detection and fail-closed behavior without duplicating authority.

Review additions: prove Workflow §§16.3–16.6 proposals: approval bound to exact verdict/baseline, stable postconditions across ordered operations, APPLY completion distinct from REC obligation closure, authorized obligation work despite its own hold, unaffected/cancelled pause recovery, and partial hold acquisition/release failure. Do not rely on a mutable APPLIED marker to solve replay.

**Outcome:** Open.

**Promote to:** Architecture + Workflow Contracts.

---

### DI-007 — Define Protected Architecture Invariant representation

**Kind:** DESIGN

**Work:** Define the simplest durable representation for Protected Architecture Invariants and their `DETERMINISTIC` / `SEMANTIC` / `MIXED` enforcement mapping.

**Why it matters:** Protected architecture is required, but SubhForge must not grow another heavyweight fitness-function framework without evidence.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-001 and DI-002's provisional scope classification (not its final closure).

**Evidence / completion method:** Prefer human-readable architecture authority plus the smallest machine-readable contract required by deterministic verification.

**Outcome:** Open.

**Promote to:** Architecture.

---

### DI-008 — Define physical agent/capability and interaction routing

**Kind:** DESIGN

**Work:** Define the smallest physical command/agent/capability mapping for the logical roles **and** the mechanism that distinguishes:
- owning-workflow interview/approval interactions; from
- Subhadeep-initiated explain/challenge conversations.

**Why it matters:** Physical role mapping and interaction-mode implementation are coupled. Both decide how logical authority contracts are exposed through the harness; designing them separately risks duplicated agents or a conversational state subsystem.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-001 and DI-002's provisional scope classification (not its final closure).

**Evidence / completion method:** Minimize physical agents/commands while preserving one owner per responsibility, authority boundaries and resumability. Prefer deriving interaction mode from invoked capability, durable target and owning authority instead of creating a new conversation-state engine.

Review additions: define the missing minimum Bug, Idea/Research and REC lifecycle contracts, including closure guards and owners; direct-authority Project admission without invented Ideation provenance; bounded Bug/Fix against accepted behavior in MAINTENANCE/COMPLETE projects without reopening completed children; and the authorization envelope for an on-demand delivery invocation. State which routine handoffs it may execute, where it stops, and what fresh invocation is needed after an exception. No background scheduler or routine Spec approval is implied.

Follow-up: map Architecture §6.4's guarded mutation boundary to actual harness/tools/credentials and explicitly record prevention versus detection/trusted-local limitations. Map Workflow §10.6's planning-quality checks and §14.2's Feature/Epic acceptance/rejection routing to existing owners; no new approval at routine Spec level.

FR-021 closure work: select the single model-map format/path, stable selection keys and centrally configured role defaults; implement explicit caller override → configured default → versioned provider identifier resolution under Architecture §7. Prove actual dispatch through the selected harness rather than a prompt claiming a model change. Include unknown/missing selection, unsupported capabilities/binding, mid-invocation map update, no silent paid fallback and agent-file independence when a compatible mapped version changes. The intended primary/independent reasoning and economical implementation preferences may be expressed as central defaults; no model-version table is retained in agent definitions or Architecture. Map resolution must preserve authority, credentials, budget and context guards.

For FR-022, prove setup makes the required logical agents/capabilities usable in the selected harness from a fresh project scope, using centrally configured models rather than manual per-agent edits.

**Outcome:** Open.

**Promote to:** Architecture / agent-command contracts.

---

### DI-009 — Define minimum lifecycle observability and recovery diagnostics

**Kind:** DESIGN

**Work:** Define the minimum durable diagnostics required for agent handoffs, backend mutations, blockers, reconciliation and recovery.

**Why it matters:** Subhadeep should normally be able to understand what happened, why work stopped, what authority/evidence was used and what safe next action exists without inspecting SubhForge internals.

**Owner:** Architect.

**Status:** BLOCKED

**Depends on:** DI-003, DI-005 and DI-006 for the operations that need to be observable.

**Evidence / completion method:** Retain only fields/events needed for diagnosis/recovery. Reuse harness/runtime telemetry where helpful but do not make provider/harness logs lifecycle authority.

**Outcome:** Open.

**Promote to:** Architecture + Qualification.

---

### DI-010 — Define the baseline external capability set

**Kind:** DECISION

**Work:** Decide the smallest v0.2 baseline of reusable Skills and MCP/integrations; classify everything else as project-specific or deferred.

**Why it matters:** Skills and integrations solve the same baseline-capability question: what external/reusable capability SubhForge itself should carry globally. Maintaining two independent baseline decisions would duplicate admission/security/cost reasoning.

**Owner:** Architect, with Subhadeep approval for consequential permissions/cost.

**Status:** BLOCKED

**Depends on:** DI-002's provisional scope classification. Work-management integration specifics also depend on DI-003.

**Evidence / completion method:** Apply real recurring need, credible provenance, non-duplication, authority compatibility, least privilege, context/tool cost, security/supply-chain risk, failure degradation and removability. Cloud/vendor integrations default to project-specific unless evidence proves global value.

Review additions: validate authority-expansion attempts through supplied notes/repository/tool output, denied writes, secret redaction in diagnostics/context/export, and declared subscription/backend/environment costs. Retry/authentication/permission failure must not silently choose a paid fallback.

Follow-up: evaluate the concrete skill-method and MCP candidates in Architecture §§19.4/20.3. Pin/adapt only those that earn admission; do not import another tracker, routine ticket-approval flow or automatic agent fan-out. Confirm removal and bounded tool/context overhead. Context7 and Playwright remain optional/project-specific rather than automatic global dependencies.

**Outcome:** Open.

**Promote to:** Architecture / installation manifest.

---

### DI-011 — Define the STANDARD compatibility boundary

**Kind:** DECISION / DESIGN

**Work:** Define the minimum STANDARD behavior/invariants that v0.2 must preserve and regression-test while LARGE is rebuilt.

**Why it matters:** The PRD protects STANDARD, but a clean v0.2 build should not accidentally drag forward every v0.1 internal contract.

**Owner:** Architect + Qualification design, with Subhadeep acceptance.

**Status:** BLOCKED

**Depends on:** DI-001 and DI-002's provisional scope classification.

**Evidence / completion method:** Preserve still-required user-visible capability/invariants, not obsolete implementation details.

**Outcome:** Open.

**Promote to:** Architecture + Qualification.

---

### DI-012 — Decide whether automatic PR creation belongs in v0.2

**Kind:** DECISION

**Work:** Decide whether v0.2 should automatically create a PR after reviewed Spec delivery or initially stop at PR-ready/manual creation.

**Why it matters:** It improves convenience but is not a core release requirement and must not distract from delivery/reconciliation reliability.

**Owner:** Subhadeep with Architect implementation recommendation.

**Status:** NON_BLOCKING

**Depends on:** DI-002's provisional scope classification; evaluate after core Spec delivery/GitHub integration shape is known.

**Evidence / completion method:** Include only if GitHub integration makes it small, safe and low-maintenance. Failure of PR automation must never invalidate valid implementation/review evidence.

**Outcome:** Open.

**Promote to:** Architecture / Workflow / implementation plan if accepted.

---

### DI-013 — Finalize the v0.2 qualification and dogfood strategy

**Kind:** DESIGN / DECISION

**Work:** Freeze one coherent verification/qualification strategy, including:
- deterministic unit/static/contract evidence;
- focused integration/FAST proof;
- behavioral compatibility canary;
- whether any dedicated dry-orchestration/contract validator is justified;
- release-level FULL qualification breadth;
- MediBot greenfield dogfood;
- Evaluation Guardrails reconciliation dogfood;
- scale/context dogfood.

**Why it matters:** The former dry-validator question, verification-strategy gate and dogfood-path gate are one proof-design problem. Splitting them risks adding validation machinery that does not serve the actual release evidence.

**Owner:** Qualification design, with Architecture input and Subhadeep acceptance.

**Status:** BLOCKED

**Depends on:** DI-014 plus the release-blocking architecture/workflow DIs that define the real boundaries and failure modes being qualified.

**Evidence / completion method:** For every expensive/model-bearing layer name the failure class it protects against and why cheaper deterministic evidence is insufficient. Dogfood remains mandatory release evidence; synthetic smoke does not replace it.

Review additions: freeze Qualification §24.10's requirement-to-proof coverage and measurable NFR thresholds before claiming RC/release success. Include real backend consistency/recovery, composed implementation evidence, exported-state restore, supported Windows bootstrap, security/permission/fallback failures and the amended reconciliation cases. Classify each applicable property as required, explicitly deferred or out of scope with authority; do not infer coverage from scenario names.

Follow-up: select the smallest mechanical/stateful/adapter/agent-evaluation proof mix under Qualification §24.11, define semantic grading examples and negative controls, freeze per-case/aggregate execution limits and trial reporting, and prove the positive baseline before expanding adversarial scenarios. FULL smoke breadth must not force repeated model execution of every workflow path.

Include FR-021's resolver/dispatch regressions under Qualification §24.12. Deterministic tests prove precedence, map snapshot identity and guard behavior; a small real-harness check proves the configured selection can actually be honored. Do not require paid calls across every configured model for each map edit.

Include FR-022's fresh-project, prerequisite-failure, read-only checking and setup-retry proof under Qualification §24.13. Cover the supported STANDARD/LARGE setup boundary defined by DI-004/DI-011; no multi-OS installer framework is required.

**Outcome:** Open.

**Promote to:** Qualification.

---

### DI-014 — Define the v0.2 walking skeleton

**Kind:** DESIGN

**Work:** Define the smallest real end-to-end LARGE implementation slice from idea/document intake through reviewed Spec delivery, including only the state/context/status/resume behavior required to prove the lifecycle is real.

**Why it matters:** The skeleton is the first implementation boundary. It must prove the architecture without front-loading the entire framework.

**Owner:** Architect + implementation planning, with Subhadeep acceptance.

**Status:** BLOCKED

**Depends on:** DI-002's provisional scope classification plus the architectural DIs required by the chosen thin slice, especially DI-003–DI-008.

**Evidence / completion method:** Specify entry/exit behavior, durable identities/state, minimum work-backend operations, handoffs, bounded context, status/resume, tests and acceptance evidence. Optional PR creation is excluded unless DI-012 is deliberately pulled into the skeleton.

Review addition: prove discovery/backend bootstrap and valid-authority direct admission, plus a composed implementation baseline that can support later Feature verification. The skeleton need not implement all higher-level acceptance, but its exit must state which lifecycle/evidence boundaries are actually proven.

Follow-up: identify the first demonstrable vertical slice and its minimal applicable cross-cutting foundations under Workflow §10.6. Establish an uninterrupted positive baseline before qualification expansion; defer infrastructure that has no accepted obligation or real consumer.

**Outcome:** Open.

**Promote to:** Architecture / Workflow / implementation plan as appropriate.

---

### DI-015 — Produce the dependency-aware implementation plan

**Kind:** DESIGN

**Work:** Convert the accepted scope, resolved architecture and walking skeleton into bounded, acceptance-driven implementation work units executable from fresh sessions and durable authority.

**Why it matters:** Implementation should not reopen settled architecture or depend on hidden chat context.

**Owner:** Planner/Architect with Subhadeep review.

**Status:** BLOCKED

**Depends on:** DI-002 through DI-014 for all release-blocking items relevant to implementation sequencing.

**Evidence / completion method:** Produce the smallest dependency-aware plan that implements foundations/walking skeleton first and then LARGE delivery, reconciliation and qualification support in accepted dependency order.

**Outcome:** Open.

**Promote to:** Implementation work system / planning authority selected by DI-003; repository only for genuinely architectural plan decisions.

---

### DI-016 — Final pre-code approval

**Kind:** GATE

**Work:** Decide whether SubhForge v0.2 implementation may begin.

**Why it matters:** This is the one consequential pre-code human gate. It should not be duplicated by a second “begin implementation” item.

**Owner:** Subhadeep.

**Status:** BLOCKED

**Depends on:** DI-001 through DI-015 for every item classified as release-blocking by DI-002. NON_BLOCKING items may remain open only when their deferral is explicitly safe.

**Evidence / completion method:** Confirm:
- accepted scope/DoD;
- no unresolved release-critical DI;
- architecture/workflow consistency;
- acceptable complexity and cost;
- qualification/dogfood strategy;
- executable implementation plan;
- no known unowned blocker.

**Outcome:** Open.

**Promote to:** Discovery closure record; implementation begins immediately after this DI closes.

---

## 5. Dependency Summary

The intended progression is:

```text
DI-001  Clean design review
   ↓
DI-002  Provisional scope boundary → eventual scope/DoD freeze
   ↓
Architectural decisions:
DI-003 backend+schema
DI-004 mode discovery
DI-005 cross-plane identity/traceability
DI-006 reconciliation representation
DI-007 protected invariants
DI-008 agents+interaction routing
DI-009 observability
DI-010 baseline skills/integrations
DI-011 STANDARD boundary
DI-012 optional PR (non-blocking)
   ↓
DI-014 walking skeleton
   ↓
DI-013 qualification + dogfood strategy
   ↓
DI-015 implementation plan
   ↓
DI-016 final pre-code approval
   ↓
Implementation
```

This is a dependency guide, not a requirement to execute every independent DI serially. Independent items may be worked in parallel when doing so does not violate their prerequisites or Subhadeep's preferred one-issue-at-a-time working style.

---

## 6. Explicitly Closed / Not Carried Forward

These are not live Discovery Items unless new evidence reopens them:

- Whether v0.2 should be implemented through stable v0.1.1 — **closed: no; clean build**.
- Whether `/specbypassceremony` is the v0.2 admission path — **closed: no**.
- Whether temporary `/arch-*` review commands/agents are required — **closed: no**.
- Whether LARGE operational Epic/Feature/Spec state should be a Markdown repository tree — **closed: no**.
- Whether SQLite should be a second workflow state store — **closed: no**.
- Whether Jira is selected by default — **closed: no; DI-003 requires evidence**.
- Whether an entire Epic must finish before another can progress — **closed: no; use truthful DAG eligibility**.
- Whether Planner may resolve missing upstream product/architecture intent by interviewing Subhadeep directly — **closed: no; route to owning authority**.
- Whether model/provider/harness identity defines SubhForge semantics — **closed: no**.
- Whether post-PR production-release orchestration is required in v0.2 — **closed: no**.
- Whether every production defect requires reconciliation — **closed: no; defects against existing authority use Bug/Fix, authority changes reconcile**.
- Whether a separate active pre-code checklist is required — **closed: no; Discovery Items own the live frontier and pre-code closure**.

---

## 7. Closure Rule

A Discovery Item is CLOSED only when:

1. its prerequisites were satisfied;
2. sufficient evidence exists;
3. Subhadeep decides when human authority is reserved;
4. the accepted result is promoted to its authoritative home;
5. affected DIs/requirements are reconciled;
6. the DI records its outcome/destination.

**Pre-code is closed when DI-016 is CLOSED.** There is no separate pre-code-gate tracker.

Git history preserves prior Discovery versions; this document should remain small enough to understand the current frontier without reconstructing old process history.

---

## 8. DI-001 Review Finding Ledger — 2026-10-06

Reviewed active design at commit `d4eaad40d7d242bb0dfeea2baeb4f8f42cf5bbf3`, PRD first, then Discovery, Architecture, Workflow and Qualification. No archived file contents were read. The attached earlier timeline is superseded by the active Git schedule.

This ledger is evidence for DI-001, not another work frontier. "Proposed" means corrected draft wording awaiting DI-001 human acceptance; "Expanded DI" means the physical/semantic decision remains open in its existing owner. No DI is closed by this review.

| Finding | Priority | Gap / consequence | Action / owning home | Disposition |
|---|---|---|---|---|
| RV-01 | High | REC blocks verification/readiness required to close its own obligations; paused baseline tests also cannot run | Workflow §§16.4–16.6 distinguish APPLY completion, bounded obligation work and final closure; Qualification cases 12/13 | Proposed; DI-006 must prove |
| RV-02 | High | Later operations can overwrite earlier postconditions, breaking backend-only replay and final checks | Workflow §16.3 requires normalized persistent effects and revision-bound approval; Qualification case 14 | Proposed; DI-006 must prove |
| RV-03 | High | Unaffected/cancelled REC releases hold but strands PAUSED Spec; cancellation can also expose changed authority | Workflow §16.4 requires current-authority checks and baseline refresh before ACTIVE; Qualification case 13 | Proposed; DI-006 must prove |
| RV-04 | High | Accepted authority can change before holds; remote writes/context checks are assumed atomic and complete | Architecture §4.4; DI-003/005/006: activation, conflict control, partial reads and lost-response recovery | Expanded DI; unresolved |
| RV-05 | High | Effective gates, waivers, claim freshness and revision-bound AC-0 acceptance have no executable contract | Workflow §23.2; DI-005 and Qualification §24.10 | Expanded DI; unresolved |
| RV-06 | High | Completed child branches do not establish an integrated Feature/Epic baseline | Workflow §23.2; DI-005/014; composed-baseline qualification | Expanded DI; unresolved |
| RV-07 | High | Ideation requires backend before project-init; direct admission has no Project entry contract | Workflow bootstrap note; DI-003/004/008/014 | Expanded DI; unresolved |
| RV-08 | High | Bug/research/REC lifecycle omitted; completed-project fixes and invocation authority unclear | Workflow §2.4 note; DI-008 | Expanded DI; unresolved |
| RV-09 | Medium | Cycle rule conditionally tolerates cycles although PRD requires a DAG | Workflow §11A blocks every execution-dependency cycle | Proposed correction |
| RV-10 | Medium | Feature/Epic diagrams send unspecified behavior straight to Planner; suite owners can appear recursively mandatory | Workflow §§10.5,13,14 route missing intent upstream and clarify owner designation | Proposed correction |
| RV-11 | Medium | DI-007/008 can depend on final scope freeze while freeze depends on them | Discovery dependencies use DI-002's provisional milestone; criticality separated from work status | Corrected draft |
| RV-12 | High | Qualitative scale/cost/recovery criteria lack frozen measurable release thresholds and coverage map | PRD NFR-010; DI-013; Qualification §24.10 candidate coverage/measurement contract | Expanded DI; unresolved |
| RV-13 | Medium | Export, Windows bootstrap and untrusted-input security are principles without specific proof; operating costs omitted | PRD CON-006/NFR-001/006; DI-003/004/010/013 and Qualification | Expanded DIs; proof pending |
| RV-14 | Low | README broken historical link, Architecture obsolete filenames and triage example citing an undefined requirement ID | README and Architecture reference active authority; Timeline maps current checkpoints to RC evidence | Corrected draft |

**Assessment:** coherent product direction, but not implementation-ready. Resolve the High findings through the cited DIs and accept the corrected semantics before DI-016. Avoid adding more agents, a second state store or broader automation to compensate for these gaps.

### Follow-up recommendation placement — 2026-10-06

Subhadeep requested that the additional suggestions be recorded in their owning documents. The additions remain REVIEW pending their owning DI/baseline acceptance; recording them does not close a DI or install a dependency.

| Recommendation | Owning document | Closure work |
|---|---|---|
| Cross-cutting coverage and decomposition-quality rubric; minimum foundations for the first slice | Workflow §10.6 | DI-008/DI-014; representation follows DI-005 |
| Reproducible Feature/Epic acceptance packet and accept/reject/defer routing | Workflow §14.2 | DI-005/DI-008 |
| Guarded mutation capability and honest enforcement limits | Architecture §6.4 | DI-008; proof DI-013 |
| Concrete, selectively adapted skill-method candidates | Architecture §19.4 | DI-010 |
| Bounded GitHub/work-backend baseline and optional documentation/browser integrations | Architecture §20.3 | DI-010; backend DI-003 |
| Mechanical/stateful/adapter tests, small agent evaluations and smoke cost controls | Qualification §24.11 and §24 | DI-013; positive skeleton DI-014 |

For the preceding planning/qualification follow-up, PRD and Timeline received no changes: those additions refined how existing requirements are delivered and proven, rather than introducing new product scope or dates.

### Model selection and architecture separation — 2026-10-06

The subsequent user request adds PRD FR-021: caller-selectable models whose concrete versions and role defaults have one central map. Architecture §7 owns the proposed resolver/dispatch/configuration design; DI-008 owns physical implementation decisions and DI-013 owns proof. No release/provider version is selected automatically.

Architecture is restructured around components, stores, interfaces and representative execution paths. Unique product/method/interaction/cost/scope rules move to PRD §§4.2/4.4/4.5, NFR-004 and §6; invariant-revision workflow remains in Workflow §17.1. Traceability, protected enforcement, guarded writes, skill/MCP seams and diagnostics retain their authoritative structural homes. Earlier recommendation placement remains historical evidence for that earlier request, not a claim that the PRD can never change.
