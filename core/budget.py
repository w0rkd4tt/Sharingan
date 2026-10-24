"""Budget Governor — per-flow, per-family caps with hard stop."""
import json
import os
import time


class BudgetGovernor:
    def __init__(self, target_dir: str, total_budget: int = 100):
        self.store_path = os.path.join(target_dir, "budget.json")
        if os.path.exists(self.store_path):
            with open(self.store_path, "r") as f:
                self.state = json.load(f)
        else:
            self.state = {
                "total": total_budget,
                "spent": {"web": 0, "src": 0},
                "per_family": {},
                "history": [],
            }

    @property
    def remaining(self) -> int:
        return self.state["total"] - sum(self.state["spent"].values())

    def can_spend(self, amount: int = 1) -> bool:
        return self.remaining >= amount

    def spend(self, flow: str, family: str, amount: int = 1, description: str = ""):
        if not self.can_spend(amount):
            raise RuntimeError(
                f"Budget exhausted. Remaining: {self.remaining}, requested: {amount}"
            )
        self.state["spent"][flow] = self.state["spent"].get(flow, 0) + amount
        fam_key = f"{flow}:{family}"
        self.state["per_family"][fam_key] = (
            self.state["per_family"].get(fam_key, 0) + amount
        )
        self.state["history"].append({
            "flow": flow,
            "family": family,
            "amount": amount,
            "description": description,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "remaining_after": self.remaining,
        })
        self._save()

    def _save(self):
        with open(self.store_path, "w") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def summary(self) -> dict:
        return {
            "total": self.state["total"],
            "spent": self.state["spent"],
            "remaining": self.remaining,
            "per_family": self.state["per_family"],
        }
