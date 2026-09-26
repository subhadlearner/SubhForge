#!/usr/bin/env python3
"""TODO-2 POC: generate a deterministic synthetic LARGE-project fixture.

Usage: gen_fixture.py <out_dir> <scale>   (scale 1 = 8 Epics / 50 Features / 200 Specs)

Front matter follows V0.2.1 §2.2 with single-line flow-style lists.
Bodies contain prose that mentions other IDs (grep noise), and records
(REC/VERIFY/applicability/ESC/BLK) reference artifacts, as a real project would.
Seeded anomalies: one cycle, one dangling ref, one duplicate ID, lifecycle
Case A and Case B, one PENDING entry whose owner is missing.
"""
import os, random, sys, subprocess

out, scale = sys.argv[1], int(sys.argv[2])
rng = random.Random(42 * scale)
N_EPIC, N_FEAT, N_SPEC, N_ADR = 8 * scale, 50 * scale, 200 * scale, 20 * scale
TS = "2026-09-26T10:00:00+05:30"
WORDS = ("order checkout ledger portfolio import retry idempotent contract boundary "
         "latency cache schema migration token auth audit export report user nav").split()

def prose(n_words, ids):
    w = [rng.choice(WORDS) for _ in range(n_words)]
    for i in range(0, n_words, 90):  # sprinkle ID mentions as noise
        w.insert(i, f"(see {rng.choice(ids)})")
    return " ".join(w)

def fm(**kv):
    lines = ["---"]
    for k in ("id", "type", "title", "state", "created_at", "updated_at",
              "parent_id", "resume_state", "depends_on", "governed_by", "exemptions"):
        if k in kv:
            v = kv[k]
            if isinstance(v, list):
                v = "[" + ", ".join(v) + "]"
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)

def write(rel, text):
    p = os.path.join(out, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text + "\n")

epics = [f"EPIC-{i:03d}" for i in range(1, N_EPIC + 1)]
feats = [f"FEATURE-{i:03d}" for i in range(1, N_FEAT + 1)]
specs = [f"SPEC-{i:03d}" for i in range(1, N_SPEC + 1)]
adrs = [f"ADR-{i:03d}" for i in range(1, N_ADR + 1)]
all_ids = epics + feats + specs + adrs

feat_parent = {f: epics[i * N_EPIC // N_FEAT] for i, f in enumerate(feats)}
spec_parent = {s: feats[i * N_FEAT // N_SPEC] for i, s in enumerate(specs)}

# --- Project, PRD, ADRs
write("docs/project/PROJECT-001.md", fm(id="PROJECT-001", type="PROJECT", title="Synthetic",
      state="ACTIVE", created_at=TS, updated_at=TS, parent_id="null", resume_state="null",
      depends_on=[], governed_by=[]) + "\n\n" + prose(800, all_ids))
write("docs/prd/PRD-001.md", "# PRD-001\n" + "\n".join(f"- FR-{i}: {prose(30, all_ids)}" for i in range(1, 81 * scale)))
for a in adrs:
    write(f"docs/adr/{a}.md", f"# {a}\n\n" + prose(400, all_ids))

# --- Epics
for e in epics:
    gov = rng.sample(adrs, rng.randint(0, 2))
    write(f"docs/epics/{e}.md", fm(id=e, type="EPIC", title=f"Epic {e}", state="ACTIVE",
          created_at=TS, updated_at=TS, parent_id="PROJECT-001", depends_on=[], governed_by=gov)
          + "\n\n" + prose(1500, all_ids))

# --- Features
for i, f in enumerate(feats):
    deps = [d for d in rng.sample(feats[:i], min(i, rng.choice([0, 0, 0, 1, 2])))]
    gov = rng.sample(adrs, rng.choice([0, 0, 1]))
    write(f"docs/features/{f}.md", fm(id=f, type="FEATURE", title=f"Feature {f}", state="ACTIVE",
          created_at=TS, updated_at=TS, parent_id=feat_parent[f], depends_on=deps, governed_by=gov)
          + "\n\n## Provided Contracts\n### Contract" + f[-3:] + "\n" + prose(1200, all_ids))

# --- Specs
for i, s in enumerate(specs):
    same = [x for x in specs[:i] if spec_parent[x] == spec_parent[s]]
    other = [x for x in specs[:i] if spec_parent[x] != spec_parent[s]]
    deps = []
    for _ in range(rng.choice([0, 1, 1, 2, 3])):
        pool = same if (same and rng.random() < 0.7) else other
        if pool:
            t = rng.choice(pool)
            deps.append(f"{t}#Contract{t[-3:]}")
    deps = sorted(set(deps))
    if rng.random() < 0.04:
        owner = rng.choice(feats)
        deps.append(f"PENDING:{owner}:NewContract{i}")
    gov = rng.sample(adrs, rng.choice([0, 0, 0, 1]))
    kv = dict(id=s, type="SPEC", title=f"Spec {s}", state="READY_FOR_IMPLEMENTATION",
              created_at=TS, updated_at=TS, parent_id=spec_parent[s], depends_on=deps, governed_by=gov)
    if rng.random() < 0.03:
        kv["exemptions"] = [f"{{authority: {rng.choice(adrs)}, authorized_by: {rng.choice(adrs)}}}"]
    write(f"docs/specs/{s}.md", fm(**kv) + "\n\n## Contract" + s[-3:] + "\n" + prose(1500, all_ids))

# --- Records that mention artifacts (noise for naive grep, signal for record lookup)
for r in range(1, 6 * scale + 1):
    refs = rng.sample(specs + feats, 25)
    body = "\n".join(f"| {x} | {rng.choice(['UNCHANGED','REVISED','DECISION_REQUIRED'])} | reason |" for x in refs)
    obls = "\n".join(f"| OBL-{k:03d} | REVERIFY | {rng.choice(refs)} | {rng.choice(['OPEN','RESOLVED'])} |" for k in range(1, 6))
    write(f"docs/workflow/reconciliation/REC-{r:03d}.md",
          f"---\nid: REC-{r:03d}\ntype: RECONCILIATION\nstate: OPEN\n---\n## Closure\n{', '.join(refs)}\n## Dispositions\n{body}\n## Obligations\n{obls}")
for s in specs:
    for k in range(1, rng.choice([1, 2, 3]) + 1):
        write(f"docs/verification/VERIFY-{s}-{k:03d}.md", f"# VERIFY-{s}-{k:03d}\nTarget: {s}\n" + prose(300, [s]))
        write(f"docs/verification/applicability/VERIFY-{s}-{k:03d}.md",
              "\n".join(f"({s}, AC-{a}) -> APPLICABLE" for a in range(1, 5)))
for k in range(1, 4 * scale + 1):
    write(f"docs/workflow/escalations/ESC-{k:03d}.md", f"---\nid: ESC-{k:03d}\nstatus: OPEN\n---\nOrigin: {rng.choice(specs)}")
    write(f"docs/workflow/blockers/BLK-{k:03d}.md", f"---\nid: BLK-{k:03d}\nstatus: OPEN\n---\nAffected: {rng.choice(feats)}")

# --- Seeded anomalies
def patch(rel, old, new):
    p = os.path.join(out, rel); t = open(p).read().replace(old, new, 1); open(p, "w").write(t)
a, b = specs[150 * scale - 1], specs[151 * scale - 1]
patch(f"docs/specs/{a}.md", "depends_on: [", f"depends_on: [{b}#Contract{b[-3:]}, ")  # cycle a<->b (b already may depend on a)
patch(f"docs/specs/{b}.md", "depends_on: [", f"depends_on: [{a}#Contract{a[-3:]}, ")
patch(f"docs/specs/{specs[10]}.md", "depends_on: [", "depends_on: [SPEC-9999#Nope, ")       # dangling
dup = open(os.path.join(out, f"docs/specs/{specs[76]}.md")).read()
write(f"docs/specs/{specs[76]}-copy.md", dup.rstrip("\n"))                                    # duplicate ID
patch(f"docs/features/{feats[5]}.md", "state: ACTIVE", "state: READY_FOR_SPEC")              # Case A (has children)
childless = feats[-1] + "X"
write(f"docs/features/FEATURE-{N_FEAT+1:03d}.md", fm(id=f"FEATURE-{N_FEAT+1:03d}", type="FEATURE",
      title="Case B", state="ACTIVE", created_at=TS, updated_at=TS, parent_id=epics[0],
      depends_on=[], governed_by=[]))                                                          # Case B
patch(f"docs/specs/{specs[20]}.md", "depends_on: [", "depends_on: [PENDING:FEATURE-8888:Ghost, ")  # missing owner

subprocess.run(["git", "init", "-q"], cwd=out, check=True)
subprocess.run(["git", "add", "-A"], cwd=out, check=True)
subprocess.run(["git", "-c", "user.email=poc@x", "-c", "user.name=poc", "commit", "-qm", "fixture"], cwd=out, check=True)
print(f"fixture: {len(epics)} epics, {len(feats)+1} features, {len(specs)+1} spec files, {len(adrs)} ADRs")
