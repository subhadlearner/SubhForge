# SubhForge v0.2.0 — Product Requirements Document

**Status:** Draft for Subhadeep review  
**Date:** 2026-10-06  
**Target release:** `stable_v0.2.0` by December 31, 2026  
**Primary next consumer:** VidyaBeacon from January 2027

> This PRD defines the product SubhForge v0.2.0 must become. It intentionally excludes superseded v0.1.1, `/specbypassceremony`, temporary `/arch-*` review machinery, and the former November/December-1 delivery plan.

---

## 1. Product Statement

SubhForge is **Subhadeep's personal AI-assisted software-delivery orchestration system**.

Its purpose is to take serious personal projects from idea to trustworthy software while reducing:

- lost context and repeated explanation;
- requirement and architecture drift;
- unsafe or excessive AI authority;
- manual project coordination;
- avoidable token/model cost;
- fragile handoffs between planning, coding, verification and review.

The operating principle is:

> **SubhForge absorbs lifecycle ceremony. Subhadeep owns consequential product, architecture, acceptance, risk and exception decisions.**

SubhForge is successful when Subhadeep can build and evolve projects such as VidyaBeacon, MFBeacon, ArogyaBeacon and ArthaBeacon more reliably, economically and with less mental coordination than without it.

---

## 2. Goals

1. Provide one coherent workflow from idea through delivery, verification, change and recovery.
2. Preserve durable product/architecture truth outside chat or model memory.
3. Keep AI agents bounded to explicit responsibilities and authority.
4. Make large projects decomposable into independently deliverable, verifiable work.
5. Make requirement/architecture change safe through traceability and reconciliation.
6. Make interrupted work resumable from durable state.
7. Keep the normal human workflow low-ceremony.
8. Use deterministic mechanisms wherever correctness can be mechanically proven.
9. Keep model, harness and external-tool choices replaceable.
10. Prove the workflow through real dogfood before declaring v0.2 stable.

---

## 3. User and Operating Modes

### Primary user

Subhadeep is the sole intended v0.2 user and final decision authority.

### STANDARD

A lightweight workflow for small/medium projects where the full LARGE planning hierarchy would add unnecessary ceremony.

### LARGE

The full lifecycle for long-lived or architecture-sensitive projects:

```text
Idea / Discovery
→ PRD
→ Architecture
→ Project
→ Epic
→ Feature
→ Spec
→ Implement
→ Verify
→ Review
→ Feature acceptance
→ Epic acceptance
→ Evolution / Reconciliation
```

Subhadeep explicitly selects LARGE. SubhForge may recommend a mode but must never silently switch modes.

Once selected, mode must be durable and must not silently change. The physical mode-marker/discovery mechanism is an architecture decision, not a PRD concern.

### Lifecycle coverage

SubhForge v0.2 deliberately covers the software-delivery lifecycle in four segments:

| Lifecycle segment | SubhForge responsibility |
|---|---|
| **Requirement → Spec** | **Core.** Own the flow from idea/document intake through Discovery → PRD → Architecture → Project/Epic/Feature/Spec. |
| **Spec → PR** | **Core through reviewed implementation; PR creation is desirable but non-blocking.** SubhForge owns implementation, tests, verification and review before the change is considered ready. It should be able to prepare/raise a PR where practical, but automated PR creation is not a v0.2 release gate. |
| **PR → Production** | **Outside the primary v0.2 lifecycle.** Code, architecture, security and quality reviews required by SubhForge happen before PR readiness. Post-PR organizational approvals, deployment orchestration and production release are not required v0.2 capabilities. |
| **Production/feedback → Spec/Feature/Epic/Authority** | **Core change path.** A proven defect against existing accepted behavior follows Bug → Diagnose/Fix → Re-verify. Feedback that changes/misses accepted requirements, architecture, acceptance criteria, dependencies or planned work enters change triage and Reconciliation, which may propagate to the appropriate Spec/Feature/Epic and upstream authority. |

---

## 4. Sources of Truth

SubhForge separates durable product truth from operational delivery state.

### Git — product truth

Git owns canonical:

- discovery;
- PRD;
- architecture and ADRs;
- source code and tests;
- approved architecture changes;
- approved mutating reconciliation decisions that must survive retry/recovery.

Canonical documents evolve in place; Git history provides versioning.

### Operational work graph — delivery truth

LARGE projects use one durable operational work-graph backend for:

- Epics, Features, Specs and Bugs;
- lifecycle state;
- dependencies and governance links;
- requirement traces;
- blockers/escalations;
- implementation/PR links;
- reconciliation operational state;
- verification/evidence references where appropriate.

The backend is intentionally not selected by this PRD. Jira vs GitHub Issues remains an architecture/evidence decision.

There must not be a second live Markdown Epic/Feature/Spec hierarchy in the repository.

---

## 5. Functional Requirements

### FR-001 — Project mode

SubhForge shall support STANDARD and LARGE workflows without one silently changing into the other.

### FR-002 — Discovery and ideation

For LARGE projects, `/ideate` shall accept either:

- a conversational idea described by Subhadeep; or
- existing notes/documents supplied by Subhadeep.

The Ideation Agent shall actively interview Subhadeep to obtain the information required to establish durable discovery. It shall extract already-known decisions from supplied material instead of forcing them to be restated.

The canonical Git discovery document shall contain at least:

- problem/outcome;
- users/actors;
- success measures;
- scope and non-goals;
- core journeys;
- binding constraints;
- confirmed decisions;
- unresolved decision/research frontier;
- assumptions and required evidence.

When a material question cannot be answered during ideation, SubhForge shall create a durable research/decision work item rather than keeping the question only in chat.

The Research Agent is optional. Subhadeep may perform the research himself and update the durable work item with evidence. The Research Agent may later be invoked to evaluate/synthesize that evidence, close the research item when justified, and update the discovery document with the research result. Research evidence does not silently become product authority; product conclusions are confirmed through the owning Ideation/PRD workflow.

Ideation shall be resumable from the current discovery document plus durable open work items, not from chat history.

### FR-003 — Existing-authority admission

SubhForge shall not force replay of upstream stages merely for ceremony.

A valid existing PRD or architecture may be admitted directly when the receiving workflow can prove it is sufficiently complete, internally consistent and safe to consume.

Missing product/architecture authority shall route to the owning workflow rather than being invented downstream.

Arbitrary onboarding of unrelated brownfield codebases is not a v0.2 requirement.

### FR-004 — Canonical PRD

`/prd` shall create/refine one canonical PRD from accepted discovery/research.

Requirements shall use stable permanent IDs:

- `FR-###` for functional requirements;
- `NFR-###` for non-functional requirements.

IDs shall never be renumbered or reused; obsolete requirements are RETIRED.

### FR-005 — Architecture and protected invariants

`/architect` shall create/refine architecture from accepted requirements and shall define, where needed:

- technology and structural decisions;
- NFR reach (`SCOPED` or `CROSS_CUTTING`);
- Protected Architecture Invariants;
- deterministic/semantic/mixed enforcement expectations.

Normal planning, implementation, fixing and reconciliation shall not silently modify Protected Architecture Invariants.

### FR-006 — Hierarchical decomposition

For LARGE projects, accepted PRD + architecture shall be decomposed into:

`Project → Epic → Feature → Spec`

with:

- human-verifiable Epic outcomes;
- human-verifiable Feature capabilities;
- implementation-ready behavioral Specs;
- real dependency/governance relationships;
- requirement traceability.

Decomposition shall prefer vertical product slices over technical-layer work.

### FR-007 — Readiness and grooming

Epic, Feature and Spec readiness shall be explicit.

A work item is ready only when the next stage can proceed without inventing material product or architecture intent.

Missing product intent routes to the PRD owner. Missing architecture intent routes to the Architect. Ambiguous ownership or consequential unresolved choice returns `HUMAN_DECISION_REQUIRED`.

### FR-008 — Dependency-aware work graph

Dependencies shall form a truthful DAG.

SubhForge shall:

- model real prerequisites only;
- allow safe work across Epic/Feature boundaries;
- detect/block cycles;
- derive eligible work deterministically;
- preserve independent work when another branch is blocked or reconciling.

The three semantic relationship classes are:

- Contains;
- Governed by;
- Depends on.

### FR-009 — Work plan and status

SubhForge shall provide deterministic, read-only projections of:

- current executable work;
- next eligible work;
- blockers;
- prerequisite chains;
- reconciliation holds;
- paused work;
- remaining/completed/active counts.

Status/work-plan capabilities shall never mutate project state and shall avoid fake precision.

### FR-010 — Spec delivery

The normal Spec loop is:

```text
READY Spec
→ Implement
→ focused tests
→ Verify
→ Review
→ Complete
```

Known failures route to Fix; unknown failures route through Diagnose then Fix; authority contradictions route to reconciliation.

Routine Spec completion shall not require Subhadeep approval.

After review approval, SubhForge should be able to prepare and, where configured, raise a PR containing the bounded change plus useful Spec/requirement/evidence references. Automated PR creation is desirable but is not mandatory for the v0.2 release.

### FR-011 — Verification and review separation

Implementation, verification and review are distinct responsibilities.

- Builder authors implementation and required tests.
- Verifier executes required checks and records factual evidence.
- Reviewer judges engineering quality against accepted authority/evidence.

Verification shall not invent expected behavior. Review shall not invent product intent.

### FR-012 — Feature and Epic acceptance

Feature and Epic are the default human acceptance boundaries.

A Feature completes only after integrated verification is clear and Subhadeep accepts its human-evaluable capability (`AC-0`).

An Epic completes only after journey-level verification is clear and Subhadeep accepts its human-evaluable outcome (`AC-0`).

### FR-013 — Planned integration/E2E ownership

Higher-level verification suites shall be planned delivery work, not hidden Verifier side effects.

Every Feature shall have an owning Spec for its integration-suite work.

Every Epic shall have an owning Feature for its E2E-suite work.

The Builder authors the suite; the Verifier runs and evidences it.

### FR-014 — Production feedback and defect workflow

Production/runtime/user feedback shall first be classified against current accepted authority.

- A proven implementation defect against already-accepted behavior enters a bounded Bug → Diagnose/Fix → Re-verify workflow and does not require full reconciliation merely because it occurred in production.
- Feedback that reveals a missing/changed requirement, acceptance criterion, architecture obligation, dependency or planned behavior enters Change Triage and, when material, Reconciliation.

Higher-level escaped defects shall be classified by the layer where they should reasonably have been caught so repeated escapes improve future planning/testing.

### FR-015 — Change triage

SubhForge shall distinguish:

- `DEFECT`;
- `LOCAL_REFINEMENT`;
- `AUTHORITY_CHANGE`;
- `PROTECTED_ARCHITECTURE_CONFLICT`.

A change shall not use a fast path unless its FR/NFR/invariant impact is explicitly understood.

A LOCAL_REFINEMENT fast path requires explicit Subhadeep approval.

### FR-016 — Reconciliation

Accepted authority changes shall use an explicit reconciliation flow:

```text
ANALYZE
→ human approval where mutation/semantic authority requires it
→ APPLY
→ re-verify affected evidence/work
```

Reconciliation shall:

- bound impact using requirement traces, governance and dependencies;
- stop propagation at unaffected branches;
- preserve unaffected work;
- invalidate only genuinely affected evidence where safely provable;
- pause an affected ACTIVE Spec rather than finish stale work;
- support RESUME / ADAPT / SUPERSEDE outcomes;
- be retryable/idempotent across partial APPLY failures;
- fail closed on missing traceability or protected-invariant conflict.

### FR-017 — Durable resume

Work shall resume by re-invoking the owning workflow against the same durable ID, not by relying on chat/session memory.

Examples:

- `/ideate` resumes discovery;
- `/epic EPIC-###`, `/feature FEATURE-###`, `/spec SPEC-###` resume planning;
- `/implement SPEC-###` resumes implementation;
- `/reconcile REC-###` resumes reconciliation.

Safe progress shall persist before stopping because of time, cost or context pressure.

### FR-018 — Bounded context

A work operation shall load minimum-sufficient current context:

- target work item;
- required ancestors;
- declared dependencies/contracts;
- applicable PRD/architecture authority;
- relevant implementation surface;
- reconciliation obligations;
- required evidence.

Broad project history shall not be loaded by default.

### FR-019 — Skills and external tools

Skills and MCP/tool integrations shall provide reusable expertise/current external capability without becoming hidden authority.

They shall be admitted deliberately for real value, provenance, security, permission scope, context cost and removability.

External output is untrusted input until validated/promoted into accepted project authority.

### FR-020 — Framework qualification

SubhForge shall provide layered framework qualification using:

1. deterministic unit/static/contract checks;
2. focused integration/FAST checks where boundaries justify them;
3. limited model-bearing behavioral canaries;
4. release-level FULL qualification;
5. real-project dogfood.

Synthetic smoke shall complement, not replace, real dogfood.

---

## 6. Logical Agent Responsibilities

Physical filenames and model choices may change; these responsibility boundaries may not.

| Agent / capability | Owns | Must not do |
|---|---|---|
| Ideation Agent | Conversational/document intake, discovery, interviews, unknowns and research frontier | Decide PRD/architecture |
| Research Agent | **Optional** bounded research closure, evidence synthesis and discovery research updates | Silently make product decisions |
| PRD Agent | Canonical requirements | Mutate architecture |
| Architect Agent | Architecture, NFR reach, protected invariants | Silently change product intent |
| Planner / Decomposition Agent | Epic/Feature/Spec decomposition, readiness, dependencies | Invent missing PRD/architecture intent |
| Work-Plan Capability | Eligible-work projection | Create dependencies or mutate state |
| Status Capability | Progress/blocker explanation | Mutate state |
| Builder / Implementer | One accepted Spec and its tests | Change product/architecture authority |
| Verifier | Execute checks and record evidence | Invent behavior or author missing expectations |
| Reviewer | Engineering-quality judgement | Invent product intent |
| Diagnoser | Root-cause analysis | Choose unresolved product/architecture semantics |
| Fixer | Bounded corrective mutation | Expand accepted behavior |
| Adversary | Independent challenge | Become authority |
| Reconciliation Planner | Impact analysis and proposed verdict | Perform semantic work mutation before approval |
| Reconciliation Executor | Apply approved reconciliation operations | Reinterpret approved intent |
| Smoke Orchestrator / Executor | Framework qualification | Become product-delivery authority |

Subhadeep can question any responsible reasoning agent's rationale.

Only Ideation, PRD and Architect agents may normally initiate broad product/architecture questioning. Other agents may initiate only bounded blocking clarification within their authority.

### Interaction contract

Agent interaction depends on **initiator + target + intent + owning authority**.

**Owning workflow → Subhadeep:** when Ideation, PRD or Architect is authoring/refining its authority, it may interview Subhadeep to obtain missing authoritative information or request a consequential decision/approval that the agent cannot make.

**Subhadeep → Agent:** when Subhadeep starts a conversation with Architect, Planner, Reviewer or another reasoning agent about an existing artifact/work item, the default mode is bounded **explain/challenge**, not mutation. The agent reconstructs the relevant durable context and explains its rationale.

If that conversation becomes a request to change accepted authority, the receiving agent must route the request to the workflow that owns that authority. For example, a Planner or Reviewer discussing an architecture choice cannot silently change architecture; an architecture change returns to the Architect/change-governance path.

Implementation may represent this interaction contract however is simplest, but conversation context alone never expands an agent's mutation authority.

---

## 7. Handover Contract

Every handover must be reconstructable from durable state and must state what authority/evidence the receiving capability may rely on.

| From | To | Required handover |
|---|---|---|
| Ideation | PRD | Discovery is materially complete; unresolved items are explicitly owned/non-blocking |
| PRD | Architect | Accepted canonical PRD with stable FR/NFR identities and no material contradiction |
| Architect | Planner | Accepted architecture, NFR classification, protected invariants and enforcement expectations |
| Planner | Builder | READY_FOR_IMPLEMENTATION Spec, valid traces, consumable contracts, no blocking dependency/REC |
| Builder | Verifier | Implementation + authored tests for accepted behavior; no hidden authority change |
| Verifier | Reviewer | Current immutable evidence tied to the implementation identity being reviewed |
| Reviewer | Spec completion | Review approved; required evidence current; no reserved human decision outstanding |
| Specs | Feature verification | Required child Specs complete + integration-suite owner/evidence ready |
| Features | Epic verification | Required Features complete + E2E-suite owner/evidence ready |
| Feature/Epic verification | Subhadeep | Automated gate clear; bounded human-evaluable `AC-0` acceptance |
| Change triage | Reconciliation | Cited affected FR/NFR/invariant context and conservative authority-change classification |
| Reconciliation Planner | Executor | Explicit approved verdict with bounded operations/preconditions/postconditions |

A handover must fail closed when mandatory authority, identity, evidence or ownership is missing.

---

## 8. Guardrails

1. **Human authority:** Subhadeep owns consequential product, architecture, acceptance, waiver/risk and exception decisions.
2. **No silent invention:** downstream agents never invent missing upstream intent.
3. **Deterministic mechanical boundaries:** identity, state transitions, dependency integrity, eligibility, schema, evidence freshness and mutation preconditions are mechanically checked where practical.
4. **Fail closed:** ambiguous identity, missing traceability, malformed state, stale evidence or unauthorized mutation blocks visibly.
5. **One owner per responsibility:** planning, implementation, verification, review and reconciliation roles do not absorb each other.
6. **Protected architecture:** normal workflows cannot change a Protected Architecture Invariant.
7. **No autonomous scheduling:** dependencies make work eligible; they never authorize SubhForge to start it without a user command.
8. **No silent model/provider fallback:** changing model does not change authority or mutation rights.
9. **Least privilege:** external tools/MCP are read-only by default and writes are bounded/authorized.
10. **Fresh authority:** agents retrieve current durable authority when correctness depends on freshness.
11. **Evidence freshness:** evidence is trusted only for the authority/implementation identity it actually proves.
12. **Bounded retries/cost:** repeated equivalent AI failure stops/escalates rather than consuming money indefinitely.
13. **Project independence:** a project remains understandable/recoverable when SubhForge, Kilo or a model provider is unavailable.
14. **Low human ceremony:** routine coordination safely derivable from authority is SubhForge's job, not Subhadeep's.

---

## 9. Non-Functional Requirements

### NFR-001 — Correctness and resilience

Correctness/recoverability outrank convenience and schedule. Failures should be detected, contained, diagnosable and recoverable.

### NFR-002 — Resumability

Interrupted work must reconstruct from Git + operational state without requiring prior chat history.

### NFR-003 — Context efficiency

- target Spec artifact: roughly 5–15k tokens;
- normal working context: roughly 20–40k tokens;
- 40k is a pressure threshold;
- 100k is a hard ceiling.

Required authority must never be dropped merely to fit context.

### NFR-004 — Cost efficiency

SubhForge shall expose and control expensive model calls, retries, smoke breadth and context growth. Stronger models are used only where expected value justifies cost.

### NFR-005 — Model and harness adaptability

No execution harness, model family or provider is a permanent product dependency.

Kilo/models/tools may execute SubhForge but shall not define lifecycle semantics, authority or project history. SubhForge's agent contracts, durable state, authority boundaries and handovers must remain stable enough that the primary harness or assigned model/provider can be replaced without redesigning project history or changing what a workflow means.

Portability is required at these seams; v0.2 is not required to build a generic plug-in framework for every possible harness/provider.

### NFR-006 — Security

External integrations use least privilege, bounded tool exposure, secret isolation, untrusted-output handling and explicit authorization for consequential writes.

### NFR-007 — Observability and diagnostics

Failures, blockers, held scopes, next actions and recovery instructions must be visible enough that Subhadeep normally does not need to inspect SubhForge internals.

### NFR-008 — Qualification feedback time

For tiny default framework fixtures:

- FAST target ≤ 10 minutes; investigate >15 minutes;
- FULL target ≤ 25 minutes;
- FULL >30 minutes is a performance-budget failure unless explained by provider outage or explicit human wait.

### NFR-009 — Compatibility protection

v0.2 LARGE evolution shall not silently regress STANDARD behavior.

### NFR-010 — Human intervention

During real dogfood, avoidable manual status reconstruction, handoff coordination, repeated settled questions and routine Spec approvals are product-quality failures. For VidyaBeacon, such intervention should approach zero.

---

## 10. Current Execution Baseline

The current development environment may use VS Code, Kilo, GitHub, ChatGPT, Claude and DeepSeek.

These are **workers/tools, not product authority**. Agent responsibilities are stable product contracts; model assignments are configurable execution policy.

Current default routing:

| Work class | Current default |
|---|---|
| Product discovery, PRD, architecture, decomposition, senior synthesis/review | Strong primary reasoning model — currently GPT-5.6 Sol |
| Lightweight orchestration/status/bookkeeping where semantic reasoning is small | Lightweight/cheaper model or deterministic code — currently GPT-5.6 Luna where a model is useful |
| Routine implementation, tests and bounded fixes | DeepSeek by default |
| Material independent co-architecture/challenge | Claude Sonnet through the bounded Claude Code + Pro path |
| Exceptional high-risk architecture/challenge or hard diagnosis | Claude Opus by explicit escalation |
| Mechanical state, graph, validation, eligibility and mutation preconditions | Deterministic code first |

This routing is a **current configuration baseline, not product authority**. It may change because of model quality, availability, price or tooling evolution without changing agent responsibility or workflow semantics.

Model/tool routing rules:

- model choice never changes lifecycle semantics or mutation authority;
- no provider is required to preserve project truth;
- there is no silent paid/provider fallback;
- stronger models are used only when expected value justifies cost;
- external construction skills/tooling may be removed without changing SubhForge product semantics.

---

## 11. Non-Goals for v0.2

v0.2 will not attempt to become:

- a generic workflow platform for other engineers;
- a multi-user enterprise governance system;
- an autonomous scheduler/background project manager;
- a post-PR CI/CD, organizational approval or production-release orchestration platform;
- an arbitrary brownfield-codebase onboarding/migration product;
- a universal provider-routing framework;
- a generic multi-backend work-management plugin framework;
- a second live repository-based Epic/Feature/Spec store;
- an automated architecture-rebaseline engine;
- a system that treats chat/session history as authority;
- a system that front-loads speculative reusable infrastructure;
- a framework whose assurance depends primarily on exhaustive expensive model smoke.

---

## 12. Release and Dogfood Requirements

A stable v0.2.0 release requires evidence from:

### Greenfield LARGE dogfood — MediBot

Prove the meaningful end-to-end lifecycle from discovery through Epic acceptance, including dependency-aware planning, status, implementation, verification and recovery.

### Evolution/Reconciliation dogfood — MediBot Evaluation Guardrails

Prove safe authority change, including:

- bounded impact discovery;
- cross-Feature dependency propagation;
- protected-invariant conflict;
- missing-trace fail-closed behavior;
- in-flight Spec pause/adapt/resume/supersede;
- partial APPLY recovery/idempotency;
- evidence invalidation and re-verification.

### Scale/context qualification — Autonomous Market Intelligence

Prove:

- multiple Epics/Features/Specs;
- cross-hierarchy DAG execution;
- multi-session resume;
- bounded context;
- status/work-plan quality;
- acceptable token/runtime behavior.

Stable release additionally requires:

- STANDARD + LARGE regression;
- install/bootstrap/doctor/release checks;
- behavioral drift canary;
- required adversarial cases;
- acceptable runtime/cost;
- sufficient diagnostics/recovery;
- Subhadeep's final acceptance of the release bar.

Schedule shall not weaken required dogfood or safety evidence.

---

## 13. Success Criteria

SubhForge v0.2 is successful when:

1. Subhadeep can begin VidyaBeacon using a tested `stable_v0.2.0` release rather than continuing to design SubhForge.
2. A LARGE project can progress from idea to accepted Epic outcome without relying on hidden chat context.
3. Routine Spec delivery requires no recurring Subhadeep ceremony.
4. Material requirement/architecture change can be reconciled without corrupting unaffected work.
5. Interrupted sessions can resume truthfully from durable state.
6. The system explains why work is blocked/eligible without requiring internal debugging.
7. Model/harness changes cannot silently change authority or lifecycle semantics.
8. Dogfood shows that Subhadeep spends his attention on product/architecture decisions, not SubhForge bookkeeping.

---

## 14. Discovery and Open-Decision Registry

Unanswered design/research questions are intentionally **not embedded as competing requirements in this PRD**.

The current decision frontier is maintained in:

`design/discovery/SUBHFORGE-V0.2-DISCOVERY.md`

Each live question has a stable `DQ-###` identity, owner, blocking status and closure evidence. When a question is resolved:

- a product requirement is promoted into this PRD only when it changes what SubhForge must do;
- an implementation/structural answer is promoted into Architecture;
- workflow semantics are promoted into the appropriate workflow authority;
- obsolete questions are closed/superseded rather than silently deleted.

The Discovery document is working decision context, not a second source of product truth.

---

## 15. v0.2 Definition of Done

`stable_v0.2.0` may be declared only when:

- the accepted PRD/architecture/workflow is implemented without known authority contradiction;
- the walking skeleton works end to end;
- required deterministic gates and recovery paths work;
- LARGE greenfield delivery has been dogfooded;
- reconciliation has been dogfooded against real implemented lifecycle/evidence contracts;
- scale/context behavior has been qualified;
- STANDARD remains protected;
- release/runtime/cost/diagnostic evidence is acceptable;
- temporary construction scaffolding is not required for product operation;
- Subhadeep accepts that SubhForge is trustworthy enough to become delivery infrastructure for VidyaBeacon.
