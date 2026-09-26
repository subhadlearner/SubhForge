---
description: Initialize repository instructions, rules, and curated skills from the approved architecture
agent: code
model: openai/gpt-5.6-luna
---

# Project Initialization Workflow

Initialize the repository for implementation using the approved PRD, architecture, ADRs, and project constraints.

This workflow prepares the repository for implementation.

It does NOT implement application functionality.

## Purpose

The purpose of this workflow is to ensure that the technology stack, repository instructions, developer documentation, project-specific rules, and relevant AI skills are established before implementation begins.

The implementation agent must never be allowed to invent the technology stack simply because repository instructions are incomplete.

## Stage 1 — Load Approved Project Context

Read only the project context required to initialize the repository:

- approved PRD
- approved architecture
- relevant ADRs
- existing project-level `AGENTS.md`
- existing `README.md`
- existing `.kilo/rules/`
- existing `.kilo/skills/`
- relevant repository configuration

Do not scan unrelated implementation files or unrelated documentation.

## Stage 2 — Determine the Approved Technology Baseline

The technology stack must come from the approved architecture and ADRs.

The architecture stage is the authority for technology decisions.

Extract the approved values for:

- programming language
- runtime/version
- application framework
- API style where relevant
- database/storage technology
- cloud provider
- cloud region where specified
- infrastructure-as-code technology
- package/dependency manager
- unit-test framework
- integration-test approach
- E2E-test approach when applicable
- linting tools
- formatting tools
- type-checking/static-analysis tools
- security-analysis tools where specified
- deployment approach

Do NOT independently choose or replace any major technology.

Do NOT infer a stack merely because one would be convenient.

If a technology decision required for implementation is missing, conflicting, or materially ambiguous:

STOP.

Return:

`PROJECT_INIT_BLOCKED`

Include:

- the missing decision
- why implementation depends on it
- the relevant PRD/architecture/ADR reference
- the minimum clarification required

Do not continue until the architecture decision is resolved.

## Stage 3 — Update Project AGENTS.md

Update the repository-level `AGENTS.md`.

Preserve relevant existing instructions.

The project-level `AGENTS.md` must describe the actual approved project rather than remaining as an unfilled template.

Populate, where applicable:

### Project Overview

- project purpose
- important domain context
- major system responsibilities

### Technology

- language
- runtime/version
- framework
- database
- cloud provider
- region
- IaC technology
- package manager

### Build and Verification Commands

Provide actual commands for:

- dependency restore/install
- build
- unit tests
- integration tests
- E2E tests when applicable
- lint
- formatting verification
- type checking/static analysis
- dependency vulnerability scanning when configured
- secret scanning when configured
- SAST/static security analysis when configured
- IaC security scanning when configured
- container/image scanning when configured

Commands must correspond to the approved stack.

Do not invent commands for tools that are not part of the project.

### Architecture Constraints

Record only implementation-relevant approved constraints.

### Coding Conventions

Record project-specific coding expectations where known.

Do not invent conventions when no project decision exists.

### Testing Requirements

Record project-specific testing requirements.

### Security Constraints

Record relevant security requirements, including where applicable:

- authentication/authorization invariants
- secret handling
- sensitive-data handling
- applicable OWASP Top 10:2025 risks
- approved security verification tools/commands
- explicitly required security gates
- project waiver policy and any non-waivable categories

When security verification is materially relevant, include the global `security-verification` skill in the Skill Coverage Matrix as `ALREADY_AVAILABLE`.

### Cloud and Cost Constraints

Record implementation-relevant cost constraints.

### Deployment Constraints

Record environments, IaC requirements, deployment restrictions, and human approval requirements.

Do not put secrets in `AGENTS.md`.

## Stage 4 — Update README.md

Update the repository-level `README.md`.

The README must accurately describe the current project state.

Include, where applicable:

- project purpose
- technology stack
- high-level architecture summary
- prerequisites
- local development commands
- repository structure
- engineering workflow

Do not claim a feature exists merely because it appears in the PRD or architecture.

Distinguish clearly between:

- implemented functionality
- planned functionality
- documentation-only design decisions

## Stage 5 — Ensure Workflow Artifact Directories

Ensure the repository contains the standard workflow artifact directories:

- `docs/discovery/`
- `docs/prd/`
- `docs/architecture/`
- `docs/adr/`
- `docs/specs/`
- `docs/diagnostics/`
- `docs/verification/`
- `docs/verification/waivers/`
- `docs/verification/smoke/`
- `docs/reviews/`
- `docs/workflow/`

Create missing directories using a repository-appropriate placeholder such as `.gitkeep` when an empty directory must be represented in Git.

Also ensure the repository contains:

`docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`

Populate it from the global canonical contract:

installed global `contracts/implementation-state-evidence-v1.md`

Copy the contract verbatim. Do not summarize, reinterpret, or maintain an independently rewritten variant.

If the global canonical contract is unavailable or the project copy cannot be synchronized exactly, return `PROJECT_INIT_BLOCKED` rather than leaving a dangling Stable-v1 reference.

Do not delete existing artifacts.

These directories and the contract hold workflow evidence/design rules; they do not authorize implementation decisions.

## Stage 6 — Configure Project Rules

Review whether project-specific Kilo rules would materially help implementation.

Use:

`.kilo/rules/`

Only create rules that are genuinely relevant.

Do not duplicate information already adequately covered by `AGENTS.md`.

Prefer concise rules containing implementation constraints rather than tutorials.

## Stage 7 — Build the Skill Coverage Matrix

Perform a mandatory skill-coverage review for every major technology and engineering concern in the approved technology baseline.

Do not skip this stage merely because implementation could proceed without additional skills.

At minimum, evaluate the approved project's relevant:

- programming language/runtime
- application framework
- database/storage technology
- cloud provider
- major cloud services
- infrastructure-as-code technology
- testing framework/strategy
- CI/CD platform
- security/dependency tooling
- observability stack
- other specialized technologies that materially affect implementation quality

For every applicable technology or concern, create one Skill Coverage Matrix row.

Use exactly one status:

- `ALREADY_AVAILABLE` — a suitable approved skill is already available to the project or globally
- `INSTALL_RECOMMENDED` — a suitable external skill exists and would materially improve implementation quality, but requires explicit user approval before installation
- `CUSTOM_SKILL_REQUIRED` — no suitable reusable skill exists and project-specific guidance is important enough to justify a focused custom skill
- `NOT_REQUIRED` — a skill would not materially improve this project beyond `AGENTS.md`, project rules, architecture, ADRs, and normal model capability

Each matrix row must include:

- technology / concern
- status
- selected skill name when applicable
- source/location when applicable
- why the skill is or is not needed
- whether user approval is required
- important security/maintenance considerations when applicable

Example shape:

| Technology / Concern | Status | Skill | Source / Location | Why | Approval |
| --- | --- | --- | --- | --- | --- |
| .NET 10 / ASP.NET Core | ALREADY_AVAILABLE | dotnet-production | global | Production .NET implementation guidance | No |
| AWS Lambda | INSTALL_RECOMMENDED | aws-serverless | reviewed external source | Specialized Lambda/IAM/retry guidance | Yes |
| Project event envelope | CUSTOM_SKILL_REQUIRED | project-event-contracts | .kilo/skills/ | Repository-specific contract rules | No external install |
| Simple JSON serialization | NOT_REQUIRED | — | — | Existing project guidance is sufficient | No |

Skills are a curated dependency layer.

Do not create or install skills merely to increase available context.

For every proposed non-`NOT_REQUIRED` skill ask:

- Is the technology actually used by this project?
- Will this skill materially improve implementation quality?
- Is the guidance specialized enough to justify a skill?
- Is equivalent guidance already present in `AGENTS.md` or project rules?
- Is the source trustworthy?
- Is the skill narrow enough to avoid unnecessary context or conflicting instructions?

The matrix is an explicit completeness check, not a requirement to maximize the number of skills.

Global workflow skills such as requirements grilling, TDD, diagnosis, and adversarial checking should normally be reported as `ALREADY_AVAILABLE` when relevant. Do not copy them into the project merely to make them visible.

A project may legitimately have many `NOT_REQUIRED` rows when normal project instructions are sufficient.

## Stage 8 — Search Existing Skills Before Creating New Ones

Prefer existing high-quality skills over generating a new generic skill from scratch.

Use this source priority:

1. official/vendor-maintained skill
2. well-established and actively maintained community skill
3. project-adapted version of a reputable skill
4. custom project-specific skill only when necessary

Potential discovery sources include:

- skills.sh
- official technology-vendor skill repositories
- reputable open-source Agent Skill collections

Treat third-party skills as untrusted until reviewed.

Before recommending installation, evaluate:

- repository owner/maintainer
- whether the source is official
- maintenance activity
- relevance to the approved stack
- scope of instructions
- bundled scripts or executable resources
- unexpected network or shell behavior
- overlap with existing project instructions

Do not silently install third-party skills.

## Stage 9 — Skill Approval Gate

When useful third-party skills are found:

- do not install them automatically
- present the recommended skill set to the user
- mark each unapproved third-party skill as `RECOMMENDED_NOT_INSTALLED`
- continue repository initialization unless the approved architecture explicitly makes that skill a required project dependency

For each recommendation provide:

- skill name
- source
- purpose
- why it is useful for this project
- whether it is official/vendor maintained
- relevant security or maintenance concern
- proposed project installation location

A third-party skill recommendation is normally non-blocking.

## Stage 10 — Install Approved Skills

Install a third-party skill only after explicit user approval.

If approval has not been given, leave it uninstalled and report it as `RECOMMENDED_NOT_INSTALLED`.

Prefer:

`.kilo/skills/<skill-name>/SKILL.md`

Keep the number of installed skills small and relevant.

Do not install large skill collections when only one or two skills are required.

## Stage 11 — Create Missing Project-Specific Skills

If no suitable external skill exists for an important project-specific need, create a focused project skill.

Do not duplicate entire vendor documentation.

Do not create a generic technology tutorial.

## Stage 12 — Validate Repository Initialization

Before declaring project initialization complete, verify:

- the technology stack comes from approved architecture/ADRs
- no major technology was invented during initialization
- `AGENTS.md` contains the actual project stack
- `AGENTS.md` contains valid build/test commands where available
- `AGENTS.md` contains executable approved security commands when architecture requires them
- required security verification capabilities are not silently omitted
- standard workflow artifact directories exist, including `docs/verification/waivers/`, `docs/verification/smoke/`, `docs/reviews/`, and `docs/workflow/`
- `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md` exists and is synchronized verbatim with the global canonical contract
- `README.md` accurately describes the project
- README does not claim unimplemented functionality
- project rules are relevant and non-duplicative
- the Skill Coverage Matrix includes every major approved technology and engineering concern that could materially benefit from specialized guidance
- every matrix row has exactly one allowed status: `ALREADY_AVAILABLE`, `INSTALL_RECOMMENDED`, `CUSTOM_SKILL_REQUIRED`, or `NOT_REQUIRED`
- every `INSTALL_RECOMMENDED` row identifies a reviewed source and remains uninstalled unless explicitly approved
- every `CUSTOM_SKILL_REQUIRED` row has either produced a focused project skill or is explicitly reported as unfinished
- installed skills are relevant to the approved stack
- third-party skills were explicitly approved
- no secrets were introduced
- implementation agents now have sufficient project context

## Blocked Output Contract

Whenever this workflow cannot safely continue, the blocked response must contain these fields:

### Blocking issue

State exactly what is missing, conflicting, unsafe, or unresolved.

### Owner

Use exactly one of:

- `PRODUCT`
- `ARCHITECTURE`
- `PROJECT_INIT`
- `SPECIFICATION`
- `REPOSITORY`
- `USER_APPROVAL`

Choose the owner that must resolve the blocker.

### Why it blocks

Explain why this stage cannot safely continue without the decision or correction.

### Required action

State the minimum action, clarification, or correction required to unblock the workflow.

### Next command

State the exact next workflow command to run after the blocker is resolved.

Use only one of:

- `/prd`
- `/architect`
- `/project-init`
- `/spec`
- `/implement`

If a user clarification or repository cleanup must happen first, say so in `Required action`, then name the command to rerun in `Next command`.

The final line must be the workflow's blocked status token and nothing may appear after it.

## Output

Report concisely:

### Technology Baseline

- language/runtime
- framework
- database/storage
- cloud
- IaC
- testing stack

### Files Updated

List:

- `AGENTS.md`
- `README.md`
- `docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md`
- relevant `.kilo/rules/*`
- relevant `.kilo/skills/*`

### Skill Coverage Matrix

Report the complete matrix for every evaluated major technology / concern.

Use only these statuses:

- `ALREADY_AVAILABLE`
- `INSTALL_RECOMMENDED`
- `CUSTOM_SKILL_REQUIRED`
- `NOT_REQUIRED`

For `INSTALL_RECOMMENDED`, clearly mark:

- source
- why it is useful
- whether it is official/vendor maintained
- security/maintenance concerns
- proposed installation path
- `Approval required: YES`

Do not treat an unapproved recommendation as installed.

### Skills

Summarize resulting skill actions:

- installed
- already available
- custom-created
- recommended but not installed
- declined
- not required

### Remaining Decisions

List unresolved non-blocking decisions.

If a blocking technology decision is unresolved, use the Blocked Output Contract.

Routing rules:

- use owner `ARCHITECTURE` and next command `/architect` when the approved architecture or ADRs are missing or conflict on a required technology decision
- use owner `PROJECT_INIT` and next command `/project-init` when the blocker is local repository initialization state that this workflow can safely resolve after a user/repository action
- use owner `USER_APPROVAL` and next command `/project-init` when explicit approval is required for a project-initialization action

Do not proceed to `/spec` or `/implement`.

Finish with exactly:

`PROJECT_INIT_BLOCKED`

If initialization is successful, finish with exactly:

`PROJECT_INIT_READY`

Do not output anything after the final status token.
