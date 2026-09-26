#!/usr/bin/env python3
"""kilo_graph — read-only, deterministic multi-hop queries over Kilo LARGE artifacts (V0.2.1 §6).

Python 3 standard library only. Never writes. Reads front matter from the current
working tree (uncommitted changes included). Authority stays in Markdown/Git; this
is a calculator, not a store.

  kilo_graph.py closure <ROOT-ID>   candidate closure for /reconcile (§3.3 step 2)
  kilo_graph.py cycles              depends_on cycles (§4.5)
  kilo_graph.py integrity           duplicate IDs, identity mismatch, dangling refs,
                                    PENDING owner problems, Case A/B lifecycle (§8.6)
  kilo_graph.py order               advisory canonical order (§8.6)
  kilo_graph.py owed <OWNER-ID>     PENDING entries owed by an owner (§2.3)
"""
import os, re, sys, json

ART_DIRS = ["docs/project", "docs/epics", "docs/features", "docs/specs"]
CANON = re.compile(r"^(PROJECT|EPIC|FEATURE|SPEC)-[0-9]{3,}$")
READY = {"FEATURE": "READY_FOR_SPEC", "EPIC": "READY_FOR_FEATURE_DECOMPOSITION"}

def listv(v):
    v = (v or "[]").strip()
    if not (v.startswith("[") and v.endswith("]")):
        return None
    v = v[1:-1]
    return [x.strip() for x in re.split(r",\s*(?![^{]*})", v) if x.strip()] if v else []

def load(root="."):
    arts, problems = {}, []
    for d in ART_DIRS:
        p = os.path.join(root, d)
        if not os.path.isdir(p):
            continue
        for fn in sorted(os.listdir(p)):
            if not fn.endswith(".md"):
                continue
            with open(os.path.join(p, fn), encoding="utf-8") as f:
                lines = f.read().split("\n")
            kv = {}
            if lines and lines[0] == "---":
                for ln in lines[1:]:
                    if ln == "---":
                        break
                    k, _, v = ln.partition(": ")
                    kv[k] = v
            aid = kv.get("id")
            if not aid or not CANON.match(aid):
                problems.append({"code": "AUTHORITATIVE_ARTIFACT_INVALID", "file": f"{d}/{fn}"}); continue
            if fn[:-3] != aid:
                problems.append({"code": "ARTIFACT_IDENTITY_MISMATCH", "file": f"{d}/{fn}", "id": aid})
            kv["_file"] = f"{d}/{fn}"
            arts.setdefault(aid, []).append(kv)
    for aid, v in arts.items():
        if len(v) > 1:
            problems.append({"code": "DUPLICATE_ARTIFACT_ID", "id": aid, "files": [x["_file"] for x in v]})
    return arts, problems

class G:
    def __init__(self, root="."):
        self.arts, self.problems = load(root)
        self.A = {i: v[0] for i, v in self.arts.items() if len(v) == 1}
        self.dep, self.pend, self.gov, self.exm, self.par, self.kids = {}, {}, {}, {}, {}, {}
        for i, kv in self.A.items():
            d = listv(kv.get("depends_on")); g = listv(kv.get("governed_by"))
            if d is None or g is None:
                self.problems.append({"code": "AUTHORITATIVE_ARTIFACT_INVALID", "id": i, "reason": "list not single-line flow style"}); d, g = d or [], g or []
            self.dep[i] = [x.split("#")[0] for x in d if not x.startswith("PENDING:")]
            self.pend[i] = [x for x in d if x.startswith("PENDING:")]
            self.gov[i] = g
            self.exm[i] = re.findall(r"authority: (\S+?),", kv.get("exemptions", ""))
            self.par[i] = kv.get("parent_id")
            self.kids.setdefault(self.par[i], []).append(i)

    def rdep(self, n): return [i for i, ds in self.dep.items() if n in ds]
    def rgov(self, n): return [i for i, gs in self.gov.items() if n in gs]
    def children(self, n): return self.kids.get(n, [])

    def gov_cover(self, auth):
        direct, out, stack = set(self.rgov(auth)), set(), list(self.rgov(auth))
        while stack:
            x = stack.pop()
            if x in out or (auth in self.exm.get(x, []) and x not in direct):
                continue
            out.add(x); stack += self.children(x)
        return out

    def closure(self, root):
        """Fail closed: if traversal reaches an ID that is duplicated (or otherwise not
        uniquely resolvable), the closure is incomplete and is reported as blocked."""
        dups = {i for i, v in self.arts.items() if len(v) > 1}
        # edges from duplicated files are unknowable; still detect when they are reached
        dup_refs = {i: [d for d in dups if d in ds] for i, ds in self.dep.items()}
        seen, stack, blocked = set(), [root], set()
        while stack:
            n = stack.pop()
            nxt = set(self.rdep(n)) | set(self.children(n))
            if not CANON.match(n):  # non-artifact authority (ADR/PRD/ARCH): governance coverage
                nxt |= self.gov_cover(n)
            for d in dups:  # a duplicate child/dependent of n is reached but cannot be expanded
                kv_par = {x.get("parent_id") for x in self.arts[d]}
                kv_dep = {y.split("#")[0] for x in self.arts[d] for y in (listv(x.get("depends_on")) or [])}
                if n in kv_par or n in kv_dep:
                    blocked.add(d)
            for x in nxt - seen - {root}:
                seen.add(x); stack.append(x)
        return {"closure": sorted(seen),
                "blocked": [{"code": "DUPLICATE_ARTIFACT_ID", "id": d} for d in sorted(blocked)]}

    def cycles(self):
        idx, low, onst, st, out, c = {}, {}, set(), [], [], [0]
        sys.setrecursionlimit(10000)
        def sc(v):
            idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); onst.add(v)
            for w in self.dep.get(v, []):
                if w not in self.A: continue
                if w not in idx: sc(w); low[v] = min(low[v], low[w])
                elif w in onst: low[v] = min(low[v], idx[w])
            if low[v] == idx[v]:
                comp = []
                while True:
                    w = st.pop(); onst.discard(w); comp.append(w)
                    if w == v: break
                if len(comp) > 1 or v in self.dep.get(v, []):
                    out.append(sorted(comp))
        for v in sorted(self.A):
            if v not in idx: sc(v)
        return out

    def integrity(self):
        p = list(self.problems)
        for i, ds in self.dep.items():
            for t in ds:
                if CANON.match(t) and t not in self.arts:
                    p.append({"code": "DANGLING_REFERENCE", "id": i, "target": t})
            for e in self.pend[i]:
                owner = e.split(":")[1]
                if owner not in self.A or self.A[owner].get("state") == "RETIRED":
                    p.append({"code": "PENDING_OWNER_INVALID", "id": i, "entry": e})
        for i, kv in self.A.items():
            t, s = kv.get("type"), kv.get("state")
            if t in READY:
                if s == READY[t] and self.children(i):
                    p.append({"code": "LIFECYCLE_CASE_A", "id": i, "note": "READY parent has durable child"})
                if s == "ACTIVE" and not self.children(i):
                    p.append({"code": "LIFECYCLE_INTEGRITY_FAILURE", "id": i, "note": "ACTIVE parent has no child"})
        for c in self.cycles():
            p.append({"code": "DEPENDENCY_CYCLE", "members": c})
        return p

    def order(self):
        done, out, cyc = set(), [], {m for c in self.cycles() for m in c}
        def visit(n):
            if n in done or n in cyc: return
            done.add(n)
            for d in sorted(self.dep.get(n, [])):
                if d in self.A: visit(d)
            if self.par.get(n) in self.A: visit(self.par[n])
            out.append(n)
        for n in sorted(self.A): visit(n)
        return {"order": out, "excluded_in_cycles": sorted(cyc)}

    def owed(self, owner):
        return [{"consumer": i, "entry": e} for i, es in self.pend.items() for e in es if e.split(":")[1] == owner]

def main(argv):
    g = G(".")
    cmd = argv[1] if len(argv) > 1 else ""
    if cmd == "closure": r = g.closure(argv[2])
    elif cmd == "cycles": r = g.cycles()
    elif cmd == "integrity": r = g.integrity()
    elif cmd == "order": r = g.order()
    elif cmd == "owed": r = g.owed(argv[2])
    else:
        print(__doc__); return 2
    print(json.dumps(r, separators=(",", ":")))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
