"""Knowledge Store — brain.json manager with evidence tracking."""
import json
import os
import time


BRAIN_TEMPLATE = {
    "target": "",
    "flow": "dual",
    "tech_stack": [],
    "api_map": {},
    "js_inventory": [],
    "accounts": [],
    "credentials_found": [],
    "key_discoveries": [],
    "attack_surface": {},
    "session_notes": [],
}


class Brain:
    def __init__(self, target_dir: str, target_name: str = ""):
        self.path = os.path.join(target_dir, "brain.json")
        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self.data = json.load(f)
        else:
            self.data = {**BRAIN_TEMPLATE, "target": target_name}
            self._save()

    def add_discovery(
        self,
        finding: str,
        evidence_label: str = "ASSUMED",
        confidence: str = "E",
        flow_source: str = "web",
        primitive_ids: list = None,
    ):
        self.data["key_discoveries"].append({
            "finding": finding,
            "evidence_label": evidence_label,
            "confidence": confidence,
            "flow_source": flow_source,
            "primitive_ids": primitive_ids or [],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self._save()

    def update_tech_stack(self, tech: list):
        existing = set(self.data["tech_stack"])
        for t in tech:
            if t not in existing:
                self.data["tech_stack"].append(t)
        self._save()

    def update_api_map(self, endpoint: str, details: dict):
        self.data["api_map"][endpoint] = details
        self._save()

    def add_js_entry(self, url: str, findings: list):
        self.data["js_inventory"].append({
            "url": url,
            "findings": findings,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self._save()

    def add_session_note(self, note: str, session_id: str = ""):
        self.data["session_notes"].append({
            "note": note,
            "session": session_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        self._save()

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def export(self) -> dict:
        return self.data.copy()
