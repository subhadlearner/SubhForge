# SubhForge v0.2.0 — Product Requirements Document

**Status:** Draft for Subhadeep review  
**Date:** 2026-10-06  
**Target release:** `stable_v0.2.0` by December 31, 2026  
**Primary next consumer:** VidyaBeacon from January 2027

> This document defines **what SubhForge v0.2.0 must be and the constraints within which it must be built**. Structural implementation choices belong in Architecture, workflow mechanics belong in Workflow Contracts, release proof belongs in Qualification, and unresolved pre-code work belongs in Discovery.

The 2026-10-06 review clarifications are proposed additions pending DI-001 acceptance; no scope freeze or Discovery closure is implied.

Additions tagged `RV-19` to `RV-38` come from the independent review recorded in Discovery §8 and carry the same proposed status.

---

## 1. Core Product Requirement

SubhForge shall be **Subhadeep's personal AI-assisted software-delivery orchestration system** for taking serious personal software projects from an initial idea or existing requirement material to trustworthy, reviewable and evolvable software.

The core requirement is:

> **SubhForge shall absorb the repeatable software-delivery coordination work while preserving Subhadeep's authority over consequential product, architecture, acceptance, risk and exception decisions.**

SubhForge must materially reduce:

- repeated explanation and lost context;
- requirement and architecture drift;
- unsafe or excessive AI authority;
- manual sequencing and handoff coordination;
- avoidable model/token/provider cost;
- fragile resume/recovery after interrupted work;
- uncertainty about what work is ready, blocked, verified or affected by change.

SubhForge is successful only if Subhadeep can build and evolve projects such as VidyaBeacon, MFBeacon, ArogyaBeacon and ArthaBeacon **more reliably, economically and with less mental coordination than without it**.

### 1.1 Intended user

Subhadeep is the sole intended v0.2 user and final human decision authority.

SubhForge v0.2 is not a multi-user/team workflow product and is not designed as a generic engineering platform for other developers.

### 1.2 Lifecycle boundary

SubhForge v0.2 deliberately covers the lifecycle in four segments:

| Lifecycle segment | Requirement |
|---|---|
| **Requirement → Spec** | **Core.** SubhForge owns the path from conversational/document intake through Discovery → PRD → Architecture → Project → Epic → Feature → Spec. |
| **Spec → reviewed implementation** | **Core.** SubhForge owns implementation, tests, verification and review. PR preparation/creation may be supported where useful, but automated PR creation is not a v0.2 release gate. |
| **PR → Production** | **Outside primary v0.2 scope.** Post-PR organizational approvals, deployment orchestration and production release are not required v0.2 capabilities. |
| **Production/runtime/user feedback → accepted authority/work** | **Core evolution path.** A proven defect against existing accepted behavior uses Bug → Diagnose/Fix → Re-verify. Feedback that changes or exposes missing requirements, architecture, acceptance, dependencies or planned behavior enters Change Triage/Reconciliation. |

Proposed boundary clarifications (RV-21): integrating a reviewed Spec change into the managed project's integration baseline belongs to *Spec → reviewed implementation* wherever a dependent Spec or Feature/Epic verification relies on it. It is not post-PR release orchestration. Who performs that step is DI-005/DI-014 work. Local or test environments needed to run integration/E2E checks and `AC-0` demonstrations are ordinary project delivery work; only production deployment and release stay outside scope.

---

## 2. Product and Delivery Constraints

The following constraints are part of the v0.2 requirement boundary. They apply regardless of the specific model, provider, harness or implementation selected later.

### CON-001 — Personal workflow first

Every v0.2 capability must materially help Subhadeep design, build, verify, reconcile, resume or understand his own projects.

Generic platform capability without demonstrated personal value is out of scope.

### CON-002 — Human authority

Subhadeep retains authority over:

- material product intent and trade-offs;
- architecture decisions and Protected Architecture Invariant changes;
- Feature/Epic human acceptance;
- risk/waiver decisions;
- ambiguous ownership/conflicts;
- exceptional scope/cost decisions.

AI/tool output is advisory until accepted through the owning workflow.

### CON-003 — Durable truth outside chat/model memory

Canonical product and architecture truth must remain durable and inspectable outside a model session.

Chat history, provider session state, hidden reasoning, model memory, subscription state and harness runtime state must not become product authority.

### CON-004 — Deterministic-first mechanics

When correctness can be mechanically proven, SubhForge shall prefer deterministic code over model judgement.

This includes identity, state transitions, dependency integrity, eligibility, schema checks, evidence freshness, context limits and mutation preconditions where practical.

### CON-005 — Replaceable model/provider/harness

ChatGPT, Claude, DeepSeek, Kilo and any future model/provider/harness are execution choices, not semantic authority.

Changing them must not redefine:

- lifecycle meaning;
- agent responsibility;
- mutation authority;
- durable work identity/history;
- acceptance criteria;
- handover semantics.

v0.2 requires migration-friendly seams, not a universal provider/plugin framework.

### CON-006 — Cost-controlled construction

SubhForge v0.2 shall be built within Subhadeep's deliberately bounded AI/tooling budget.

The current construction ceiling is approximately **$50/month before tax**, presently composed of existing ChatGPT and Claude subscriptions plus at most **$10/month of new variable model spend**.

Rules:

- any increase to the construction budget requires explicit Subhadeep approval;
- no new subscription, purchased Kilo credits, Anthropic API spend or other paid fallback is assumed by the v0.2 plan;
- existing prepaid balances may be consumed deliberately;
- model strength/escalation must be justified by expected value;
- repeated equivalent model failure must stop/escalate rather than burn budget indefinitely.

The exact provider/model split is execution configuration, not a permanent product requirement.

Construction spend and the cost of operating SubhForge-managed projects are distinct measurements. Backend licensing, storage, hosted test environments and optional integrations must be surfaced before adoption; the construction ceiling does not implicitly authorize them. Discovery DI-003/DI-010/DI-013 must establish an affordable operating baseline with Subhadeep.

Model/tool spend for the §7 dogfood evidence must be classified before it is incurred (RV-33, proposed): DI-013 states whether it counts against this construction ceiling or the operating baseline, with an estimate for the December dogfood sequence. An unclassified dogfood run is not assumed affordable.

### CON-007 — No silent paid/provider fallback

Quota exhaustion, authentication failure, balance exhaustion, rate limits, denied permission or configured provider failure shall surface explicitly.

SubhForge/build tooling must not silently route to a different paid provider or billing path.

### CON-008 — Low human ceremony

Routine coordination that is safely derivable from accepted authority is SubhForge's responsibility.

Subhadeep should primarily spend attention on:

- answering meaningful product/architecture questions;
- challenging rationale;
- approving consequential decisions;
- Feature/Epic acceptance;
- risk/exception decisions.

Routine Spec progression, status reconstruction and agent handoff coordination should not require recurring manual intervention.

### CON-009 — Fail closed on uncertainty that affects correctness

Missing authority, ambiguous identity, invalid state, stale evidence, missing traceability, unsafe dependency state or unauthorized mutation must block visibly rather than be guessed through.

### CON-010 — Project independence

A managed project must remain understandable and recoverable when SubhForge, Kilo or a specific model/provider is unavailable.

Git history, accepted authority, operational state/export and documented semantics must be sufficient to reconstruct what the project means and where work stands.

### CON-011 — Schedule does not weaken required evidence

The target is `stable_v0.2.0` by **December 31, 2026**, enabling VidyaBeacon to start in **January 2027**.

Schedule pressure must not silently remove required correctness, recovery, dogfood or release evidence. Scope must be deliberately reduced/replanned instead.

### CON-012 — Simplicity and removability

SubhForge shall use the smallest robust mechanism that satisfies the requirement.

Temporary construction scaffolding, external skills, provider-specific tooling and review helpers must remain removable without changing product semantics.

---

## 3. Detailed Functional Requirements

The functional requirements below decompose the core requirement into the capabilities SubhForge v0.2 must provide.

### 3.1 Project mode, discovery and authority formation

#### FR-001 — Project mode

SubhForge shall support **STANDARD** and **LARGE** workflows.

- STANDARD is the lightweight path where the full LARGE hierarchy would add unnecessary ceremony.
- LARGE is the full long-lived/architecture-sensitive path.

Subhadeep explicitly selects LARGE. SubhForge may recommend a mode but must not silently switch modes.

Once selected, the mode must be durable and must not depend on chat/session memory.

Converting an existing project between modes is not a v0.2 capability (RV-34, proposed). An attempted or implied conversion is refused visibly unless DI-004 accepts an explicit bounded conversion path.

#### FR-002 — Discovery and ideation

For LARGE projects, Ideation shall accept either:

- a conversational idea described by Subhadeep; or
- existing notes/documents supplied by Subhadeep.

Ideation shall:

- extract already-known decisions/context rather than force restatement;
- actively interview Subhadeep only for missing discovery information or reserved decisions;
- maintain canonical durable discovery;
- capture problem/outcome, actors, success measures, scope/non-goals, journeys, constraints, confirmed decisions, assumptions/evidence and the unresolved frontier;
- create durable research/decision work when a material question cannot be answered immediately;
- resume from durable discovery + open work, not prior chat.

The Research Agent is optional. Subhadeep may perform research himself. When invoked, Research may evaluate/synthesize evidence and support closure of the durable research item, but accepted product conclusions are promoted only through the owning Ideation/PRD workflow.

#### FR-003 — Existing-authority admission

SubhForge shall not force replay of upstream authoring stages merely for ceremony or provenance.

A valid existing PRD or architecture may be admitted directly when the receiving workflow can prove it is sufficiently complete, internally consistent and safe to consume.

Missing product authority shall route to the PRD-owning workflow. Missing architecture authority shall route to Architect. Downstream agents shall not invent either.

Arbitrary onboarding/migration of unrelated brownfield codebases is not a v0.2 requirement.

#### FR-004 — Canonical PRD and stable requirement identity

The PRD workflow shall maintain one canonical PRD.

Requirements shall use durable IDs:

- `FR-###` for functional requirements;
- `NFR-###` for non-functional requirements.

IDs shall not be reused or cosmetically renumbered. Obsolete requirements are retired through accepted change governance.

#### FR-005 — Architecture and protected invariants

The Architecture workflow shall derive structural decisions from accepted requirements and define where necessary:

- technology/system boundaries;
- NFR reach (`SCOPED` or `CROSS_CUTTING`);
- Protected Architecture Invariants;
- deterministic/semantic/mixed enforcement expectations.

Normal planning, implementation, fixing and reconciliation shall not silently modify Protected Architecture Invariants.

---

### 3.2 Planning, work graph and readiness

#### FR-006 — Hierarchical decomposition

For LARGE projects, accepted PRD + Architecture shall decompose into:

`Project → Epic → Feature → Spec`

with:

- human-verifiable Epic outcomes;
- human-verifiable Feature capabilities;
- implementation-ready behavioral Specs;
- truthful requirement traceability;
- real dependency/governance relationships.

Decomposition shall prefer vertical product slices over technical-layer decomposition.

#### FR-007 — Readiness and grooming

Epic, Feature and Spec readiness shall be explicit.

A work item is ready only when the next stage can proceed without inventing material product or architecture intent.

Missing product intent routes to the PRD owner. Missing architecture intent routes to Architect. Ambiguous ownership or consequential unresolved choice returns `HUMAN_DECISION_REQUIRED`.

#### FR-008 — Dependency-aware operational work graph

LARGE projects shall use one durable operational work-graph backend for Epics, Features, Specs, Bugs and their operational state.

It shall support the semantic relationship classes:

- Contains;
- Governed by;
- Depends on.

Dependencies must form a truthful DAG.

SubhForge shall:

- model real prerequisites only;
- derive eligible work deterministically;
- detect/block cycles;
- allow safe work across Epic/Feature boundaries;
- preserve independent work when another branch is blocked or reconciling.

The repository shall not maintain a second live Markdown Epic/Feature/Spec hierarchy.

#### FR-009 — Work plan and status

SubhForge shall provide deterministic, read-only projections of:

- current executable work;
- next eligible work;
- blockers and prerequisite chains;
- reconciliation holds;
- paused work;
- completed/active/remaining counts where meaningful.

Status/work-plan capabilities shall never mutate project state and shall avoid fake precision.

An incomplete, inaccessible or stale backend view must be reported as such; missing results must not be presented as zero work, successful completion or proven eligibility.

---

### 3.3 Delivery, verification and acceptance

#### FR-010 — Spec delivery

The normal Spec loop shall be:

```text
READY Spec
→ Implement
→ focused tests
→ Verify
→ Review
→ Complete
```

Known failures route to Fix. Unknown failures route through Diagnose then Fix. Authority contradictions route to Change Triage/Reconciliation.

Routine Spec completion shall not require Subhadeep approval.

After review approval, SubhForge may prepare and, where configured, raise a PR containing the bounded change plus useful Spec/requirement/evidence references. Automated PR creation is desirable but is not a v0.2 release gate.

#### FR-011 — Separation of implementation, verification and review

Implementation, verification and review are distinct responsibilities.

- Builder authors implementation and required tests.
- Verifier executes required checks and records factual evidence.
- Reviewer judges engineering quality against accepted authority/evidence.

Verification shall not invent expected behavior. Review shall not invent product intent.

#### FR-012 — Feature and Epic acceptance

Feature and Epic are the default human acceptance boundaries.

A Feature completes only after integrated verification is clear and Subhadeep accepts its human-evaluable capability (`AC-0`).

An Epic completes only after journey-level verification is clear and Subhadeep accepts its human-evaluable outcome (`AC-0`).

#### FR-013 — Planned integration/E2E ownership

Higher-level verification suites shall be planned delivery work, not hidden Verifier side effects.

- every Feature shall have an owning Spec for integration-suite work;
- every Epic shall have an owning Feature for E2E-suite work;
- Builder authors the suite;
- Verifier runs and evidences it.

---

### 3.4 Feedback, defects, change and recovery

#### FR-014 — Production/runtime/user feedback and defects

Feedback shall first be classified against current accepted authority.

- A proven implementation defect against already-accepted behavior enters Bug → Diagnose/Fix → Re-verify and does not require full reconciliation merely because it was observed in production.
- Feedback that reveals a missing/changed requirement, acceptance criterion, architecture obligation, dependency or planned behavior enters Change Triage and, when material, Reconciliation.

Escaped defects shall record the verification/planning layer where the problem should reasonably have been caught so repeated escapes improve future design/testing.

#### FR-015 — Change triage

SubhForge shall distinguish:

- `DEFECT`;
- `LOCAL_REFINEMENT`;
- `AUTHORITY_CHANGE`;
- `PROTECTED_ARCHITECTURE_CONFLICT`.

A fast/local path is allowed only when FR/NFR/invariant impact is explicitly understood.

A `LOCAL_REFINEMENT` fast path requires explicit Subhadeep approval.

#### FR-016 — Reconciliation

Accepted authority changes shall use:

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

#### FR-017 — Durable resume

Work shall resume by re-invoking the owning workflow against the same durable identity rather than depending on prior chat/session memory.

Safe progress shall persist before stopping because of time, cost, context pressure or external failure.

An uncertain write result must be resolved from authoritative state before retrying or reporting success. Resume must preserve durable logical identity and must not duplicate work merely because a response was lost.

---

### 3.5 Context, external capabilities and framework assurance

#### FR-018 — Bounded context

A work operation shall load minimum-sufficient current context:

- target work item;
- required ancestors;
- declared dependencies/contracts;
- applicable PRD/Architecture authority;
- relevant implementation surface;
- reconciliation obligations;
- required evidence.

Broad project history shall not be loaded by default.

#### FR-019 — Skills and external tools

Skills and MCP/tool integrations may provide reusable expertise/current external capability without becoming hidden authority.

They shall be admitted deliberately based on:

- demonstrated value;
- provenance;
- security/permission scope;
- context/tool cost;
- removability.

External output is untrusted input until validated/promoted into accepted authority.

#### FR-020 — Framework qualification

SubhForge shall use layered framework qualification:

1. deterministic unit/static/contract checks;
2. focused integration/FAST checks where real boundaries justify them;
3. limited model-bearing behavioral compatibility canaries;
4. release-level FULL qualification where justified;
5. real-project dogfood.

Synthetic smoke complements, but does not replace, real dogfood.

#### FR-021 — Caller-selected models and centralized model versions

Agent responsibility and model selection shall be independent. Subhadeep shall be able to invoke a logical agent with an explicit model-selection key, without editing that agent's definition.

- One predefined, durable execution-configuration map owns model keys, their concrete provider/model-version identifiers and configured agent defaults.
- An explicit caller selection takes precedence over the configured default for that agent. Omission uses the configured default; it does not permit the agent to guess a model.
- Agent definitions shall not hardcode provider model-version identifiers or duplicate the central map. Updating an existing key to a new compatible model version requires changing the map only, not every agent file.
- Selection is scoped to the addressed agent invocation. It does not silently change another agent, shared defaults or later calls.
- The selected key, map revision and resolved provider/model identifier shall be recorded with invocation evidence. Updating the map during a running invocation shall not silently switch its model.
- Unknown keys, missing defaults, unsupported capabilities or inability of the configured harness to honor the selection shall stop explicitly before model work begins. No silent provider, model or paid fallback is permitted.
- Model selection never expands authority or bypasses tool permissions, budget or context limits. A configuration change remains subject to the applicable behavioral compatibility check.

This requires a small central map and a supported selection path, not automatic discovery of new releases or a universal provider router. Adopting a new provider/harness may require adapter changes; upgrading a compatible version behind an existing supported key must not require agent-file edits.

#### FR-022 — Simple project setup and prerequisite verification

Starting a new SubhForge-managed project shall use a short guided setup path that does not require Subhadeep to manually copy agent files, assemble templates or reconstruct software prerequisites. This applies to the selected STANDARD/LARGE mode and supported local environment.

Setup shall:

- establish the intended project scope, durable mode and pinned SubhForge release/configuration references;
- make the applicable agent/capability definitions available to the configured harness and connect them to FR-021's central model map without duplicating model-version definitions;
- initialize the applicable project-local authority/document/configuration templates for the selected mode and entry stage; valid supplied authority may be admitted rather than overwritten or recreated;
- preserve the one-backend rule: operational Epic/Feature/Spec work is created through the selected backend, not a duplicate live Markdown hierarchy;
- check required software availability and compatible versions against the supported prerequisite manifest, including applicable runtime, Git, shell/harness and required integration dependencies; distinguish required, optional, missing, incompatible and unchecked conditions;
- verify locally checkable configuration/model-map/backend-binding prerequisites and report access/authentication checks honestly; any optional live check must expose its scope and cost rather than silently making paid model calls;
- report a clear readiness result with precise remediation and the safe next invocation, without claiming READY when a required prerequisite is unresolved;
- safely resume or repeat interrupted setup without duplicate identities, overwriting existing project work or destroying customizations. Managed files/changes must be identifiable and conflicts surfaced;
- keep prerequisite/health checking read-only. Installation, configuration mutation or remediation belongs to the setup path within the explicit invocation authorization, existing permission and budget boundaries; no silent system-wide installation, subscription or paid fallback is assumed.

Templates are starting structures, not accepted requirements, completed decisions or evidence. Setup readiness proves the environment is usable for the selected next stage; it does not bypass discovery, authority admission or delivery readiness gates. A project should remain understandable and recoverable without the original setup session.

---

## 4. Operating Model Requirements

The capabilities below define responsibility and handover boundaries required to satisfy the functional requirements. Physical command names, files and model assignments may change.

### 4.1 Logical responsibilities

| Agent / capability | Owns | Must not do |
|---|---|---|
| Ideation | Conversational/document intake, discovery, interviews, unresolved frontier | Decide PRD/Architecture |
| Research | **Optional** bounded research/evidence synthesis | Silently make product decisions |
| PRD | Canonical requirements | Mutate Architecture |
| Architect | Architecture, NFR reach, protected invariants | Silently change product intent |
| Planner / Decomposition | Epic/Feature/Spec decomposition, readiness, dependencies | Invent missing PRD/Architecture intent |
| Work-Plan | Eligible-work projection | Create dependencies or mutate state |
| Status | Progress/blocker explanation | Mutate state |
| Builder / Implementer | One accepted Spec and its tests | Change product/Architecture authority |
| Verifier | Execute checks and record evidence | Invent expected behavior |
| Reviewer | Engineering-quality judgement | Invent product intent |
| Diagnoser | Root-cause analysis | Choose unresolved product/Architecture semantics |
| Fixer | Bounded corrective mutation | Expand accepted behavior |
| Adversary | Independent challenge | Become authority |
| Change Triage | Classify feedback/change requests against accepted authority with cited FR/NFR/invariant context | Downgrade its own `AUTHORITY_CHANGE`; mutate authority or work |
| Reconciliation Planner | Impact analysis/proposed verdict | Perform semantic work mutation before approval |
| Reconciliation Executor | Apply approved reconciliation operations | Reinterpret approved intent |
| Setup / Health check | Guided project setup; read-only prerequisite and health reporting | Create accepted authority, activate delivery or make undeclared paid calls |
| Smoke/Qualification capabilities | Framework qualification | Become product-delivery authority |

The Change Triage and Setup / Health check rows are proposed (RV-32). They give FR-015 and FR-022 an owner in this matrix, restating Workflow §17.1 and §9.4; neither adds an agent.

### 4.2 Interaction requirements

Interaction depends on **initiator + target + intent + owning authority**.

- **Owning workflow → Subhadeep:** Ideation, PRD and Architect may interview Subhadeep for missing authoritative information or consequential decisions/approvals they cannot make.
- **Subhadeep → Agent:** a conversation about an existing artifact/work item defaults to bounded **explain/challenge**, not mutation.
- If an explain/challenge conversation becomes a request to change accepted authority, the receiving capability routes it to the workflow that owns that authority.
- Planner, Reviewer, Verifier, Status and other downstream capabilities do not gain product/Architecture mutation authority from conversation context.

Subhadeep may challenge the rationale of any responsible reasoning capability.

Research may ask only bounded clarification of an ambiguous/blocking research target. Builder may initiate blocking escalation, and Diagnoser may ask for evidence needed to resolve a blocking ambiguity. These are not downstream product/architecture interviews. Planner and Reconciliation Planner route missing upstream intent to the owning authority.

### 4.3 Handover requirements

Every handover must be reconstructable from durable state and explicitly identify the authority/evidence the receiver may rely on.

| From | To | Required handover |
|---|---|---|
| Ideation | PRD | Discovery materially complete; remaining items explicitly owned/non-blocking |
| PRD | Architect | Accepted canonical PRD with stable FR/NFR IDs and no material contradiction |
| Architect | Planner | Accepted Architecture, NFR reach, protected invariants and enforcement expectations |
| Planner | Builder | implementation-ready Spec, valid traces/contracts and no blocking dependency/reconciliation |
| Builder | Verifier | implementation + authored tests for accepted behavior; no hidden authority change |
| Verifier | Reviewer | current evidence tied to the implementation identity under review |
| Reviewer | Spec completion | review approved; evidence current; no reserved human decision outstanding |
| Specs | Feature verification | required child Specs complete + integration-suite owner/evidence ready |
| Features | Epic verification | required Features complete + E2E-suite owner/evidence ready |
| Feature/Epic verification | Subhadeep | automated gate clear + bounded human-evaluable `AC-0` |
| Change Triage | Reconciliation | cited FR/NFR/invariant context and conservative authority-change classification |
| Reconciliation Planner | Executor | explicit approved verdict with bounded operations/preconditions/postconditions |

A handover shall fail closed when mandatory authority, identity, evidence or ownership is missing.

### 4.4 Engineering-method and independent-reasoning requirements

SubhForge shall consider appropriate TDD, domain modelling, explicit API/event/data contracts, security, testability, observability, resilience, performance/cost, migration/backward compatibility, maintainability and research/prototyping/decision methods. Apply the smallest useful method to the accepted problem; industry practice alone does not justify extra machinery.

Skills/integrations are admitted only for demonstrated value, non-duplication, credible provenance/licensing, authority compatibility, bounded permissions/context/cost, portability, security and focused validation. Pin/adapt reviewed inputs and retain provenance. A capability that can be removed without material quality/reliability/cost loss does not earn global baseline scope.

Material architecture work may use ChatGPT and Claude for independent co-architecture: one develops an alternative analysis/recommendation, and synthesis remains subject to Subhadeep's acceptance. Independent challenge uses fresh bounded context. This creates neither dual authority nor a requirement to call both providers routinely; no particular provider is required for basic lifecycle continuity, and smoke does not consume Claude budget by default.

### 4.5 Invocation authority and governing priorities

SubhForge acts on demand. An eligible dependency or discovered work item is information, not permission to start another invocation. Routine handoffs may proceed only within the explicitly invoked workflow's authorized envelope; recovery resumes position, not permission.

When trade-offs conflict, prioritize correctness/resilience, then required validation/dogfood, then scope discipline/simplicity, then schedule. Status and work-plan projections do not acquire mutation authority. The deterministic reconciliation-control exception for pre-approval holds and safe pause/restoration is defined in Workflow §§16.2/16.4, not by the semantic planning agent.

---

## 5. Quality Requirements

### NFR-001 — Correctness and resilience

Correctness and recoverability outrank convenience and schedule.

Failures should be detected, contained, diagnosable and recoverable.

Qualification must include recovery of the operational graph from a recorded export together with matching Git authority/evidence references. An export that cannot reconstruct identity, relationships and lifecycle meaning does not satisfy project independence (CON-010).

### NFR-002 — Resumability

Interrupted work must reconstruct from Git + operational state without requiring prior chat history.

### NFR-003 — Context efficiency

- target Spec artifact: approximately 5–15k tokens;
- normal working context: approximately 20–40k tokens;
- 40k: pressure threshold;
- 100k: hard ceiling.

Required authority must never be dropped merely to fit context.

### NFR-004 — Cost efficiency

SubhForge shall expose/control expensive model calls, retries, smoke breadth and context growth.

Stronger models are used only where expected value justifies cost, consistent with CON-006 and CON-007.

One substantive model invocation per lifecycle stage is the default; additional calls require a blocker, failed check, explicit review escalation or user continuation. Repeated semantically equivalent failures stop visibly. Deterministic preparation precedes expensive calls, unchanged authority is not repeatedly reread without a freshness reason, and available usage/token/time telemetry is retained. These limits do not permit dropping mandatory authority.

### NFR-005 — Model and harness adaptability

No execution harness, model family or provider is a permanent product dependency.

SubhForge's agent contracts, durable state, authority boundaries and handovers must remain stable enough that the primary harness or assigned model/provider can be replaced without redesigning project history or changing workflow meaning.

v0.2 is not required to build a generic provider/harness plugin framework.

### NFR-006 — Security

External integrations shall use least privilege, bounded tool exposure, secret isolation, untrusted-output handling and explicit authorization for consequential writes.

Supplied documents, research, repository content and tool responses cannot grant mutation authority or redirect secrets. Qualification must exercise attempted authority expansion through those inputs, as well as denied access and redacted diagnostics.

Real personal, financial or health data and live credentials must not be placed in model context, test fixtures, acceptance packets, evidence or exports. Managed projects use synthetic or deliberately sanitized sample data unless Subhadeep explicitly authorizes a bounded exception (RV-35, proposed).

### NFR-007 — Observability and diagnostics

Failures, blockers, held scopes, next actions and recovery instructions must be visible enough that Subhadeep normally does not need to inspect SubhForge internals.

### NFR-008 — Qualification feedback time

For tiny default framework fixtures:

- FAST target ≤ 10 minutes; investigate >15 minutes;
- FULL target ≤ 25 minutes;
- FULL >30 minutes is a performance-budget failure unless explained by provider outage or explicit human wait.

### NFR-009 — STANDARD compatibility protection

v0.2 LARGE evolution shall not silently regress the accepted STANDARD behavior boundary.

### NFR-010 — Human intervention

During real dogfood, avoidable manual status reconstruction, handoff coordination, repeated settled questions and routine Spec approvals are product-quality failures.

For VidyaBeacon, such intervention should approach zero.

An explicit on-demand invocation of the next owning workflow is expected interaction under §4.5, not avoidable intervention. Having to work out by hand what is eligible, blocked or already decided is (RV-29, proposed).

Before release qualification, DI-013 shall define measurable acceptance thresholds for cost/context/scale, recovery and avoidable human intervention, including fixture size, environment, repeat policy and permitted exceptions. Narrative claims of "acceptable" behavior alone do not prove these NFRs.

---

## 6. Scope Exclusions

v0.2 shall not attempt to become:

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

The exclusions also cover arbitrary agent-to-agent communication, a generic project-management/graph database, vector DB/RAG for workflow state, and support for multiple harnesses merely to demonstrate abstraction.

### 6.1 Deferred capability boundary

Unless accepted evidence reopens scope, defer whole-Feature/Epic implementation in one invocation, additional specialized smoke fixtures, sophisticated effort-weighted progress percentages, broad cloud write integrations, rare automated invariant rebaseline, and richer provider/backend abstractions beyond the required seams. No local SQLite workflow-state database is assumed; reconsidering storage requires an explicit authority decision and must not create a second live state store.

---

## 7. Release Acceptance Requirements

A stable v0.2.0 release requires implementation **and evidence**.

### 7.1 Greenfield LARGE dogfood — MediBot

Prove the meaningful end-to-end lifecycle from discovery through Epic acceptance, including:

- dependency-aware planning;
- durable status/resume;
- implementation;
- verification/review;
- human Feature/Epic acceptance;
- recovery without hidden chat dependence.

### 7.2 Evolution/Reconciliation dogfood — MediBot Evaluation Guardrails

Prove safe authority change, including:

- bounded impact discovery;
- cross-Feature dependency propagation;
- propagation stopping at unaffected branches;
- protected-invariant conflict handling;
- missing-trace fail-closed behavior;
- in-flight Spec pause/adapt/resume/supersede;
- partial APPLY recovery/idempotency;
- evidence invalidation and re-verification.

### 7.3 Scale/context qualification — Autonomous Market Intelligence

Prove:

- multiple Epics/Features/Specs;
- cross-hierarchy DAG execution;
- multi-session resume;
- bounded context;
- status/work-plan quality;
- acceptable runtime/token/provider-cost behavior.

### 7.4 Release-wide evidence

Stable release additionally requires:

- accepted STANDARD + LARGE regression;
- install/bootstrap/doctor/release checks;
- model/harness behavioral compatibility canary;
- required adversarial cases;
- acceptable runtime/cost;
- sufficient diagnostics/recovery;
- removal/non-dependence on temporary construction scaffolding;
- Subhadeep's final acceptance of the release bar.

Schedule shall not weaken required dogfood or safety evidence.

---

## 8. Definition of Done

`stable_v0.2.0` may be declared only when:

1. the accepted PRD/Architecture/Workflow is implemented without known authority contradiction;
2. every release-blocking Discovery Item is CLOSED and its accepted result promoted;
3. the walking skeleton works end to end;
4. required deterministic gates and recovery paths work;
5. LARGE greenfield delivery has been dogfooded;
6. reconciliation has been dogfooded against real implemented lifecycle/evidence contracts;
7. scale/context behavior has been qualified;
8. STANDARD remains protected;
9. release/runtime/cost/security/diagnostic evidence is acceptable;
10. temporary construction tooling/evidence files are not required for product operation;
11. Subhadeep accepts that SubhForge is trustworthy enough to become delivery infrastructure for VidyaBeacon.

---

## 9. Success Criteria

SubhForge v0.2 is successful when:

1. Subhadeep can begin VidyaBeacon using a tested `stable_v0.2.0` release rather than continuing to design SubhForge.
2. A LARGE project can progress from idea to accepted Epic outcome without relying on hidden chat context.
3. Routine Spec delivery requires no recurring Subhadeep ceremony.
4. Material requirement/Architecture change can be reconciled without corrupting unaffected work.
5. Interrupted sessions resume truthfully from durable state.
6. The system explains why work is blocked/eligible without requiring internal debugging.
7. Model/harness changes cannot silently change authority or lifecycle semantics.
8. Dogfood shows Subhadeep spends attention on product/Architecture decisions rather than SubhForge bookkeeping.

---

## 10. Discovery Linkage

Unresolved research, design, review and pre-code work is intentionally **not embedded as competing requirements in this PRD**.

The single live frontier is:

`design/discovery/SUBHFORGE-V0.2-DISCOVERY.md`

Each Discovery Item uses a stable `DI-###` identity.

When a DI resolves:

- a product requirement/constraint change is promoted into this PRD;
- a structural answer is promoted into Architecture;
- lifecycle semantics are promoted into Workflow Contracts;
- release-proof decisions are promoted into Qualification;
- schedule-only decisions are promoted into the Delivery Timeline.

Discovery is working decision context, not a second source of product truth.
