#!/usr/bin/env python3
"""TODO-2 POC: measure Markdown/Git-only lookup and resume against a ground-truth oracle.

Usage: evaluate.py <fixture_dir>

- ORACLE: parses every artifact's front matter directly (ground truth).
- ANCHORED: the procedure an agent would follow with front-matter-anchored `git grep`
  (one call per relationship per node). Answers are derived ONLY from grep stdout,
  so this checks whether the procedure is sufficient; stdout size ≈ model input.
- NAIVE: unanchored `git grep -l <ID>` + reading each hit's front matter.
- SCAN: one grep returning every front-matter line (the input an LLM would need to
  compute cycles/integrity for /status without a helper).
Tokens are estimated as chars/4 (TODO-4 covers exact counts).
"""
import os, re, random, subprocess, sys, time, json, statistics

FX = sys.argv[1]
ART_DIRS = ["docs/project", "docs/epics", "docs/features", "docs/specs"]
CANON = re.compile(r"^(PROJECT|EPIC|FEATURE|SPEC)-[0-9]{3,}$")
calls = {"n": 0, "chars": 0, "ms": 0.0}

def sh(args):
    t = time.perf_counter()
    r = subprocess.run(args, cwd=FX, capture_output=True, text=True)
    calls["n"] += 1; calls["chars"] += len(r.stdout); calls["ms"] += (time.perf_counter() - t) * 1000
    return r.stdout

def reset():
    calls.update(n=0, chars=0, ms=0.0)

def tok(chars):
    return chars // 4

# ---------------- ORACLE ----------------
def parse_fm(path):
    kv = {}
    with open(path) as f:
        lines = f.read().split("\n")
    if lines[0] != "---":
        return None
    for ln in lines[1:]:
        if ln == "---":
            break
        k, _, v = ln.partition(": ")
        kv[k] = v
    return kv

def listv(v):
    v = (v or "[]").strip()[1:-1]
    return [x.strip() for x in re.split(r",\s*(?![^{]*})", v) if x.strip()] if v else []

arts = {}
for d in ART_DIRS:
    for fn in sorted(os.listdir(os.path.join(FX, d))):
        kv = parse_fm(os.path.join(FX, d, fn))
        arts.setdefault(kv["id"], []).append((fn, kv))
dups = {i for i, v in arts.items() if len(v) > 1}
A = {i: v[0][1] for i, v in arts.items()}
dep = {i: [x.split("#")[0] for x in listv(kv.get("depends_on"))] for i, kv in A.items()}
gov = {i: listv(kv.get("governed_by")) for i, kv in A.items()}
exm = {i: re.findall(r"authority: (\S+?),", kv.get("exemptions", "")) for i, kv in A.items()}
par = {i: kv.get("parent_id") for i, kv in A.items()}
kids = {}
for i, p in par.items():
    kids.setdefault(p, []).append(i)

def o_rev_dep(n): return sorted(i for i, ds in dep.items() if n in ds)
def o_rev_gov(n): return sorted(i for i, gs in gov.items() if n in gs)
def o_children(n): return sorted(kids.get(n, []))

def o_gov_cover(auth):
    out, stack = set(), list(o_rev_gov(auth))
    while stack:
        x = stack.pop()
        if auth in exm.get(x, []) and auth not in gov.get(x, []):
            continue
        if x in out: continue
        out.add(x); stack += o_children(x)
    return out

def o_closure(root):
    seen, stack = set(), [root]
    while stack:
        n = stack.pop()
        nxt = set(o_rev_dep(n)) | set(o_children(n)) | (o_gov_cover(n) if n.startswith("ADR-") else set())
        for x in nxt - seen - {root}:
            seen.add(x); stack.append(x)
    return seen

def o_cycles():
    color, cyc = {}, set()
    def dfs(u, path):
        color[u] = 1
        for v in dep.get(u, []):
            if v not in A: continue
            if color.get(v) == 1: cyc.add(tuple(sorted(path[path.index(v):] + [u]) if v in path else (u, v)))
            elif not color.get(v): dfs(v, path + [u])
        color[u] = 2
    for u in A:
        if not color.get(u): dfs(u, [])
    return cyc

# ---------------- ANCHORED grep procedure ----------------
def ids_from(out):
    ids = set()
    for ln in out.splitlines():
        stem = os.path.splitext(os.path.basename(ln.split(":")[0]))[0]
        ids.add(stem)
    return ids

def g_rev_dep(n):  return ids_from(sh(["git", "grep", "-n", "-E", rf"^depends_on: \[.*\b{n}([#,]|\])", "--", *ART_DIRS]))
def g_rev_gov(n):  return ids_from(sh(["git", "grep", "-n", "-E", rf"^governed_by: \[.*\b{n}([,]|\])", "--", *ART_DIRS]))
def g_children(n): return ids_from(sh(["git", "grep", "-n", "-E", rf"^parent_id: {n}$", "--", *ART_DIRS]))
def g_exempt(auth): return ids_from(sh(["git", "grep", "-n", "-E", rf"^exemptions: .*authority: {auth},", "--", *ART_DIRS]))

def g_gov_cover(auth):
    exempt, direct = g_exempt(auth), g_rev_gov(auth)
    out, stack = set(), list(direct)
    while stack:
        x = stack.pop()
        if x in exempt and x not in direct: continue
        if x in out: continue
        out.add(x); stack += g_children(x)
    return out

def g_closure(root):
    seen, stack = set(), [root]
    while stack:
        n = stack.pop()
        nxt = g_rev_dep(n) | g_children(n) | (g_gov_cover(n) if n.startswith("ADR-") else set())
        for x in nxt - seen - {root}:
            seen.add(x); stack.append(x)
    return {x for x in seen if CANON.match(x)}

def naive_rev_dep(n):
    hits = sh(["git", "grep", "-l", "-w", n]).split()
    res = set()
    for h in hits:
        out = sh(["head", "-12", h])
        m = re.search(r"^depends_on: (.*)$", out, re.M)
        if m and re.search(rf"\b{n}([#,]|\])", m.group(1)):
            res.add(os.path.splitext(os.path.basename(h))[0])
    return res

# ---------------- run ----------------
rng = random.Random(7)
good = sorted(i for i in A if i not in dups and CANON.match(i))
specs = [i for i in good if i.startswith("SPEC-")]
feats = [i for i in good if i.startswith("FEATURE-")]
adrs = sorted({g for gs in gov.values() for g in gs})
R = {}

# 1. single reverse-dependency lookup
res = {"anch": [], "naive": [], "ok": 0, "naive_ok": 0}
for n in rng.sample(specs, 40):
    truth = set(o_rev_dep(n)) - dups
    reset(); got = g_rev_dep(n) - dups; res["anch"].append((calls["n"], calls["chars"], calls["ms"])); res["ok"] += got == truth
    reset(); ng = naive_rev_dep(n) - dups; res["naive"].append((calls["n"], calls["chars"], calls["ms"])); res["naive_ok"] += ng == truth
def summ(rows):
    return {"calls_median": statistics.median(r[0] for r in rows), "tokens_median": tok(statistics.median(r[1] for r in rows)),
            "tokens_max": tok(max(r[1] for r in rows)), "ms_median": round(statistics.median(r[2] for r in rows), 1)}
R["reverse_dep_lookup"] = {"samples": 40, "anchored_correct": res["ok"], "naive_correct": res["naive_ok"],
                           "anchored": summ(res["anch"]), "naive": summ(res["naive"])}

# 2. reconciliation closure (spec / feature / ADR roots)
rows, ok, sizes = [], 0, []
roots = rng.sample(specs, 8) + rng.sample(feats, 6) + rng.sample(adrs, 6)
for r in roots:
    truth = o_closure(r) - dups
    reset(); got = g_closure(r) - dups
    ok += got == truth; rows.append((calls["n"], calls["chars"], calls["ms"])); sizes.append(len(truth))
R["closure"] = {"roots": len(roots), "correct": ok, **summ(rows), "calls_max": max(r[0] for r in rows),
                "closure_size_median": statistics.median(sizes), "closure_size_max": max(sizes)}

# 3. /status full scan input (what an LLM would read to find cycles/integrity itself)
reset()
sh(["git", "grep", "-n", "-E", r"^(id|type|state|parent_id|depends_on|governed_by|exemptions): ", "--", *ART_DIRS])
R["status_full_scan"] = {"calls": calls["n"], "tokens": tok(calls["chars"]), "ms": round(calls["ms"], 1),
                         "cycles_in_truth": len(o_cycles()), "duplicate_ids": sorted(dups)}

# 4. resume inputs
fx_feat = rng.choice(feats)
reset()
open_feat = open(os.path.join(FX, "docs/features", fx_feat + ".md")).read(); calls["chars"] += len(open_feat); calls["n"] += 1
g_children(fx_feat)
sh(["git", "grep", "-l", "-w", fx_feat, "--", "docs/workflow"])
sh(["git", "grep", "-n", "-E", rf"PENDING:{fx_feat}:", "--", *ART_DIRS])
R["resume_feature"] = {"target": fx_feat, "calls": calls["n"], "tokens": tok(calls["chars"]), "ms": round(calls["ms"], 1)}

big = max(roots, key=lambda r: len(o_closure(r)))
cl = sorted(o_closure(big))
pkg = "\n".join(["---", "id: REC-900", "type: RECONCILIATION", "state: ASSESSING", "---",
                 "## Delta\nold: ... new: ...", "## Closure", ", ".join(cl), "## Dispositions"] +
                [f"| {x} | UNCHANGED | premise not touched |" for x in cl[: len(cl) // 2]])
R["resume_reconcile"] = {"closure_size": len(cl), "package_tokens": tok(len(pkg)), "calls": 1,
                         "remaining_derivable": True}

print(json.dumps(R, indent=2))

# 5. helper (kilo_graph.py): same closure roots + cycles + integrity, one call each
HELPER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kilo_graph.py")
rows, ok = [], 0
for r in roots:
    truth = o_closure(r) - dups
    reset(); out = json.loads(sh([sys.executable, HELPER, "closure", r]))
    reaches_dup = bool(o_closure(r) & dups)
    if out["blocked"]:
        ok += reaches_dup            # correct = failed closed exactly when truth touches a duplicate
    else:
        ok += (set(out["closure"]) == truth) and not reaches_dup
    rows.append((calls["n"], calls["chars"], calls["ms"]))
reset(); cyc = json.loads(sh([sys.executable, HELPER, "cycles"])); cyc_ms = calls["ms"]
reset(); integ = json.loads(sh([sys.executable, HELPER, "integrity"]))
codes = sorted({p["code"] for p in integ})
R["helper"] = {"closure_correct": ok, "closure": summ(rows), "cycles_found": len(cyc),
               "cycles_match_truth": len(cyc) == len(o_cycles()), "cycles_ms": round(cyc_ms, 1),
               "integrity_tokens": tok(calls["chars"]), "integrity_ms": round(calls["ms"], 1),
               "integrity_codes": codes}
print(json.dumps({"helper": R["helper"]}, indent=2))
