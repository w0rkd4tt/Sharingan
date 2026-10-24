#!/usr/bin/env python3
"""Sharingan CLI — dual-flow security harness.

Usage:
    sharingan pentest <target> [--scope=<file>] [--budget=<n>] [--provider=<p>] [--model=<m>]
    sharingan audit <repo_path> [--budget=<n>] [--provider=<p>] [--model=<m>]
    sharingan dual <target> <repo_path> [--scope=<file>] [--budget=<n>] [--provider=<p>] [--model=<m>]
    sharingan config [--provider=<p>] [--model=<m>] [--api-key=<k>] [--base-url=<u>]
    sharingan status [<target>]
"""
import argparse
import asyncio
import json
import logging
import os
import sys

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from runtime.llm import create_backend
from runtime.coordinator import Coordinator
from runtime.tools.registry import ToolRegistry
from runtime.middleware import create_default_middleware


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sharingan")

CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "sharingan.json")


def load_config() -> dict:
    """Load or create default config."""
    default = {
        "provider": "anthropic",
        "model": "",
        "api_key": "",
        "base_url": "",
        "max_tokens": 4096,
        "temperature": 0.0,
        "rate_limit_rps": 10,
        "default_budget": 100,
    }
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            saved = json.load(f)
        default.update(saved)
    return default


def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {CONFIG_PATH}")


def load_scope(scope_file: str) -> dict:
    """Load scope from file."""
    if not scope_file:
        return {}
    with open(scope_file) as f:
        return json.load(f)


async def cmd_pentest(args, config):
    """Run web/host blackbox pentest."""
    scope = load_scope(args.scope) if args.scope else {}
    if not scope:
        scope_path = os.path.join("targets", args.target, "scope.json")
        if os.path.exists(scope_path):
            with open(scope_path) as f:
                scope = json.load(f)

    if not scope:
        print("WARNING: No scope.json found. Create one at targets/<target>/scope.json")
        print('Example: {"in_scope": ["*.example.com"], "out_of_scope": []}')
        return

    provider = args.provider or config["provider"]
    model = args.model or config["model"]

    llm = create_backend(
        provider,
        model=model,
        api_key=args.api_key or config.get("api_key", ""),
        base_url=args.base_url or config.get("base_url", ""),
        max_tokens=config.get("max_tokens", 4096),
        temperature=config.get("temperature", 0.0),
    )

    scope_file = os.path.join("targets", args.target, "scope.json")
    os.makedirs(os.path.dirname(scope_file), exist_ok=True)
    with open(scope_file, "w") as f:
        json.dump(scope, f, indent=2)

    registry = ToolRegistry()
    tools = registry.create_pentest_tools(working_dir=PROJECT_ROOT)
    middleware = create_default_middleware(
        scope_file=os.path.abspath(scope_file),
        rate_limit=config.get("rate_limit_rps", 10),
    )

    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)
    budget = args.budget or config.get("default_budget", 100)

    try:
        results = await coordinator.run_pentest(args.target, scope, budget=budget)
        _print_results(results)
    finally:
        await llm.close()


async def cmd_audit(args, config):
    """Run whitebox source code audit."""
    repo_path = os.path.abspath(args.repo_path)
    if not os.path.isdir(repo_path):
        print(f"ERROR: Repository path not found: {repo_path}")
        return

    provider = args.provider or config["provider"]
    model = args.model or config["model"]

    llm = create_backend(
        provider,
        model=model,
        api_key=args.api_key or config.get("api_key", ""),
        base_url=args.base_url or config.get("base_url", ""),
    )

    registry = ToolRegistry()
    tools = registry.create_audit_tools(working_dir=repo_path)
    middleware = create_default_middleware(rate_limit=config.get("rate_limit_rps", 10))

    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)
    budget = args.budget or config.get("default_budget", 100)

    try:
        results = await coordinator.run_audit(repo_path, budget=budget)
        _print_results(results)
    finally:
        await llm.close()


async def cmd_dual(args, config):
    """Run dual flow (web + whitebox)."""
    scope = load_scope(args.scope) if args.scope else {}
    repo_path = os.path.abspath(args.repo_path)

    provider = args.provider or config["provider"]
    model = args.model or config["model"]

    llm = create_backend(
        provider,
        model=model,
        api_key=args.api_key or config.get("api_key", ""),
        base_url=args.base_url or config.get("base_url", ""),
    )

    registry = ToolRegistry()
    tools = registry.create_pentest_tools(working_dir=PROJECT_ROOT)
    middleware = create_default_middleware(rate_limit=config.get("rate_limit_rps", 10))

    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)
    budget = args.budget or config.get("default_budget", 200)

    try:
        results = await coordinator.run_dual(args.target, repo_path, scope, budget=budget)
        _print_results(results)
    finally:
        await llm.close()


def cmd_config(args, config):
    """Update configuration."""
    changed = False
    if args.provider:
        config["provider"] = args.provider
        changed = True
    if args.model:
        config["model"] = args.model
        changed = True
    if args.api_key:
        config["api_key"] = args.api_key
        changed = True
    if args.base_url:
        config["base_url"] = args.base_url
        changed = True

    if changed:
        save_config(config)
    else:
        print("Current configuration:")
        safe = {k: v if k != "api_key" else ("***" + v[-4:] if v else "(not set)")
                for k, v in config.items()}
        print(json.dumps(safe, indent=2))


def cmd_status(args, config):
    """Show status of a target or all targets."""
    targets_dir = os.path.join(PROJECT_ROOT, "targets")
    if not os.path.isdir(targets_dir):
        print("No targets directory found.")
        return

    if args.target:
        target_dir = os.path.join(targets_dir, args.target)
        if not os.path.isdir(target_dir):
            print(f"Target '{args.target}' not found.")
            return
        _print_target_status(args.target, target_dir)
    else:
        for name in sorted(os.listdir(targets_dir)):
            td = os.path.join(targets_dir, name)
            if os.path.isdir(td):
                _print_target_status(name, td)
                print()


def _print_target_status(name: str, target_dir: str):
    from core.primitive_cache import PrimitiveCache
    from core.budget import BudgetGovernor

    print(f"Target: {name}")
    cache = PrimitiveCache(target_dir)
    stats = cache.stats()
    print(f"  Primitives: {stats['total']} (web: {stats['web']}, src: {stats['src']})")
    print(f"  Oracle confirmed: {stats['oracle_confirmed']}")
    print(f"  Chains: {stats['chains']}")
    if stats['classes']:
        print(f"  Classes: {stats['classes']}")

    budget_path = os.path.join(target_dir, "budget.json")
    if os.path.exists(budget_path):
        bg = BudgetGovernor(target_dir)
        print(f"  Budget: {bg.remaining}/{bg.state['total']} remaining")


def _print_results(results: dict):
    """Pretty print results."""
    print("\n" + "=" * 60)
    print(f"TARGET: {results.get('target', '?')}")
    print("=" * 60)

    summary = results.get("summary", {})
    if summary:
        print(f"\nPrimitives: {summary.get('total', 0)}")
        print(f"Oracle confirmed: {summary.get('oracle_confirmed', 0)}")
        print(f"Chains: {summary.get('chains', 0)}")

    budget = results.get("budget", {})
    if budget:
        print(f"Budget: {budget.get('remaining', '?')}/{budget.get('total', '?')} remaining")

    dual = results.get("dual_confirmed", [])
    if dual:
        print(f"\nDUAL-CONFIRMED findings: {len(dual)}")
        for d in dual:
            print(f"  [{d['class']}] web:{d['web_prim']} + src:{d['src_prim']}")

    # Save full results
    out_path = os.path.join("targets", results.get("target", "unknown"), "results.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Sharingan — dual-flow security harness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # Common args
    def add_common(p):
        p.add_argument("--provider", choices=["anthropic", "openai", "ollama"], default="")
        p.add_argument("--model", default="")
        p.add_argument("--api-key", dest="api_key", default="")
        p.add_argument("--base-url", dest="base_url", default="")
        p.add_argument("--budget", type=int, default=0)

    # pentest
    p_pentest = subparsers.add_parser("pentest", help="Web/host blackbox pentest")
    p_pentest.add_argument("target", help="Target name")
    p_pentest.add_argument("--scope", help="Path to scope.json")
    add_common(p_pentest)

    # audit
    p_audit = subparsers.add_parser("audit", help="Whitebox source code audit")
    p_audit.add_argument("repo_path", help="Path to repository")
    add_common(p_audit)

    # dual
    p_dual = subparsers.add_parser("dual", help="Dual flow (web + whitebox)")
    p_dual.add_argument("target", help="Target name")
    p_dual.add_argument("repo_path", help="Path to repository")
    p_dual.add_argument("--scope", help="Path to scope.json")
    add_common(p_dual)

    # config
    p_config = subparsers.add_parser("config", help="Configure Sharingan")
    p_config.add_argument("--provider", choices=["anthropic", "openai", "ollama"])
    p_config.add_argument("--model")
    p_config.add_argument("--api-key", dest="api_key")
    p_config.add_argument("--base-url", dest="base_url")

    # status
    p_status = subparsers.add_parser("status", help="Show target status")
    p_status.add_argument("target", nargs="?", default="")

    args = parser.parse_args()
    config = load_config()

    if args.command == "pentest":
        asyncio.run(cmd_pentest(args, config))
    elif args.command == "audit":
        asyncio.run(cmd_audit(args, config))
    elif args.command == "dual":
        asyncio.run(cmd_dual(args, config))
    elif args.command == "config":
        cmd_config(args, config)
    elif args.command == "status":
        cmd_status(args, config)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
