"""Reactive Loop — event-driven pipeline triggered when a new primitive hits the cache.

When a hunter writes a finding, the reactive loop kicks in immediately:
  1. VALIDATE  — run oracle if not confirmed
  2. EXPAND    — spawn variant hunter on nearby targets
  3. CHAIN     — check chains_to against cache, spawn chain-hunter if match
  4. PROPAGATE — cross-flow notify, brain update, memory update
  5. ADAPT     — budget realloc, priority boost, anti-bias check
"""
import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional, Callable

logger = logging.getLogger("sharingan.reactive")


@dataclass
class ReactiveEvent:
    """A new primitive that just hit the cache."""
    primitive: dict
    session_id: str
    flow: str  # "web" | "src"
    timestamp: float = field(default_factory=time.time)


@dataclass
class ReactiveAction:
    """An action the reactive loop decided to take."""
    action_type: str  # validate, expand_variant, expand_class, chain_hunt, propagate, adapt
    primitive_id: str
    details: dict = field(default_factory=dict)
    priority: float = 0.0


class ReactiveLoop:
    """Watches the cache and reacts to new findings in real-time."""

    def __init__(self, session, llm, tools, middleware, make_agent_fn):
        self.session = session
        self.llm = llm
        self.tools = tools
        self.middleware = middleware
        self._make_agent = make_agent_fn
        self._seen_ids: set = set()
        self._action_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._stats = {
            "events_processed": 0,
            "variants_spawned": 0,
            "chains_spawned": 0,
            "oracle_retries": 0,
            "cross_flow_signals": 0,
        }

    def _load_seen_ids(self):
        """Load existing primitive IDs so we only react to NEW ones."""
        for p in self.session.cache.read_all():
            self._seen_ids.add(p["id"])

    def _detect_new_primitives(self) -> list[ReactiveEvent]:
        """Check cache for primitives we haven't seen yet."""
        events = []
        for p in self.session.cache.read_all():
            if p["id"] not in self._seen_ids:
                self._seen_ids.add(p["id"])
                events.append(ReactiveEvent(
                    primitive=p,
                    session_id=self.session.id,
                    flow=p.get("flow", "web"),
                ))
        return events

    async def evaluate(self, event: ReactiveEvent) -> list[ReactiveAction]:
        """Evaluate a new primitive and decide what actions to take."""
        prim = event.primitive
        actions = []

        # 1. VALIDATE — oracle not yet run?
        if not prim.get("oracle_ran"):
            actions.append(ReactiveAction(
                action_type="validate",
                primitive_id=prim["id"],
                details={
                    "class": prim["class"],
                    "path_line": prim.get("path_line", ""),
                    "oracle_type": self._pick_oracle(prim["class"]),
                },
                priority=10.0,
            ))

        # 2. EXPAND — variant search
        # 2a. Same class, nearby endpoints/files
        nearby = self._find_nearby_targets(prim)
        if nearby:
            actions.append(ReactiveAction(
                action_type="expand_variant",
                primitive_id=prim["id"],
                details={
                    "class": prim["class"],
                    "nearby_targets": nearby,
                    "reason": f"Found {prim['class']} at {prim.get('path_line', '?')} — check nearby",
                },
                priority=8.0,
            ))

        # 2b. Same location, other classes that often co-occur
        co_classes = self._co_occurring_classes(prim["class"])
        if co_classes:
            actions.append(ReactiveAction(
                action_type="expand_class",
                primitive_id=prim["id"],
                details={
                    "original_class": prim["class"],
                    "test_classes": co_classes,
                    "location": prim.get("path_line", ""),
                    "reason": f"{prim['class']} often co-occurs with {co_classes}",
                },
                priority=6.0,
            ))

        # 3. CHAIN — does this finding chain with existing cache?
        chain_matches = self._find_chain_matches(prim)
        if chain_matches:
            actions.append(ReactiveAction(
                action_type="chain_hunt",
                primitive_id=prim["id"],
                details={
                    "candidates": chain_matches,
                    "reason": f"New {prim['class']} chains with {len(chain_matches)} existing primitives",
                },
                priority=9.0,
            ))

        # 4. PROPAGATE — cross-flow, brain, memory
        actions.append(ReactiveAction(
            action_type="propagate",
            primitive_id=prim["id"],
            details={
                "flow": event.flow,
                "class": prim["class"],
                "path_line": prim.get("path_line", ""),
                "entry": prim.get("entry", ""),
            },
            priority=3.0,
        ))

        # 5. ADAPT — strategy adjustment
        adapt = self._compute_adaptation(prim)
        if adapt:
            actions.append(ReactiveAction(
                action_type="adapt",
                primitive_id=prim["id"],
                details=adapt,
                priority=2.0,
            ))

        actions.sort(key=lambda a: a.priority, reverse=True)
        return actions

    async def execute_action(self, action: ReactiveAction):
        """Execute a single reactive action."""
        logger.info(f"  REACT [{action.action_type}] prim={action.primitive_id} "
                     f"priority={action.priority}")

        if action.action_type == "validate":
            await self._do_validate(action)
        elif action.action_type == "expand_variant":
            await self._do_expand_variant(action)
        elif action.action_type == "expand_class":
            await self._do_expand_class(action)
        elif action.action_type == "chain_hunt":
            await self._do_chain_hunt(action)
        elif action.action_type == "propagate":
            self._do_propagate(action)
        elif action.action_type == "adapt":
            self._do_adapt(action)

    async def _do_validate(self, action: ReactiveAction):
        """Run oracle on unconfirmed primitive."""
        details = action.details
        oracle_type = details["oracle_type"]
        prim_class = details["class"]
        path_line = details["path_line"]

        self._stats["oracle_retries"] += 1
        logger.info(f"    Oracle retry: {oracle_type} on {prim_class} at {path_line}")

        # The hunter agent handles oracle execution
        flow = "web" if "/" in path_line or "?" in path_line else "src"
        prompt_path = f"agents/{flow}/hunter-{flow}.md"

        if os.path.exists(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), prompt_path
        )):
            agent = self._make_agent(f"oracle-{prim_class}", prompt_path)
            ctx = self.session.get_context(flow)
            ctx["mode"] = "chain"
            ctx["oracle_target"] = {
                "primitive_id": action.primitive_id,
                "class": prim_class,
                "path_line": path_line,
                "oracle_type": oracle_type,
            }

            if self.session.budget.can_spend(3):
                await agent.run(
                    f"Run {oracle_type} oracle on {prim_class} primitive at {path_line}. "
                    f"Confirm or invalidate. Update cache with oracle_ran result.",
                    context=ctx,
                )
                self.session.budget.spend(flow, "oracle_retry", 3,
                                          f"oracle {oracle_type} on {prim_class}")

    async def _do_expand_variant(self, action: ReactiveAction):
        """Spawn variant hunter on nearby targets."""
        details = action.details
        nearby = details["nearby_targets"]
        prim_class = details["class"]

        self._stats["variants_spawned"] += 1
        logger.info(f"    Variant expansion: {prim_class} → {len(nearby)} nearby targets")

        flow = "web"  # determine from context
        prompt_path = f"agents/{flow}/hunter-{flow}.md"

        if self.session.budget.can_spend(5):
            agent = self._make_agent(f"variant-{prim_class}", prompt_path)
            ctx = self.session.get_context(flow)
            ctx["mode"] = "variant"
            ctx["variant_targets"] = nearby
            ctx["original_finding"] = action.primitive_id

            await agent.run(
                f"Variant hunting: found {prim_class} at original location. "
                f"Test these {len(nearby)} nearby targets for the same class: "
                f"{json.dumps(nearby[:10])}",
                context=ctx,
            )
            self.session.budget.spend(flow, "variant", 5,
                                      f"variant {prim_class} x{len(nearby)}")

    async def _do_expand_class(self, action: ReactiveAction):
        """Test co-occurring vulnerability classes at same location."""
        details = action.details
        co_classes = details["test_classes"]
        location = details["location"]
        original = details["original_class"]

        logger.info(f"    Class expansion: {original} → test {co_classes} at {location}")

        # This is informational — added to next hunt round's context
        self.session.memory.set_fact(
            f"co_class_hint_{action.primitive_id}",
            {"location": location, "found": original, "test": co_classes},
            label="INFERRED",
        )

    async def _do_chain_hunt(self, action: ReactiveAction):
        """Spawn chain-hunter for viable chain candidates."""
        candidates = action.details["candidates"]

        self._stats["chains_spawned"] += 1
        logger.info(f"    Chain hunt: {len(candidates)} candidates from {action.primitive_id}")

        for candidate in candidates[:3]:  # top 3 by priority
            if not self.session.budget.can_spend(5):
                break

            flow = "web"
            prompt_path = f"agents/{flow}/hunter-{flow}.md"

            agent = self._make_agent(
                f"chain-{candidate['source_class']}-{candidate['target_class']}",
                prompt_path,
            )
            ctx = self.session.get_context(flow)
            ctx["mode"] = "chain"
            ctx["chain_candidate"] = candidate

            await agent.run(
                f"Chain validation: connect {candidate['source_class']} "
                f"(prim {candidate['source']}) to {candidate['target_class']} "
                f"(prim {candidate['target']}). Build end-to-end PoC. "
                f"Priority score: {candidate['priority']}",
                context=ctx,
            )
            self.session.budget.spend(flow, "chain", 5,
                                      f"chain {candidate['source_class']}→{candidate['target_class']}")

    def _do_propagate(self, action: ReactiveAction):
        """Update brain, memory, cross-flow signals."""
        details = action.details
        prim_class = details["class"]
        flow = details["flow"]

        # Update family status
        self.session.memory.set_family_status(prim_class, "hunting")

        # Brain: record discovery
        self.session.brain.add_discovery(
            f"Found {prim_class} at {details.get('path_line', '?')}",
            evidence_label="READ",
            flow_source=flow,
            primitive_ids=[action.primitive_id],
        )

        # Cross-flow hint: if web finds something, hint src (and vice versa)
        other_flow = "src" if flow == "web" else "web"
        entry = details.get("entry", "")
        path_line = details.get("path_line", "")
        if entry or path_line:
            self.session.memory.set_fact(
                f"cross_flow_hint_{action.primitive_id}",
                {
                    "from_flow": flow,
                    "class": prim_class,
                    "entry": entry,
                    "path_line": path_line,
                    "hint": f"Check {other_flow} flow for corresponding {prim_class}",
                },
                label="INFERRED",
            )
            self._stats["cross_flow_signals"] += 1

        logger.info(f"    Propagated: brain + memory + cross-flow hint for {prim_class}")

    def _do_adapt(self, action: ReactiveAction):
        """Adjust hunt strategy based on finding patterns."""
        details = action.details

        if details.get("boost_family"):
            family = details["boost_family"]
            logger.info(f"    Adapt: boosting priority for family '{family}'")
            self.session.memory.set_fact(
                f"priority_boost_{family}",
                {"family": family, "reason": details.get("reason", "productive area")},
                label="INFERRED",
            )

        if details.get("rotation_warning"):
            logger.warning(f"    Adapt: rotation warning — {details['rotation_warning']}")

    # --- Helper methods ---

    def _pick_oracle(self, prim_class: str) -> str:
        """Select oracle type by primitive class."""
        oracle_map = {
            "sqli": "fuzz", "rce": "fuzz", "stored_xss": "canary",
            "open_redirect": "fuzz", "idor_read": "fuzz", "idor_write": "fuzz",
            "file_read": "canary", "file_write": "canary", "secret_read": "canary",
            "ssrf": "canary", "path_traversal": "canary",
            "race_condition": "race", "deser": "parser_diff",
            "auth_bypass": "fuzz",
        }
        return oracle_map.get(prim_class, "fuzz")

    def _find_nearby_targets(self, prim: dict) -> list[str]:
        """Find endpoints/files near this finding for variant testing."""
        path_line = prim.get("path_line", "")
        entry = prim.get("entry", "")
        nearby = []

        if entry:
            # Web: find endpoints with similar URL pattern
            # e.g., /api/users?id=1 → also check /api/orders?id=1, /api/products?id=1
            base_pattern = re.sub(r'\?.*', '', entry)  # strip params
            base_parts = base_pattern.rstrip('/').split('/')

            brain_api_map = self.session.brain.data.get("api_map", {})
            for endpoint in brain_api_map:
                if endpoint == entry:
                    continue
                ep_parts = endpoint.rstrip('/').split('/')
                # Similar path depth and structure
                if len(ep_parts) == len(base_parts) and ep_parts[:-1] == base_parts[:-1]:
                    nearby.append(endpoint)

        if path_line and ":" in path_line:
            # Source: find files in same directory
            file_path = path_line.split(":")[0]
            directory = os.path.dirname(file_path)
            # Add directory as a hint — the variant hunter will enumerate
            if directory:
                nearby.append(f"directory:{directory}")

        return nearby[:10]

    CO_OCCURRENCE = {
        "sqli": ["auth_bypass", "idor_read"],
        "file_read": ["path_traversal", "secret_read"],
        "ssrf": ["file_read", "secret_read"],
        "idor_read": ["idor_write", "auth_bypass"],
        "stored_xss": ["idor_write"],
        "path_traversal": ["file_read", "file_write"],
        "auth_bypass": ["idor_read", "idor_write"],
        "rce": ["file_write"],
        "deser": ["rce"],
        "open_redirect": ["stored_xss"],
    }

    def _co_occurring_classes(self, prim_class: str) -> list[str]:
        """Classes that frequently co-occur with this one."""
        return self.CO_OCCURRENCE.get(prim_class, [])

    def _find_chain_matches(self, prim: dict) -> list[dict]:
        """Check if this primitive chains with anything in cache."""
        chains_to = prim.get("chains_to", [])
        if not chains_to:
            return []

        all_prims = self.session.cache.read_all()
        matches = []

        for target_class in chains_to:
            for other in all_prims:
                if other["id"] == prim["id"]:
                    continue
                if other.get("class") != target_class:
                    continue
                if not other.get("oracle_ran"):
                    continue

                # Constraint check
                prim_constraint = prim.get("constraint")
                other_constraint = other.get("constraint")
                constraint_count = sum(1 for c in [prim_constraint, other_constraint] if c)

                auth_map = {"none": 0, "user": 1, "admin": 2}
                auth = max(
                    auth_map.get(prim.get("auth", "none"), 0),
                    auth_map.get(other.get("auth", "none"), 0),
                )

                severity_map = {
                    "rce": 4, "sqli": 3, "secret_read": 3, "auth_bypass": 3,
                    "file_write": 3, "deser": 3, "ssrf": 2, "file_read": 2,
                    "idor_write": 2, "stored_xss": 2, "idor_read": 1,
                    "race_condition": 1, "path_traversal": 2, "open_redirect": 1,
                }
                sev = severity_map.get(target_class, 1)
                auth_inv = {0: 4, 1: 2, 2: 1}.get(auth, 1)
                priority = sev * (1 / max(constraint_count, 1)) * auth_inv

                matches.append({
                    "source": prim["id"],
                    "target": other["id"],
                    "source_class": prim["class"],
                    "target_class": target_class,
                    "cross_flow": prim.get("flow") != other.get("flow"),
                    "priority": round(priority, 2),
                })

        matches.sort(key=lambda m: m["priority"], reverse=True)
        return matches

    def _compute_adaptation(self, prim: dict) -> Optional[dict]:
        """Decide if hunt strategy should change based on this finding."""
        prim_class = prim.get("class", "")

        # Check if this family is suddenly productive
        same_class = self.session.cache.read_by_class(prim_class)
        if len(same_class) >= 2:
            return {
                "boost_family": prim_class,
                "reason": f"{len(same_class)} findings in {prim_class} — productive family",
            }

        # Check anti-bias: are we stuck?
        family_status = self.session.memory.state.get("family_status", {})
        hunting_families = [f for f, s in family_status.items()
                           if s.get("status") == "hunting"]
        if len(hunting_families) >= 3:
            all_same = len(set(hunting_families)) == 1
            if all_same:
                return {
                    "rotation_warning": f"Stuck on {hunting_families[0]} — force rotation",
                }

        return None

    # --- Main loop ---

    async def run_reactive_hunt(self, max_rounds: int = 10,
                                 poll_interval: float = 2.0) -> dict:
        """Run the full reactive hunt loop.

        Instead of simple round-based hunting, this:
        1. Spawns initial hunters
        2. Polls cache for new findings
        3. Reacts immediately to each new finding
        4. Spawns variant/chain hunters mid-round
        5. Adapts strategy continuously
        """
        self._load_seen_ids()
        self._running = True
        all_actions = []

        logger.info(f"=== Reactive Hunt Loop started (max {max_rounds} rounds) ===")

        for round_num in range(1, max_rounds + 1):
            if not self.session.budget.can_spend(5):
                logger.info("Budget exhausted — stopping reactive loop")
                break

            logger.info(f"--- Round {round_num} ---")

            # Spawn the primary hunter for this round
            flow = "web"  # or determined by session
            mode = "cold" if round_num == 1 else "variant"
            prompt_path = f"agents/{flow}/hunter-{flow}.md"

            hunter = self._make_agent(f"hunter-{flow}-r{round_num}", prompt_path)
            ctx = self.session.get_context(flow)
            ctx["hunt_round"] = round_num
            ctx["mode"] = mode

            # Include reactive hints from previous rounds
            hints = self._gather_hints()
            if hints:
                ctx["reactive_hints"] = hints

            # Run hunter
            result = await hunter.run(
                f"Hunt for vulnerabilities. Round {round_num}. Mode: {mode}. "
                f"Check cache for existing findings. "
                f"Write findings to cache with chains_to populated.",
                context=ctx,
            )
            self.session.budget.spend(flow, "hunting", 5, f"reactive round {round_num}")

            # Detect new findings from this round
            new_events = self._detect_new_primitives()
            self._stats["events_processed"] += len(new_events)

            if not new_events:
                logger.info(f"  Round {round_num}: no new findings")
                # Two dry rounds in a row → stop
                if round_num >= 2:
                    prev_events = [a for a in all_actions
                                   if a.details.get("round") == round_num - 1]
                    if not prev_events:
                        logger.info("  Two consecutive dry rounds — stopping")
                        break
                continue

            logger.info(f"  Round {round_num}: {len(new_events)} new findings — reacting")

            # React to each new finding
            for event in new_events:
                actions = await self.evaluate(event)
                for action in actions:
                    action.details["round"] = round_num
                    all_actions.append(action)

                    # Execute high-priority actions immediately
                    if action.priority >= 5.0 and self.session.budget.can_spend(3):
                        await self.execute_action(action)

            # Check termination
            stats = self.session.cache.stats()
            if stats["oracle_confirmed"] >= 10:
                logger.info(f"  {stats['oracle_confirmed']} confirmed findings — sufficient")
                break

        self._running = False
        logger.info(f"=== Reactive Hunt Loop ended ===")
        logger.info(f"  Stats: {json.dumps(self._stats)}")

        return {
            "rounds_completed": round_num,
            "actions_taken": len(all_actions),
            "stats": self._stats,
            "cache_stats": self.session.cache.stats(),
        }

    def _gather_hints(self) -> list[dict]:
        """Gather reactive hints from memory for the next hunter."""
        hints = []
        hunt_state = self.session.memory.state.get("hunt_state", {})
        for key, entry in hunt_state.items():
            if key.startswith("co_class_hint_") or key.startswith("cross_flow_hint_"):
                hints.append(entry["value"])
            elif key.startswith("priority_boost_"):
                hints.append(entry["value"])
        return hints[:20]
