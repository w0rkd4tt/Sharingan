"""Coordinator — orchestrates multi-agent hunt sessions."""
import asyncio
import json
import logging
import os
from typing import Optional

from .agent import Agent, AgentResult, load_prompt
from .session import Session
from .llm.base import LLMBackend

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.primitive_cache import PrimitiveCache

logger = logging.getLogger("sharingan.coordinator")

SHARINGAN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Coordinator:
    """Orchestrates multi-agent security assessments."""

    def __init__(self, llm: LLMBackend, tools: list = None, middleware: list = None):
        self.llm = llm
        self.tools = tools or []
        self.middleware = middleware or []

    def _make_agent(self, name: str, prompt_path: str, extra_tools: list = None) -> Agent:
        """Create an agent with the given prompt and tools."""
        full_path = os.path.join(SHARINGAN_ROOT, prompt_path)
        system = load_prompt(full_path)
        tools = self.tools + (extra_tools or [])
        return Agent(
            name=name,
            system_prompt=system,
            llm=self.llm,
            tools=tools,
            middleware=self.middleware,
        )

    async def run_pentest(self, target: str, scope: dict,
                          budget: int = 100) -> dict:
        """Run the full web/host blackbox pentest pipeline."""
        logger.info(f"=== PENTEST: {target} ===")
        with Session(target, budget_total=budget, scope=scope) as session:
            results = {"target": target, "phases": {}}

            # Phase 1: Recon
            logger.info("[Phase 1] Reconnaissance")
            recon = self._make_agent("recon-web", "agents/web/recon-web.md")
            ctx = session.get_context("web")
            r = await recon.run(
                f"Enumerate the attack surface for target: {target}. "
                f"In-scope domains: {json.dumps(scope.get('in_scope', []))}",
                context=ctx,
            )
            results["phases"]["recon"] = {
                "content": r.content, "tools": r.tool_calls_made,
                "tokens": r.tokens_used,
            }
            session.budget.spend("web", "recon", 5, "recon phase")

            # Phase 2: Mapping
            logger.info("[Phase 2] Endpoint Mapping")
            mapper = self._make_agent("mapper", "agents/web/mapper.md")
            ctx = session.get_context("web")
            r = await mapper.run(
                "Deep crawl discovered endpoints, analyze JS, map auth flows.",
                context=ctx,
            )
            results["phases"]["mapping"] = {
                "content": r.content, "tools": r.tool_calls_made,
                "tokens": r.tokens_used,
            }
            session.budget.spend("web", "mapping", 5, "mapping phase")

            # Phase 3: Hunt loop
            logger.info("[Phase 3] Vulnerability Hunting")
            hunt_round = 0
            hunt_history = []
            while session.budget.can_spend(10):
                hunt_round += 1
                logger.info(f"  Hunt round {hunt_round}")

                rotation = session.anti_bias.validate_family_rotation(hunt_history)
                if not rotation["valid"]:
                    logger.warning(f"  Forced rotation from {rotation['stuck_family']}")

                hunter = self._make_agent("hunter-web", "agents/web/hunter-web.md")
                ctx = session.get_context("web")
                ctx["hunt_round"] = hunt_round
                ctx["mode"] = "cold" if hunt_round == 1 else "variant"

                r = await hunter.run(
                    f"Hunt for vulnerabilities. Round {hunt_round}. "
                    f"Mode: {ctx['mode']}. Check cache for existing findings first.",
                    context=ctx,
                )
                results["phases"][f"hunt_round_{hunt_round}"] = {
                    "content": r.content, "tools": r.tool_calls_made,
                }
                session.budget.spend("web", "hunting", 10, f"hunt round {hunt_round}")
                hunt_history.append({"family": "mixed", "round": hunt_round})

                stats = session.cache.stats()
                if stats["oracle_confirmed"] >= 5:
                    logger.info(f"  Found {stats['oracle_confirmed']} confirmed — moving to exploitation")
                    break

                if hunt_round >= 5:
                    break

            # Phase 4: Chain exploitation
            chains = session.cache.find_chain_candidates()
            if chains:
                logger.info(f"[Phase 4] Chain Exploitation ({len(chains)} candidates)")
                exploiter = self._make_agent("exploiter", "agents/web/exploiter.md")
                ctx = session.get_context("web")
                ctx["chain_candidates"] = chains[:5]
                r = await exploiter.run(
                    "Build end-to-end PoCs for the top chain candidates.",
                    context=ctx,
                )
                results["phases"]["exploitation"] = {
                    "content": r.content, "tools": r.tool_calls_made,
                }

            # Phase 5: Report
            logger.info("[Phase 5] Report Generation")
            reporter = self._make_agent("reporter-web", "agents/web/reporter-web.md")
            ctx = session.get_context("web")
            r = await reporter.run(
                "Generate the final security advisory from confirmed findings.",
                context=ctx,
            )
            results["phases"]["report"] = {"content": r.content}
            results["summary"] = session.cache.stats()
            results["budget"] = session.budget.summary()

        return results

    async def run_audit(self, repo_path: str, budget: int = 100) -> dict:
        """Run whitebox source code audit pipeline."""
        target = os.path.basename(os.path.abspath(repo_path))
        logger.info(f"=== AUDIT: {target} ({repo_path}) ===")
        with Session(target, budget_total=budget) as session:
            results = {"target": target, "repo": repo_path, "phases": {}}

            # Step 1-2: Recon
            logger.info("[Step 1-2] Source Reconnaissance")
            recon = self._make_agent("recon-src", "agents/src/recon-src.md")
            r = await recon.run(
                f"Map the attack surface of repository at: {repo_path}",
                context=session.get_context("src"),
            )
            results["phases"]["recon"] = {"content": r.content, "tools": r.tool_calls_made}
            session.budget.spend("src", "recon", 5, "source recon")

            # Step 3: Normalize
            logger.info("[Step 3] Code Normalization")
            normalizer = self._make_agent("normalize", "agents/src/normalize.md")
            r = await normalizer.run(
                f"Parse source code into function catalog with sink labels. Repo: {repo_path}",
                context=session.get_context("src"),
            )
            results["phases"]["normalize"] = {"content": r.content, "tools": r.tool_calls_made}
            session.budget.spend("src", "normalize", 5, "normalization")

            # Step 4: Graph
            logger.info("[Step 4] Graph Building")
            grapher = self._make_agent("graph", "agents/src/graph.md")
            r = await grapher.run(
                "Build reachability, data flow, lifecycle, and contract graphs.",
                context=session.get_context("src"),
            )
            results["phases"]["graph"] = {"content": r.content, "tools": r.tool_calls_made}
            session.budget.spend("src", "graph", 5, "graph building")

            # Steps 5-7: Hunt loop
            logger.info("[Steps 5-7] Hunt Loop")
            hunt_round = 0
            while session.budget.can_spend(10):
                hunt_round += 1
                hunter = self._make_agent("hunter-src", "agents/src/hunter-src.md")
                ctx = session.get_context("src")
                ctx["hunt_round"] = hunt_round
                ctx["repo_path"] = repo_path
                r = await hunter.run(
                    f"Hunt for vulnerabilities in source code. Round {hunt_round}.",
                    context=ctx,
                )
                results["phases"][f"hunt_round_{hunt_round}"] = {
                    "content": r.content, "tools": r.tool_calls_made,
                }
                session.budget.spend("src", "hunting", 10, f"hunt round {hunt_round}")

                stats = session.cache.stats()
                if stats["oracle_confirmed"] >= 5 or hunt_round >= 5:
                    break

            # Step 8: Report
            logger.info("[Step 8] Report Generation")
            reporter = self._make_agent("reporter-src", "agents/src/reporter-src.md")
            r = await reporter.run(
                "Generate the security audit report from confirmed findings.",
                context=session.get_context("src"),
            )
            results["phases"]["report"] = {"content": r.content}
            results["summary"] = session.cache.stats()
            results["budget"] = session.budget.summary()

        return results

    async def run_dual(self, target: str, repo_path: str,
                       scope: dict, budget: int = 200) -> dict:
        """Run both flows in parallel with cross-flow bridge."""
        logger.info(f"=== DUAL: {target} + {repo_path} ===")

        web_task = asyncio.create_task(
            self.run_pentest(target, scope, budget=budget // 2)
        )
        src_task = asyncio.create_task(
            self.run_audit(repo_path, budget=budget // 2)
        )

        web_results, src_results = await asyncio.gather(web_task, src_task)

        target_dir = os.path.join("targets", target)
        cache = PrimitiveCache(target_dir)
        web_prims = cache.read_all(flow="web")
        src_prims = cache.read_all(flow="src")

        dual_confirmed = []
        for wp in web_prims:
            for sp in src_prims:
                if (wp.get("class") == sp.get("class") and
                    wp.get("oracle_ran") and sp.get("oracle_ran")):
                    dual_confirmed.append({
                        "class": wp["class"],
                        "web_prim": wp["id"],
                        "src_prim": sp["id"],
                        "confidence": "DUAL-CONFIRMED",
                    })

        return {
            "target": target,
            "repo": repo_path,
            "web": web_results,
            "src": src_results,
            "dual_confirmed": dual_confirmed,
            "cross_flow_chains": cache.find_chain_candidates(),
        }
