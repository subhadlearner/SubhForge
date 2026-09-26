# Implementation-State Evidence Contract v1

This contract defines the canonical repository-content identity used by `/verify`, `/review`, and `/waive`.

The goal is to prove that review and waiver decisions apply to the exact non-evidence repository contents that were deterministically verified, without requiring those contents to be committed first.

## Authority

The **canonical implementation-state manifest** is the authoritative freshness evidence.

The **implementation-state fingerprint** is a compact checksum/identifier of that canonical manifest. A matching fingerprint alone is never sufficient when the canonical manifest is available. Freshness decisions are made from exact canonical-manifest equality.

## Verification Base

Every verification report records:

- current branch
- verification base HEAD SHA captured before checks run
- canonical pre-check implementation-state manifest
- implementation-state fingerprint
- canonical post-check manifest comparison result

The base HEAD is provenance and the reconstruction anchor. Commit identity alone is not implementation-state identity.

## Included Paths

Build the manifest from the union of:

1. tracked paths whose effective current contents differ from the recorded verification base HEAD
2. untracked, non-ignored paths

A deleted tracked path is included with state `DELETED`.

Git-ignored paths are intentionally outside implementation-state identity.

## Workflow Evidence Exclusion Set

Exclude **only** these workflow evidence paths from implementation-state identity:

- `docs/verification/**`
- `docs/reviews/**`
- `docs/diagnostics/**`

This exclusion set is normative for Contract v1. `/verify`, `/review`, and `/waive` must not independently add exclusions.

In particular, these remain identity-bearing when changed:

- `docs/specs/**`
- `docs/architecture/**`
- `docs/adr/**`
- project/global instruction files such as `AGENTS.md`
- `.kilo/**`
- source and tests
- build/package/project configuration
- dependency manifests and lockfiles
- CI/IaC configuration

## Per-Path State

For each included path record:

- repository-relative path using `/` as separator
- current effective Git mode/type
- current Git blob/content hash produced with read-only `git hash-object --no-filters`, or the literal `DELETED`

Canonical Git mode/type values are:

- `100644` — regular non-executable file
- `100755` — regular executable file
- `120000` — symbolic link
- `160000` — gitlink/submodule
- `DELETED` — tracked path absent from the effective current state

For tracked paths, determine effective mode/type from read-only Git index/diff evidence such as `git ls-files --stage` and `git diff --raw`, accounting for unstaged mode-only changes.

For untracked, non-ignored paths, determine the Git-compatible mode/type that Git would record for the current filesystem object. If regular executable state, symlink state, embedded-repository/gitlink state, or any other relevant mode/type cannot be determined reliably on the current platform, reconstruction is `UNRECONSTRUCTABLE`; do not guess.

Mode/type is part of implementation identity. A content-identical change from `100644` to `100755`, or file ↔ symlink/gitlink, is a different implementation state.

Do not use timestamps, file size, working-tree mtime, branch name, or commit SHA as per-path identity.

## Canonical Manifest Serialization

Serialize each entry exactly as:

`<repository-relative-path><TAB><git-mode-or-DELETED><TAB><git-blob-hash-or-DELETED><LF>`

For a deleted path, serialize:

`<repository-relative-path><TAB>DELETED<TAB>DELETED<LF>`

Rules:

- paths are repository-relative
- path separator is `/`
- preserve path case
- one entry per path
- exactly two TAB (U+0009) field separators per record
- LF (U+000A) is the only record terminator
- no CR characters
- UTF-8 encoding
- no BOM
- no blank records
- no duplicate paths
- entries sorted ascending by the UTF-8 byte sequence of the repository-relative path
- an empty manifest is valid and is represented by zero bytes

For Contract v1, a repository path containing TAB, CR, or LF cannot be represented canonically. If such a path participates in implementation-state identity, reconstruction is `UNRECONSTRUCTABLE` and reusable review/waiver evidence must fail closed.

## Fingerprint

The implementation-state fingerprint is the Git blob object ID of the exact canonical manifest bytes, computed using read-only:

`git hash-object --stdin`

Persist it as:

`GIT_BLOB_OID:<object-id>`

The repository's Git object format determines the object-ID algorithm. This is acceptable because the fingerprint is a compact identifier within the same repository; **exact canonical-manifest equality remains the authoritative freshness test**.

Never use the fingerprint as a substitute for persisting the full canonical manifest.

## Freshness Outcomes

Reconstruction has exactly three outcomes:

### MATCH

Return `MATCH` only when:

- scope/specification matches
- branch matches
- the verification base HEAD is available
- the current canonical manifest can be reconstructed under this contract
- the reconstructed manifest is byte-for-byte identical to the persisted canonical manifest

A later commit of those exact verified contents does not invalidate `MATCH`.

### MISMATCH

Return `MISMATCH` when reconstruction succeeds but the canonical manifests differ.

This means verification evidence is stale for the current implementation state.

### UNRECONSTRUCTABLE

Return `UNRECONSTRUCTABLE` when freshness cannot be proven reliably, including when:

- recorded base HEAD is unavailable
- required Git inspection fails
- required report fields are missing or malformed
- manifest records are malformed or duplicated
- an identity-bearing path contains TAB, CR, or LF
- effective Git mode/type cannot be determined reliably
- current repository state cannot be determined reliably

`MISMATCH` and `UNRECONSTRUCTABLE` both fail closed and require a fresh `/verify` before review or waiver use.

## Required Verification Evidence Schema

A reusable verification report must contain:

- verification ID
- specification/change identity
- branch
- verification base HEAD SHA
- Contract version: `implementation-state-evidence-v1`
- canonical implementation-state manifest
- implementation-state fingerprint
- pre-check/post-check manifest equality result
- factual verification result: `DONE` or `NOT_DONE`
- effective delivery gate
- commands/checks executed with outcomes
- materially relevant verification-environment facts when applicable

A report missing any required field is not reusable evidence and freshness is `UNRECONSTRUCTABLE`.

## Verification Environment Boundary

Implementation-state freshness proves repository-content identity. It does **not** prove that the execution environment is identical.

Git-ignored files, credentials, external services, mutable databases, OS/runtime versions, SDK/tool versions, and environment variables may affect verification without being part of the implementation-state manifest.

When materially relevant to a check, the verification report must record concise environment assumptions/evidence, for example:

- runtime/SDK version
- integration-test profile
- external emulator/service version
- required externally supplied configuration
- relevant mutable dependency assumptions

Do not dump secrets or entire environments.

A changed environment does not automatically make repository evidence stale, but reviewers must treat materially incompatible or missing environment evidence as a verification/review concern.

## Waiver Binding

A waiver is logically bound to:

- exact verification report
- canonical implementation-state manifest from that report
- implementation-state fingerprint
- exact accepted failure set
- expiry
- human-authorized justification and residual-risk acceptance

The waiver does not need to duplicate the full manifest if it references the immutable verification report, but `/waive` and `/review` must establish current `MATCH` against that report before the waiver can establish `CLEAR_WITH_EXCEPTION`.

A later commit of identical contents does not invalidate the waiver. `MISMATCH` or `UNRECONSTRUCTABLE` does.

## Fail-Closed Rule

When evidence is missing, malformed, ambiguous, or cannot be reconstructed reliably:

- do not infer freshness from HEAD
- do not select a different report merely because it is newer
- do not continue review or waiver use
- require a fresh `/verify`

This contract controls implementation-state freshness for Stable v1.
