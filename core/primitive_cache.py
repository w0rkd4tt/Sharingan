"""Unified Primitive Cache — single store for web + whitebox findings."""
import json
import hashlib
import os
import time
from typing import Optional


PRIMITIVE_CLASSES = frozenset([
    "file_read", "file_write", "secret_read", "ssrf", "sqli", "rce",
    "deser", "idor_read", "idor_write", "stored_xss", "auth_bypass",
    "race_condition", "path_traversal", "open_redirect",
])


class PrimitiveCache:
    def __init__(self, target_dir: str):
        self.cache_dir = os.path.join(target_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.prims_file = os.path.join(self.cache_dir, "primitives.jsonl")
        self.chains_file = os.path.join(self.cache_dir, "chains.jsonl")
        self._index = {}
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.prims_file):
            with open(self.prims_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    p = json.loads(line)
                    key = f"{p.get('path_line', '')}:{p.get('class', '')}"
                    self._index[key] = p["id"]

    def _make_id(self, path_line: str, prim_class: str) -> str:
        h = hashlib.sha256(f"{path_line}:{prim_class}".encode()).hexdigest()[:12]
        return f"prim_{h}"

    def is_duplicate(self, path_line: str, prim_class: str) -> bool:
        return f"{path_line}:{prim_class}" in self._index

    def write_primitive(self, primitive: dict) -> Optional[str]:
        """Write a primitive to cache. Returns prim_id or None if duplicate."""
        pclass = primitive.get("class", "")
        if pclass not in PRIMITIVE_CLASSES:
            raise ValueError(
                f"Unknown primitive class: {pclass}. Must be one of {PRIMITIVE_CLASSES}"
            )

        path_line = primitive.get("path_line", "")
        if self.is_duplicate(path_line, pclass):
            return None

        prim_id = self._make_id(path_line, pclass)
        primitive["id"] = prim_id
        primitive.setdefault(
            "timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        primitive.setdefault("evidence_label", "ASSUMED")
        primitive.setdefault("confidence", {"M": False, "D": False, "E": False})
        primitive.setdefault("oracle_ran", False)
        primitive.setdefault("chains_to", [])
        primitive.setdefault("chained_from", [])
        primitive.setdefault("cross_flow_ref", None)

        with open(self.prims_file, "a") as f:
            f.write(json.dumps(primitive, ensure_ascii=False) + "\n")

        self._index[f"{path_line}:{pclass}"] = prim_id
        return prim_id

    def read_all(self, flow: Optional[str] = None) -> list:
        """Read all primitives, optionally filtered by flow (web|src)."""
        results = []
        if not os.path.exists(self.prims_file):
            return results
        with open(self.prims_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                p = json.loads(line)
                if flow and p.get("flow") != flow:
                    continue
                results.append(p)
        return results

    def read_by_class(self, prim_class: str) -> list:
        return [p for p in self.read_all() if p.get("class") == prim_class]

    def find_chain_candidates(self) -> list:
        """Find viable chain candidates across flows with constraint-aware matching."""
        all_prims = self.read_all()
        by_class: dict[str, list] = {}
        for p in all_prims:
            by_class.setdefault(p.get("class", ""), []).append(p)

        candidates = []
        for p in all_prims:
            for target_class in p.get("chains_to", []):
                if target_class not in by_class:
                    continue
                for target in by_class[target_class]:
                    if target["id"] == p["id"]:
                        continue
                    if not p.get("oracle_ran") or not target.get("oracle_ran"):
                        continue

                    is_cross_flow = p.get("flow") != target.get("flow")
                    auth_map = {"none": 0, "user": 1, "admin": 2}
                    auth = max(
                        auth_map.get(p.get("auth", "none"), 0),
                        auth_map.get(target.get("auth", "none"), 0),
                    )
                    severity_map = {
                        "rce": 4, "sqli": 3, "secret_read": 3, "auth_bypass": 3,
                        "file_write": 3, "deser": 3, "ssrf": 2, "file_read": 2,
                        "idor_write": 2, "stored_xss": 2, "idor_read": 1,
                        "race_condition": 1, "path_traversal": 2, "open_redirect": 1,
                    }
                    sev = severity_map.get(target_class, 1)
                    constraints = sum(
                        1 for x in [p.get("constraint"), target.get("constraint")] if x
                    )
                    auth_inv = {0: 4, 1: 2, 2: 1}.get(auth, 1)
                    priority = sev * (1 / max(constraints, 1)) * auth_inv

                    candidates.append({
                        "source": p["id"],
                        "target": target["id"],
                        "source_class": p["class"],
                        "target_class": target["class"],
                        "cross_flow": is_cross_flow,
                        "priority": round(priority, 2),
                        "auth_required": ["none", "user", "admin"][auth],
                    })

        candidates.sort(key=lambda c: c["priority"], reverse=True)
        return candidates

    def write_chain(self, chain: dict):
        chain.setdefault(
            "timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        with open(self.chains_file, "a") as f:
            f.write(json.dumps(chain, ensure_ascii=False) + "\n")

    def read_chains(self) -> list:
        results = []
        if not os.path.exists(self.chains_file):
            return results
        with open(self.chains_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    results.append(json.loads(line))
        return results

    def stats(self) -> dict:
        all_p = self.read_all()
        web = [p for p in all_p if p.get("flow") == "web"]
        src = [p for p in all_p if p.get("flow") == "src"]
        oracle_ok = [p for p in all_p if p.get("oracle_ran")]
        classes_set = set(p.get("class", "") for p in all_p)
        return {
            "total": len(all_p),
            "web": len(web),
            "src": len(src),
            "oracle_confirmed": len(oracle_ok),
            "chains": len(self.read_chains()),
            "classes": dict(sorted(
                {c: len([p for p in all_p if p.get("class") == c]) for c in classes_set}.items()
            )),
        }
