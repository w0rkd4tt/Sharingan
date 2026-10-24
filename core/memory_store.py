"""Memory Store — cross-session persistence for hunt state."""
import json
import os
import time


class MemoryStore:
    def __init__(self, target_dir: str):
        self.store_path = os.path.join(target_dir, "memory_store.json")
        if os.path.exists(self.store_path):
            with open(self.store_path, "r") as f:
                self.state = json.load(f)
        else:
            self.state = {
                "hunt_state": {},
                "family_status": {},
                "hypotheses": [],
                "sessions": [],
            }

    def set_fact(self, key: str, value, label: str = "ASSUMED"):
        """Set a fact with evidence label (READ/INFERRED/ASSUMED)."""
        if label not in ("READ", "INFERRED", "ASSUMED"):
            raise ValueError(f"Invalid label: {label}")
        self.state["hunt_state"][key] = {
            "value": value,
            "label": label,
            "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._save()

    def get_fact(self, key: str):
        entry = self.state["hunt_state"].get(key)
        return entry["value"] if entry else None

    def get_fact_with_label(self, key: str):
        return self.state["hunt_state"].get(key)

    def set_family_status(self, family: str, status: str):
        if status not in ("open", "hunting", "closed", "residual"):
            raise ValueError(f"Invalid status: {status}")
        self.state["family_status"][family] = {
            "status": status,
            "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._save()

    def get_family_status(self, family: str) -> str:
        entry = self.state["family_status"].get(family)
        return entry["status"] if entry else "open"

    def get_open_families(self) -> list:
        return [
            f for f, e in self.state["family_status"].items()
            if e["status"] in ("open", "hunting", "residual")
        ]

    def add_hypothesis(
        self, hypothesis: str, evidence_against: str, session: str, loop: int
    ):
        self.state["hypotheses"].append({
            "hypothesis": hypothesis,
            "evidence_against": evidence_against,
            "session": session,
            "loop": loop,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self._save()

    def is_refuted(self, hypothesis: str) -> bool:
        return any(h["hypothesis"] == hypothesis for h in self.state["hypotheses"])

    def start_session(self, session_id: str):
        self.state["sessions"].append({
            "id": session_id,
            "started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ended": None,
        })
        self._save()

    def end_session(self, session_id: str):
        for s in self.state["sessions"]:
            if s["id"] == session_id and not s["ended"]:
                s["ended"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                break
        self._save()

    def _save(self):
        with open(self.store_path, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def export_continuation_context(self) -> dict:
        return {
            "hunt_state": self.state["hunt_state"],
            "family_status": self.state["family_status"],
            "hypotheses_count": len(self.state["hypotheses"]),
            "sessions_count": len(self.state["sessions"]),
        }
