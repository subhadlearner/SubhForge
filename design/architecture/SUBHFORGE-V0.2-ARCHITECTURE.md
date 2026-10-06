# SubhForge v0.2.0 — Architecture

**Status:** Draft reconciled to the clean v0.2 PRD and Discovery baseline  
**Date:** 2026-10-06

> **Authority relationship**
>
> - Product requirements: `design/prd/SUBHFORGE-V0.2-PRD.md`
> - Live unresolved questions: `design/discovery/SUBHFORGE-V0.2-DISCOVERY.md`
> - This document: durable structural architecture decisions
> - Detailed workflow behavior: `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md`
>
> An unresolved `DI-###` remains Discovery authority. This document must not guess its answer merely to appear complete.

The 2026-10-06 review corrections are proposals pending DI-001 acceptance. Physical choices remain open in their owning DIs; this review does not close them.

---

## 1. Vision

SubhForge is **Subhadeep's personal AI-assisted software-delivery orchestration
system**.

It is not merely a coding agent, not a generic engineering platform, and not a
workflow product intended for other developers.

Its purpose is to help Subhadeep take serious personal products such as
VidyaBeacon, MFBeacon, ArogyaBeacon and ArthaBeacon from idea to trustworthy
software while minimizing:

- lost context;
- repeated explanation;
- requirement drift;
- accidental architecture erosion;
- uncontrolled AI authority;
- unnecessary token/model cost;
- manual project coordination;
- framework maintenance during product development.

The desired operating model is:

> **SubhForge absorbs lifecycle ceremony. Subhadeep owns consequential product,
> architecture, acceptance and exception decisions.**

And the practical release test is:

> **Can Subhadeep build the next Beacon more reliably, economically and with less
> mental coordination using SubhForge than without it?**

### 1.1 Delivery boundary — ACCEPTED

The PRD defines four lifecycle segments. Architecturally, SubhForge is responsible for:

- **Requirement → Spec:** core lifecycle from conversational/document intake through Discovery, PRD, Architecture and decomposition.
- **Spec → reviewed implementation:** core lifecycle through implementation, tests, verification and review. PR creation is an optional terminal integration, not a release gate.
- **PR → Production:** outside the primary v0.2 lifecycle. SubhForge does not become a post-PR approval/deployment/release orchestration platform.
- **Production/feedback → delivery authority:** re-enters through either bounded Bug/Fix when accepted behavior is violated, or Change Triage/Reconciliation when requirements, architecture, acceptance criteria, dependencies or planned behavior must change.

This boundary prevents the framework from expanding into CI/CD or release-management scope while preserving safe product evolution.

---

## 2. Decision Status Vocabulary

The shared v0.2 decision-status vocabulary (`ACCEPTED`, `REVIEW`, `DEFERRED`, `NON-GOAL`) is defined once in `design/README.md`.

A settled architecture decision is reopened only because of contradiction, implementation limitation, new evidence, dogfood failure, meaningful cost/operational problem, or a deliberate human architecture revision.

---
## 3. Core Engineering Principles

### 3.1 Personal workflow first — ACCEPTED

Every capability must answer:

> **Does this materially help Subhadeep design, build, verify, reconcile or resume
> his own projects?**

If the benefit is unclear, do not add it.

### 3.2 Borrow the principle, not the enterprise machinery — ACCEPTED

Before inventing a SubhForge-specific mechanism:

1. understand the problem;
2. inspect credible established solutions;
3. identify the useful principle;
4. identify assumptions that do not fit SubhForge;
5. implement the smallest robust version needed for one developer + AI.

"Industry best practice" alone is not sufficient justification for complexity.

### 3.3 Determinism at mechanical boundaries — ACCEPTED

Use deterministic code for things software can prove reliably:

- lifecycle/state transitions;
- work-item identity;
- dependency integrity;
- DAG traversal;
- eligibility calculation;
- status projections;
- evidence freshness;
- schema validation;
- retry/budget accounting;
- mutation preconditions;
- smoke setup/assertions;
- context-size checks where mechanically measurable.

Use LLM reasoning for semantic work:

- product discovery;
- requirements reasoning;
- architecture trade-offs;
- decomposition;
- implementation reasoning;
- diagnosis hypotheses;
- semantic review.

### 3.4 Human authority for consequential decisions — ACCEPTED

Human judgement remains authoritative for:

- product intent;
- material requirement trade-offs;
- architecture decisions;
- Protected Architecture Invariant changes;
- reconciliation verdict approval;
- risk acceptance/waivers;
- human Feature/Epic acceptance;
- ambiguous ownership or conflicts.

When SubhForge cannot confidently classify a workflow-significant ambiguity,
it does not guess.

Use the shared stop principle:

`HUMAN_DECISION_REQUIRED`

### 3.5 Command on demand — ACCEPTED

SubhForge does not autonomously schedule or start work.

A dependency is:

- information;
- a constraint;
- an eligibility condition;

but **never permission to act**.

### 3.6 Vertical, human-verifiable decomposition — ACCEPTED

Prefer vertical product slices over technical-layer decomposition.

- Epics represent human-verifiable outcomes.
- Features represent human-verifiable capabilities.
- Specs represent implementation-ready behavioral slices.
- Foundations/cross-cutting work is front-loaded only when required by accepted architecture.

### 3.7 TDD and design discipline — ACCEPTED

Architecture/planning should actively consider appropriate engineering practices,
including:

- TDD where behavior can be expressed before implementation;
- domain-driven modelling where domain complexity justifies it;
- explicit API/event/data contracts;
- security-by-design;
- testability;
- observability;
- resilience/failure recovery;
- cost awareness;
- migration/backward compatibility where relevant.

These are supplied through curated skills and architecture reasoning rather than
blindly imposed as ceremony.

### 3.8 Safe failure and resumability — ACCEPTED

Failures should be:

> **detected → contained → diagnosable → recoverable**

Interrupted work must resume from durable authority, not model memory.

### 3.9 Low ceremony for the human — ACCEPTED

SubhForge may contain internal rigor, but it must not require Subhadeep to
manually maintain that rigor.

Human interaction should concentrate on:

`answer → question rationale → approve → verify/accept`

not bookkeeping.

SubhForge optimizes for **trustworthy autonomy, not maximum governance**.
Governance must not transfer coordination or routine decision load back to
Subhadeep. Human attention is reserved for consequential product, architecture,
acceptance, risk and exception decisions; everything safely derivable from
accepted authority should be handled by SubhForge.

Repeated avoidable human handoffs, repeated requests for already-settled
decisions, or routine decisions that SubhForge could safely derive are
architecture evidence, not obligations for Subhadeep to absorb.

### 3.10 Governing decision priorities — ACCEPTED

When architecture, validation, scope and schedule compete, use this order:

1. **Correctness and resilience**
2. **Required validation and dogfooding**
3. **Scope discipline and simplicity**
4. **Schedule**

Schedule is a planning constraint, not an architectural-correctness constraint.

If a justified change materially improves a required invariant or addresses a credible failure mode and survives the simplicity/cost test, make the change even when the plan must move.

Dogfooding/release evidence must not be weakened merely to preserve a target date.

The current product target is a trustworthy `stable_v0.2.0` by **December 31, 2026**, with VidyaBeacon beginning in **January 2027**. Schedule remains a planning constraint, not permission to weaken required architecture, recovery or dogfood evidence.

### 3.11 Project independence — ACCEPTED

A SubhForge-managed project must remain understandable, version-controlled and recoverable if **SubhForge or Kilo is unavailable**.

Core product/architecture/code truth must therefore remain inspectable outside a model or harness session. Operational work-backend exports/recovery paths, Git history, documented lifecycle semantics and deterministic recovery tooling must be sufficient to reconstruct what the project means and what state it is in.

SubhForge may improve coordination; it must not become the only way to understand the repository/project.


---

## 4. Authority and Execution Planes

### 4.1 Product Truth — Git — ACCEPTED

Git is the durable authority for:

- canonical discovery document;
- canonical PRD;
- canonical architecture document;
- source code;
- tests;
- architecture/ADR decisions where required;
- every **approved mutating reconciliation verdict** whose stable operations,
  preconditions and postconditions are required for APPLY/retry/recovery;
- optional supplementary reconciliation audit material when additional durable
  explanation is useful.

Canonical documents evolve **in place**.

Do not create:

- `discovery-v2.md`;
- `prd-v2.md`;
- `architecture-v2.md`;

for normal evolution. Git history already provides versioning.

### 4.2 Operational Work Graph — REVIEW (`DI-003`)

For LARGE projects, SubhForge will use **one external operational work-graph system of record** for:

- Idea/Research work items;
- Epics;
- Features;
- Specs;
- Bugs;
- lifecycle/status;
- acceptance criteria;
- requirement traceability;
- declared dependencies;
- implementation/PR links;
- reconciliation **operational state** such as phase/scope holds/obligation status (while the approved mutating verdict itself remains durable Git authority);
- durable escalation/blocker operational records such as `ESC-###` and `BLK-###`;
- verification state/evidence references where appropriate.

The repository should **not** contain a duplicate Markdown Epic/Feature/Spec tree.

The backend is deliberately **not settled yet**. Discovery `DI-003` requires evidence-based comparison of at least:

- **Jira**; and
- **GitHub Issues**.

The comparison uses the same representative work graph and measures:

- hierarchy/sub-item fit;
- dependency modelling;
- requirement-traceability representation;
- PR/commit linkage;
- human usability;
- MCP/API/tool support;
- read/write permission boundaries;
- partial-mutation recovery/idempotency;
- retrieval/context/token cost;
- **tokens/tool calls/latency specifically for high-frequency next-work queries**;
- **tokens/tool calls/latency specifically for high-frequency status queries**;
- native fallback when the primary AI tool path is unavailable;
- export/backup/recovery;
- vendor lock-in risk;
- status/work-plan query complexity.

The evaluation must remain bounded. If a candidate needs backend-specific rescue machinery merely to make the representative graph workable, that is negative evidence rather than permission to grow the comparison into a migration project.

Whichever backend wins becomes the **single live operational authority**. Discovery `DI-003` then defines the smallest backend schema needed by accepted requirements—no speculative fields or duplicated authority. A periodic machine-readable export is allowed for disaster recovery, but the export is never a second writable/live source of truth.

If both candidates prove unsuitable, preserve the **separation of Product Truth and Operational Work Graph** rather than returning automatically to thousands of repository planning artifacts.

### 4.3 Execution Plane — ACCEPTED

Execution combines:

- SubhForge lifecycle rules;
- specialized agents;
- deterministic utilities;
- Git/GitHub;
- CI/build/test tools;
- bounded MCP/tool access;
- selected LLMs.

Derived views such as status and work plans are projections, not third stores of
truth.

### 4.4 Cross-plane safety boundary — REVIEW (`DI-005`, `DI-006`)

Git and the external work backend do not provide one shared transaction. DI-005/DI-006 must define the smallest safe authority-activation and mutation protocol, including:

- how draft versus accepted authority and the exact approved revision are recognized;
- how an accepted revision invalidates old readiness/evidence before affected work can advance, including the window before REC candidate holds exist;
- version/fingerprint checks at mutation and completion boundaries, rather than trusting a context packet loaded earlier;
- ownership of serialization or equivalent conflict detection for overlapping invocations and manual backend edits;
- complete versus partial/paginated/unavailable reads;
- recovery after a successful remote write whose response is lost;
- durable create identity, duplicate detection and safe retry under the selected backend's actual API semantics.

Atomic transition semantics in Workflow §2.4 are a required observable guarantee, not an assumption that several remote writes are transactional. Qualification must prove the chosen protocol against real backend boundaries. No local cache or telemetry marker may override authoritative state.

---

## 5. Protected Architecture Invariants

### 5.1 Principle — ACCEPTED

Each approved product architecture may declare a small set of
**Protected Architecture Invariants**.

Examples may include:

- persistence/data-ownership boundaries;
- domain boundaries;
- eventing/consistency model;
- deployment topology;
- security/trust boundaries;
- observability architecture;
- CI/CD/build foundations;
- repository/data ownership;
- testing philosophy.

The exact list is project-specific.

The **semantics** of Protected Architecture Invariants are accepted here. Their smallest durable physical representation remains open under Discovery `DI-007`; implementation must not invent a heavyweight invariant subsystem before that decision closes.

### 5.2 Normal workflow rule — ACCEPTED

Planning, implementation, fixing and normal reconciliation cannot change a
Protected Architecture Invariant.

A conflict returns:

`PROTECTED_ARCHITECTURE_CONFLICT`

and stops before downstream work mutation.

### 5.3 Invariant Enforcement Matrix — ACCEPTED

Protected Architecture Invariants must not live only as prose.

When the Architect establishes an invariant, it also records its enforcement mode:

| Enforcement mode | Meaning | Owner |
|---|---|---|
| **DETERMINISTIC** | A static/architecture/dependency/contract/integration check can prove it mechanically. | `/verify` executes the declared check at the applicable level. |
| **SEMANTIC** | The invariant requires engineering judgement and cannot be reduced reliably to a mechanical assertion. | Architect/Reviewer checks it against bounded change context. |
| **MIXED** | Mechanical checks cover part of the invariant and semantic review covers the remainder. | `/verify` + Architect/Reviewer. |

Examples of deterministic candidates include forbidden layer/package dependencies, provider-specific SDKs leaking into domain code, repository/module boundary rules, explicit API/event contract conformance, and mandatory logging/correlation behavior where testable.

Do **not** create a separate fitness-function agent. For v0.2, deterministic invariant checks have one operational owner: **`/verify`**. CI may later reuse the same checks if dogfooding proves that useful, but duplicate execution is not required merely for ceremony.

### 5.4 Exceptional revision — ACCEPTED

v0.2 does **not** build a complex automated architecture-rebaseline subsystem.

If Subhadeep decides an invariant is genuinely wrong or must change:

1. perform an explicit architecture review;
2. revise canonical `architecture.md`;
3. review/approve the architecture PR;
4. then run normal reconciliation against the newly accepted authority.

Therefore:

> **Protected invariants are immutable to normal workflow, but changeable through
> explicit human-authorized architecture revision.**

---

## 6. Planned Tooling and Harness Boundaries

| Tool / Harness | Role | v0.2 Position |
|---|---|---|
| **VS Code** | Primary development environment | Existing / core |
| **Kilo** | Current primary execution harness for SubhForge commands/agents | Replaceable execution choice; must not define lifecycle semantics |
| **Git** | Versioned product/code/architecture authority | Core |
| **GitHub** | Repository hosting, commit/PR linkage and optional PR creation | Core repository integration; post-PR release orchestration remains out of scope |
| **Operational Work Graph Backend** | LARGE-project Idea/Epic/Feature/Spec/Bug graph | **REVIEW:** Discovery `DI-003` selects the backend and its minimal schema |
| **Claude Code + Pro** | Current bounded path for independent co-architecture/challenge and selected hard diagnosis | Current execution option, never authority or a required lifecycle dependency |
| **Python deterministic helpers** | Graph/status/smoke/context/evidence mechanics where code is stronger than prompting | Core principle |
| **Project CI/build/test tooling** | Product-specific build/test/deploy evidence | Chosen by project architecture; SubhForge must integrate without hard-coding one stack |
| **MCP / bounded external tools** | Current knowledge, repository/service access and bounded actions | Capability class; baseline integrations remain REVIEW under `DI-010` |
| **Skills** | Reusable engineering methods and technology guidance | Capability class; baseline global set remains REVIEW under `DI-010` |

### 6.1 Harness portability rule — ACCEPTED

Kilo is the primary harness for v0.2, but:

> **Kilo should run SubhForge; Kilo should not define SubhForge.**

Lifecycle semantics, work graph, context contracts, evidence contracts and
authority boundaries should sit behind narrow seams so a future harness change
does not require redesigning project history.

This is **migration-friendly architecture**, not a generic multi-harness
platform.

### 6.2 Management-tool portability rule — ACCEPTED

Jira or GitHub Issues may become the selected operational system of record, but
backend-specific API/MCP call shapes must not spread throughout agents.

Agents should reason in capabilities such as:

- get work item;
- get ancestors;
- get declared dependencies;
- query eligible children;
- update lifecycle state;
- create/link work item;
- attach implementation/evidence reference.

This is a narrow tool boundary, **not** a generic work-management plugin
framework. v0.2 needs only the adapter surface required by the selected backend;
it does not implement interchangeable backends merely to prove abstraction.

### 6.3 Model and harness adaptability rule — ACCEPTED

Neither a model/provider nor the execution harness may define SubhForge semantics.

Changing Kilo, model family or provider must not change:

- authority;
- context contract;
- mutation permission;
- acceptance criteria;
- lifecycle semantics;
- durable work identity/history;
- handover meaning.

Models and harnesses are replaceable workers/execution surfaces behind stable SubhForge contracts. v0.2 requires **migration-friendly seams**, not a universal provider or multi-harness plug-in framework.

---

## 7. Current Model Assignment Strategy — CONFIGURABLE

Logical agent responsibility is architecture. **Model assignment is execution policy** and may change for quality, price, availability or tooling reasons without changing workflow semantics.

Current baseline:

| Model family | Primary use | Cost/authority rule |
|---|---|---|
| **GPT-5.6 Sol** | Product/requirements planning, architecture reasoning, decomposition, senior review, synthesis | Default high-value reasoning |
| **GPT-5.6 Luna** | Lightweight orchestration, init/status/smoke bookkeeping where reasoning demand is lower | Economical support |
| **DeepSeek** | High-volume implementation, deterministic-adjacent coding, tests, routine fixes, bounded spikes | Cost-sensitive execution |
| **Claude Sonnet** | Co-architecture analysis for material decisions plus independent challenge/review in a fresh bounded context | Prefer Claude Code + Pro handoff where applicable |
| **Claude Opus** | High-risk/critical co-architecture, architecture challenge, hard diagnosis and selected complex review | Escalation / explicit use only |

Rules:

- the table above is a current default, not durable authority;
- no silent model fallback;
- model escalation does not increase mutation authority;
- material architecture work may use both ChatGPT and Claude as bounded co-architects; ChatGPT normally leads synthesis, while Claude develops an alternative analysis/recommendation and may separately challenge the proposal from a fresh context;
- dual-model architecture input does not create dual authority: Subhadeep decides and accepted authority exists only after review/persistence;
- Claude is not required for basic workflow continuity;
- smoke does not consume Claude budget by default;
- stronger models are used where the expected quality gain justifies cost;
- no universal provider-routing framework in v0.2.

---

## 8. Logical Agent Architecture

Physical Kilo filenames may evolve; these logical names, responsibilities and authority boundaries are architectural. Discovery `DI-008` owns the eventual logical-role → physical-command/agent mapping.

| Specific agent / capability | Responsibility | Authority boundary | Capability / entrypoint | Model association | Grill direction |
|---|---|---|---|---|---|
| **Ideation Agent** | Accept conversational ideas or Subhadeep-supplied documents/notes; extract known facts; interview for missing discovery; create/maintain discovery and research frontier | May author/refine discovery within its stage; cannot decide later PRD/architecture authority | `/ideate` | Strong primary reasoning model; currently GPT-5.6 Sol | **BI** — Agent may actively interview Subhadeep; Subhadeep may challenge rationale |
| **Research Agent** | **Optional** bounded evidence synthesis/closure for a durable research item; help promote justified conclusions into discovery | Evidence/closure support only; Subhadeep may research directly; cannot silently make product decisions | bounded Research/Idea work item | Sufficient reasoning model for the research | **BI (bounded)** — Agent→Subhadeep only when the research target itself is ambiguous/blocking; Subhadeep→Agent always allowed |
| **PRD Agent** | Produce/refine canonical PRD from accepted discovery/research | PRD authority only through reviewed/accepted change; no architecture mutation | `/prd` | Strong primary reasoning model; currently GPT-5.6 Sol | **BI** — Agent may actively interview for missing product intent/approval; Subhadeep may challenge rationale |
| **Architect Agent** | Create/revise architecture; classify NFR reach; define Protected Architecture Invariants and enforcement | Architecture through reviewed/accepted change; normal workflows cannot change protected invariants | `/architect` | Strong primary reasoning model; Claude Sonnet currently used for material independent co-architecture, Opus by explicit escalation | **BI** — Agent may actively interview for missing architecture intent/approval; Subhadeep may challenge rationale |
| **Planner / Decomposition Agent** | Decompose accepted PRD + architecture into Epic → Feature → Spec and truthful dependencies | Operational planning only; cannot redefine PRD/architecture or invent missing intent | `/epic`, `/feature`, `/spec` planning/grooming | GPT-5.6 Sol | **UNI — Subhadeep → Agent** for rationale. If a readiness gate exposes missing product/architecture intent, Planner records/routes an upstream gap to the owning agent; Planner does not ask Subhadeep to resolve that intent directly |
| **Work-Plan Capability** | Compute executable order from DAG + current state | Read-only derived projection; cannot create dependencies or mutate lifecycle | derived work-plan projection | Deterministic first; LLM only for explanation | **UNI — Subhadeep → capability** |
| **Status Capability** | Explain progress, eligibility, blockers, reconciliation holds and next work | Read-only projection; never changes work state | `/status` | Deterministic first; lightweight explanation | **UNI — Subhadeep → capability** |
| **Builder / Implementer** | Implement one accepted Spec | Code/workspace changes within Spec authority; no product/architecture authority | `/implement` | DeepSeek default; explicit stronger-model escalation | **BI (escalation-bounded)** — Subhadeep may question rationale; Agent→Subhadeep only through a blocking escalation |
| **Verifier** | Run factual Spec/Feature/Epic checks and produce evidence | Evidence only; cannot redefine expected behavior or acceptance | `/verify` | Deterministic tooling + lightweight agent | **UNI — Subhadeep → Agent** |
| **Reviewer** | Judge implementation quality against accepted authority/evidence | May request code changes; cannot invent product intent or alter authority | `/review` | Sol senior review; cheaper pre-review where useful | **UNI — Subhadeep → Agent** |
| **Debugger / Diagnoser** | Determine root cause when cause is unknown | Diagnosis only; cannot choose unresolved product/architecture semantics | `/diagnose` | DeepSeek default; Claude/Sol escalation for hard cases | **BI (evidence-bounded)** — Subhadeep may question rationale; Agent→Subhadeep only when evidence cannot resolve a blocking ambiguity |
| **Fixer** | Apply corrective change once failure is understood | Bounded corrective mutation only; cannot expand accepted behavior | `/fix` | DeepSeek default | **UNI — Subhadeep → Agent** |
| **Adversary** | Independently challenge high-risk decision/implementation | Findings are evidence, never authority | `/adversarial-check` | Claude/Sol/DeepSeek according to risk | **UNI — Subhadeep → Agent** |
| **Reconciliation Planner** | Analyse accepted authority delta; derive affected scope/evidence/dependencies; produce verdict | No semantic/content work-graph mutation; deterministic control layer alone may acquire/release holds and pause affected ACTIVE Specs | `/reconcile` ANALYZE | GPT-5.6 Sol | **UNI — Subhadeep → Agent**; upstream ambiguity routes to owning authority |
| **Reconciliation Executor** | Apply an approved verdict to operational work graph | Only mutations explicitly authorized by approved verdict; no semantic reinterpretation | `/reconcile` APPLY | Deterministic mutation layer + bounded tool calls | **UNI — Subhadeep → capability** |
| **Smoke Orchestrator** | Select/profile framework validation at appropriate breadth | Test orchestration only | `/smoke` orchestration | GPT-5.6 Luna / orchestrator | **UNI — Subhadeep → capability** |
| **Smoke Executor** | Execute deterministic/model-bearing smoke scenarios | Disposable test fixture only | `/smoke` scenario execution | Cheapest model satisfying scenario | **UNI — Subhadeep → capability** |

**Grill direction legend**

- **BI** — both Subhadeep and the agent may initiate questioning within the stated boundary.
- **UNI — Subhadeep → Agent/Capability** — Subhadeep may challenge/explore rationale; the agent does not initiate requirement interrogation.
- A BI qualifier such as **bounded**, **escalation-bounded** or **evidence-bounded** narrows when the agent may initiate.

### 8.1 Interaction and question authority — ACCEPTED

Interaction meaning is determined by **initiator + target + intent + owning authority**.

**Owning workflow → Subhadeep**

Ideation, PRD and Architect may actively interview Subhadeep while authoring/refining their authority for only two broad reasons:

1. obtain missing authoritative information; or
2. obtain a consequential decision/approval that the agent may not make itself.

Research may initiate only bounded clarification when the research target itself is ambiguous/blocking. Builder and Diagnoser may initiate only bounded blocking escalation within their authority.

**Subhadeep → Agent**

Subhadeep can always ask the responsible reasoning agent:

- Why did you make this choice?
- Why is this one Epic instead of two?
- Why is this Spec dependent on that one?
- Why is this technology/architecture appropriate?
- Why is this work not next?

When Subhadeep initiates such a conversation against an existing artifact/work item, the default mode is **bounded explain/challenge**, not mutation. The agent reconstructs current durable context and explains its rationale.

If the conversation becomes a request to change accepted authority, the receiving agent routes that request to the workflow that owns the authority. Conversation context never expands mutation permission. For example, Planner/Reviewer cannot silently change architecture because the discussion began with them.

**Planner/Reconciliation Planner** should receive settled product/architecture authority. A material ambiguity means an **upstream gap**, not another planning interview.

The exact physical mechanism for distinguishing these interaction modes remains open under Discovery `DI-008`; prefer derivation from command/target/owner rather than a new conversational state engine.

### 8.2 One owner per responsibility — ACCEPTED

Do not let:

- implementation absorb verification;
- verification absorb review;
- planning rewrite architecture;
- status mutate work;
- research silently decide product intent;
- reconciliation analysis semantically mutate planned work, dependencies, acceptance, lifecycle completion or authority before approval. **The sole pre-approval exception is deterministic reconciliation-control bookkeeping:** acquire/release the REC scope hold and transition an affected `ACTIVE` Spec to `PAUSED_FOR_RECONCILE` so stale implementation cannot continue. Safe restoration after a recorded no-impact/cancellation outcome follows Workflow §§16.2/16.4; it does not grant semantic mutation authority.

---

## 10.1 Requirement Identity and Traceability Architecture

---

The following requirement-identity and traceability **semantics** are **ACCEPTED**. Their physical Git/backend representation remains open under Discovery `DI-005`:

Canonical PRD requirements use **stable, permanent identifiers**.

Baseline convention:

- functional requirements: `FR-###`;
- non-functional requirements: `NFR-###`.

Identity rules:

- an FR/NFR ID is never renumbered;
- an FR/NFR ID is never reused for a different requirement;
- ordinary edits retain the same ID when the requirement remains the same authority;
- an obsolete requirement is marked **RETIRED** rather than deleted/resequenced;
- Git history preserves the prior meaning of retired requirements;
- no workflow may infer requirement identity from list position or heading order.

### Functional requirement traceability

FRs normally trace directly into the operational work graph because they describe product behavior or capability:

```text
FR-017
  ↓ traces-to
Epic / Feature / Spec candidates
  ↓ dependency closure
bounded candidate affected set
  ↓
semantic reconciliation analysis
```

Rules:

- work items reference FR IDs rather than copying authoritative requirement text;
- Epics/Features/Specs link only to FRs they materially realize;
- traceability answers **why this work exists**; the dependency DAG answers **what must precede what**;
- when an FR changes, its directly traced work items form the deterministic initial impact candidate set;
- dependency closure expands that candidate set;
- the Reconciliation Planner performs semantic impact judgement only over that bounded set, plus any explicitly detected traceability gaps.

### Non-functional requirement traceability

NFRs do **not** automatically trace like FRs because many are cross-cutting.

Each NFR is classified by **`/architect` at architecture time** as one of:

- **CROSS_CUTTING** — governs architecture or broad system quality;
- **SCOPED** — applies only to a defined capability/surface.

The PRD owns the NFR's intent; the Architect owns its architectural classification,
governance relationship and enforcement mapping.

NFR classification is itself durable architecture authority. If an NFR later moves
from `SCOPED` to `CROSS_CUTTING` (or the reverse), that change is an
**`AUTHORITY_CHANGE`** because it can create/remove architecture obligations,
Protected Architecture Invariants and/or Enforcement Matrix rows. It must therefore
enter the normal reconciliation path rather than being treated as a local metadata edit.

For a **CROSS_CUTTING** NFR:

```text
NFR-003
  ↓ governs
Architecture obligation / Protected Invariant / Quality Policy
  ↓
Invariant Enforcement Matrix row(s)
  ↓
applicable implementation scopes + verification checks
```

Examples include system-wide security, observability, architectural-boundary or resilience requirements.

For a **SCOPED** NFR, the NFR may additionally trace directly to the relevant Feature/Spec when that is the clearest authoritative relationship.

Not every NFR becomes a Protected Architecture Invariant. The Architect decides whether the NFR is:

- a protected invariant;
- another architecture/quality policy;
- or a scoped verification obligation.

A change to an NFR starts impact discovery from its declared governance/enforcement relationships, then expands through affected scopes and dependencies before semantic reconciliation.

### Missing-trace rule

Missing traceability is a **coverage gap**, never evidence that a work item is unaffected.

If SubhForge cannot establish the relevant FR/NFR relationship cleanly, it stops or routes the gap for repair rather than silently narrowing the impact set.

This makes impact discovery **deterministic narrowing → semantic judgement**.

---

## 19. Skill Architecture

Skills are reusable **engineering knowledge/method**, not hidden authority.

Authority precedence remains:

1. accepted PRD;
2. accepted architecture/ADRs;
3. project rules;
4. project-local skills;
5. curated global skills;
6. generic model knowledge.

A skill cannot silently replace an approved product/technology decision.

### 19.1 Current available/candidate skill inventory — REVIEW (`DI-010`)

The following inventory is useful input, but **does not mean every listed skill belongs in the v0.2 global baseline**. Discovery `DI-010` decides the smallest set that earns global scope.

| Skill | Primary responsibility |
|---|---|
| `requirements-grilling` | Product/design interrogation and ambiguity removal |
| `tdd` | Behavioral red → green implementation discipline |
| `diagnosing-bugs` | Root-cause-first debugging |
| `adversarial-check` | Independent challenge of high-risk decisions |
| `security-verification` | Security verification, supply-chain/secrets/IaC/cloud evidence discipline |
| `dotnet-production` | Production .NET/C#/ASP.NET guidance |
| `python-production` | Production Python guidance |
| `postgresql-production` | PostgreSQL modelling/transactions/index/query guidance |
| `sqlite-production` | SQLite correctness/concurrency/migration guidance |
| `frontend-design` | Intentional frontend design |
| `web-design-guidelines` | Accessibility/UX/interface review |
| `react-best-practices` | React performance/data-flow/component guidance |
| `nextjs-production` | Next.js production/App Router practices |
| `aws-serverless` | AWS serverless architecture/implementation |
| `aws-iam` | IAM policy/trust/boundary correctness |
| `amazon-dynamodb` | Access-pattern-led DynamoDB design |
| `azure-architecture` | Azure reliability/security/operations/cost |

### 19.2 Capability families to evaluate under `DI-010`

Whether by an existing skill, adapted skill, command, deterministic tool or
project rule, evaluate coverage for:

- software/module/interface design;
- architecture trade-offs;
- domain modelling;
- API/event/data-contract design;
- resilience/failure recovery;
- testing architecture/testability;
- observability/operability;
- security/threat modelling;
- performance/cost engineering;
- migration/backward compatibility;
- refactoring/maintainability;
- research/prototyping/decision methods;
- code/spec/standards review.

Candidate external sources already identified include credible work from:

- Matt Pocock: `wayfinder`, `codebase-design`, `domain-modeling`,
  `research`, `prototype`, `to-spec`, `to-tickets`, `tdd`,
  `diagnosing-bugs`, `code-review`;
- Addy Osmani's agent-skill work;
- official/vendor guidance;
- mature open-source engineering workflows.

These are **sources to evaluate**, not automatically installed dependencies.

### 19.3 Skill admission gate — ACCEPTED

A skill earns global scope only when it passes:

1. real need/value;
2. non-duplication;
3. credible source;
4. provenance/license/adaptation record;
5. authority compatibility;
6. bounded tool/permission needs;
7. acceptable context/token cost;
8. determinism fit;
9. portability fit;
10. security/supply-chain review;
11. focused validation/dogfood evidence;
12. removal test: if removal would not materially hurt quality/reliability/cost,
    it does not deserve global scope.

Preferred lifecycle:

`inspect → understand → pin/version → adapt → record SOURCE.md → test`

not:

`install latest → trust automatically`

---

## 20. MCP Philosophy

MCP is for:

- authoritative current knowledge;
- live repository/service access;
- bounded external action.

MCP is a **tool/transport boundary**, not an authority boundary.

An MCP response does not become project truth just because an agent saw it.

### 20.1 Candidate MCP / integration classes — REVIEW (`DI-010`)

| Integration | Intended use | v0.2 position |
|---|---|---|
| **Work-management integration** | Read/mutate operational work graph | Required capability; concrete backend/transport follows `DI-003` and `DI-010` |
| **GitHub repository integration** | Repository/commit/optional-PR operations and GitHub Issues if selected as work backend | High-value/core repository boundary; exact baseline tool surface follows `DI-010` |
| **Official documentation/knowledge integrations** | Current .NET/Azure/platform knowledge where freshness matters | Evaluate selectively |
| **AWS/Azure platform integration** | Bounded inspection and carefully authorized operations | Project-specific; not globally enabled by default |
| **Human-in-the-loop/notification integration** | Reduce interaction friction where useful | Optional / evidence-driven |

### 20.2 MCP admission/security gate — ACCEPTED

Before normal use:

- concrete need is identified;
- official/trusted source is preferred;
- least privilege;
- read-only by default;
- exact tools/namespaces are allowlisted;
- consequential writes require human authorization where appropriate;
- secrets isolated from prompts/artifacts/logs;
- external output treated as untrusted input;
- prompt/tool poisoning considered;
- material schema/version/permission changes trigger re-review;
- fail-safe degradation;
- meaningful actions auditable;
- context/tool-discovery cost acceptable;
- mechanical correctness remains local where stronger;
- safe-path + denied/failure-path validation exists.

Possible integration decisions:

`REJECT | WATCH | READ_ONLY_PILOT | APPROVE_BOUNDED`

---

## 21. Bounded Context

### 21.1 Context targets — ACCEPTED

- **Spec artifact target:** roughly **5–15k tokens**.
- **Normal working context:** roughly **20–40k tokens**.
- **40k:** pressure threshold; optimize/reduce optional context, but never drop
  required authority.
- **100k:** hard ceiling; stop rather than silently overflow.

### 21.2 Context assembly — ACCEPTED

A work-item operation normally loads only:

- target operational work item;
- required parent/ancestor scope;
- declared dependencies/contracts;
- relevant canonical Git authority;
- relevant implementation surface;
- active reconciliation obligations;
- required verification evidence.

Do not load broad project history by default.

### 21.3 Context freshness — ACCEPTED

Agents must retrieve current authority when correctness depends on freshness.
Do not rely on stale chat context.

Within one stage, unchanged authority should not be reread repeatedly without a
specific freshness reason.

### 21.4 Bounded rationale conversation — ACCEPTED

A major SubhForge differentiator is the ability to converse with the
**responsible agent in the bounded context of one artifact/decision**.

This is the Subhadeep-initiated **explain/challenge** side of §8.1; it does not grant additional mutation authority.

Examples:

- "Why is FEATURE-24 separate from FEATURE-25?"
- "Why did you choose eventing here?"
- "Why is SPEC-41 blocked?"
- "Why does this change require re-verification?"
- "Why isn't EPIC-3's next item ready?"

The agent should reconstruct the necessary narrow context from durable systems
of record instead of requiring Subhadeep to restate project history.

---

## 22. Cost and Retry Discipline

- one substantive model invocation per lifecycle stage is the default;
- extra invocations require blocker, failed check, explicit review escalation or
  user continuation;
- repeated semantically identical failures stop instead of burning budget;
- deterministic preparation happens before expensive model calls;
- model usage/token/time telemetry is captured where practical;
- mandatory context is never dropped merely to hit a budget.

---

## 23A. Lifecycle Observability — REVIEW (`DI-009`)

> **Kilo owns harness/runtime telemetry. SubhForge owns lifecycle observability.**

Kilo logs may be useful evidence, but they are not by themselves the SubhForge observability model.

The PRD requires diagnosable lifecycle behavior. The following is the **candidate minimum set** to validate under `DI-009`; retain only what is necessary to answer what happened, why work stopped, what authority/evidence was used and what safe next action exists:

- operation / command / capability;
- target Project/Epic/Feature/Spec/Bug/REC/ESC/BLK;
- starting and resulting lifecycle state;
- deterministic gates/checks and their outcomes;
- selected bounded context identity where relevant;
- harness/model invocation identity where relevant;
- proposed and committed mutations;
- block/escalation reason and required next action;
- retry / repair / recovery attempt;
- verification/evidence changes;
- causal failure chain linking the originating operation to the final failure/block.

Prefer the **minimum useful implementation** for one developer + AI:

- structured lifecycle events;
- stable correlation IDs;
- deterministic diagnostics;
- reuse/linkage of Kilo telemetry where it helps.

Do not introduce a heavyweight telemetry platform unless qualification demonstrates material value.

Observability must support diagnosis and recovery without making Kilo-specific runtime logs the authority for SubhForge lifecycle truth.

---
## 29A. v0.2 Implementation Sequence — ACCEPTED

Reconciliation must be implemented/tested against the real verification and evidence state model, not a half-defined placeholder.

Preferred implementation dependency order:

```text
Authority planes + selected work-backend foundation
        ↓
Stable FR/NFR identity + traceability
        ↓
Planning / decomposition / truthful DAG
        ↓
Status + resume + work-plan projection
        ↓
Spec implement / verify / review
        ↓
Feature verification + human acceptance
        ↓
Epic verification + human acceptance
        ↓
Reconciliation
        ↓
Intelligent smoke + dogfood qualification
```

Feature/Epic verification semantics, evidence freshness and completion states are therefore implemented before reconciliation qualification.

Reconciliation may be designed in parallel, but it does not pass its architecture/release gate until it operates against the actual implemented verification/evidence states.

This dependency order is architectural; calendar dates are planning concerns and must remain consistent with the PRD target. Qualification evidence is owned by the active Qualification document.

No v0.1.1 bridge, `/specbypassceremony`, temporary `/arch-*` review system or separate implementation-tooling framework is required to preserve this dependency order. Implementation planning should derive bounded work directly from the accepted PRD, Architecture, Workflow Contracts and current Discovery decisions.

---
## 25. Capability Index — NON-DUPLICATING

This index preserves the user-facing capability view without restating normative rules.

| Capability | Normative home |
|---|---|
| Bounded two-way reasoning / grill direction | §8 in this document |
| Durable work-item resume | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §17.3 |
| Dependency-aware work planning | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §11 |
| Explainable status | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §17.2 |
| Protected architecture | §5 in this document |
| First-class reconciliation | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §16 |
| Analyse → approve → apply separation | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §16 |
| Replaceable AI workers / harness boundaries | §§6–8 in this document |
| Skills + MCP | §§19–20 in this document; baseline scope resolves through `DI-010` |
| Feature/Epic verification + human acceptance | `design/workflow/SUBHFORGE-V0.2-WORKFLOW-CONTRACTS.md` §§13–14 and §23 |
| Intelligent validation economics | `design/qualification/SUBHFORGE-V0.2-QUALIFICATION.md` §24 |
| Human authority with low ceremony | §3 in this document |
| Small repository knowledge surface | §4 in this document |
| Long-lived project context | §21 in this document |

---

## 33. Non-Goals for v0.2

Do not turn SubhForge into:

- a generic workflow platform;
- a post-PR CI/CD, organizational approval or production-release orchestration platform;
- a provider plugin marketplace;
- a universal model router;
- a generic project-management database;
- a graph database/knowledge graph;
- a vector DB/RAG requirement for workflow state;
- autonomous scheduling/background watchers;
- arbitrary agent-to-agent communication;
- multi-user/team workflow;
- enterprise governance framework;
- automatic architecture rebaseline engine;
- support for multiple harnesses merely to prove abstraction.

---

## 34. Deferred Until Evidence Requires It

- direct implementation of an entire Feature/Epic instead of Spec-by-Spec;
- additional specialized smoke fixtures beyond demonstrated need;
- sophisticated effort-weighted project completion percentages;
- richer tool-provider abstraction beyond narrow boundaries;
- SQLite/local workflow state DB unless measured need returns after selected
  work-graph implementation;
- automation of rare Protected Architecture Invariant rebaseline;
- broad cloud MCP write capability.

---

## 38. Final Success Criterion

SubhForge v0.2 succeeds when Subhadeep can return to a serious project after
days or months, identify a durable work item, and confidently continue because:

- product intent is durable;
- architecture is protected and enforceable where mechanical checks are possible;
- operational work state is navigable;
- dependencies are truthful;
- the next work is explainable;
- context is reconstructed automatically;
- agents have narrow authority;
- engineering skills/current tools are available on demand;
- verification evidence is trustworthy;
- requirement changes can be reconciled safely;
- failures are diagnosable/recoverable;
- model/tool/harness choices can evolve without rewriting the lifecycle;
- and Subhadeep spends his time building the product rather than maintaining
  SubhForge.

Open structural details remain governed by `design/discovery/SUBHFORGE-V0.2-DISCOVERY.md`; an implementation must not silently close them.

> **The machine owns coordination. Subhadeep owns judgement.**
