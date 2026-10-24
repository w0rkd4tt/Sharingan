"""Session — manages a hunt session (target + shared state)."""
import os
import json
import time
import uuid
import logging
from typing import Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.primitive_cache import PrimitiveCache
from core.budget import BudgetGovernor
from core.memory_store import MemoryStore
from core.anti_bias import AntiBiasEngine
from core.brain import Brain

logger = logging.getLogger("sharingan.session")


class Session:
    """A hunt session for a single target."""

    def __init__(self, target_name: str, target_dir: str = "",
                 budget_total: int = 100, scope: Optional[dict] = None):
        self.id = f"session_{uuid.uuid4().hex[:8]}"
        self.target_name = target_name
        self.target_dir = target_dir or os.path.join("targets", target_name)
        os.makedirs(self.target_dir, exist_ok=True)

        self.cache = PrimitiveCache(self.target_dir)
        self.budget = BudgetGovernor(self.target_dir, budget_total)
        self.memory = MemoryStore(self.target_dir)
        self.anti_bias = AntiBiasEngine()
        self.brain = Brain(self.target_dir, target_name)

        self.scope = scope
        scope_path = os.path.join(self.target_dir, "scope.json")
        if scope:
            with open(scope_path, "w") as f:
                json.dump(scope, f, indent=2)
        elif os.path.exists(scope_path):
            with open(scope_path, "r") as f:
                self.scope = json.load(f)

        os.environ["SCOPE_FILE"] = os.path.abspath(scope_path) if self.scope else ""
        os.environ["ACTIVE_TARGET"] = target_name

        self.memory.start_session(self.id)
        self.started = time.time()
        logger.info(f"Session {self.id} started for target '{target_name}'")

    def get_context(self, flow: str = "web") -> dict:
        """Build context dict to pass to agents."""
        return {
            "session_id": self.id,
            "target": self.target_name,
            "flow": flow,
            "scope": self.scope,
            "tech_stack": self.brain.data.get("tech_stack", []),
            "api_map": self.brain.data.get("api_map", {}),
            "cache_stats": self.cache.stats(),
            "budget": self.budget.summary(),
            "open_families": self.memory.get_open_families(),
            "hunt_state": {k: v["value"] for k, v in
                          self.memory.state.get("hunt_state", {}).items()},
        }

    def end(self):
        """End the session."""
        self.memory.end_session(self.id)
        duration = time.time() - self.started
        logger.info(
            f"Session {self.id} ended. Duration: {duration:.0f}s. "
            f"Cache: {self.cache.stats()['total']} primitives. "
            f"Budget remaining: {self.budget.remaining}"
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.end()
