# CLAUDE.md — Sharingan

Dual-flow security harness: Web/Host blackbox pentest + Whitebox source code audit, unified knowledge & enforcement.

Default language: Vietnamese (unless asked for English).

## Flows

| Command | Flow | Description |
|---------|------|-------------|
| `/pentest <TARGET>` | Web/Host | Blackbox pentest on live targets |
| `/audit <REPO>` | Whitebox | Source code security audit |
| `/dual <TARGET> <REPO>` | Both | Dual flow with cross-flow bridge |

## Context Loading Rules

**DO NOT load agent prompts at session start.** Only load when triggered:

| Trigger | Load |
|---------|------|
| `/pentest <X>` | `agents/web/*.md` prompts, scope.json, brain.json |
| `/audit <X>` | `agents/src/*.md` prompts, coordinator.md |
| `/dual <X> <Y>` | All agent prompts, coordinator.md, scope.json, brain.json |
| `/attack-tree` | `.claude/commands/attack-tree.md` |
| `/attack-coverage` | `.claude/commands/attack-coverage.md` |
| `/brain-sync` | Run brain sync scripts |
| Scope questions | grep on scope.json directly |
| General questions | This file is enough |

## Enforcement (runtime hooks — not bypassable)

| Hook | Event | What |
|------|-------|------|
| `scope_guard.py` | PreToolUse | Block out-of-scope hosts |
| `force_user_agent.py` | PreToolUse | Inject Chrome UA on outbound HTTP |
| `rate_limiter.py` | PreToolUse | Token-bucket RPS limiting |
| `block_platform_emails.py` | PreToolUse | Email RoE enforcement |
| `destructive_guard.py` | PreToolUse | Block rm -rf, sqlmap --os-shell, msfconsole, etc. |
| `finding_logger.py` | PostToolUse | Audit log all cache/brain writes |

## Identity Rules

**Outbound UA:** Every HTTP request identifies as Chrome. Source of truth: `config/user-agents.json`. Never hardcode a UA string.

**Scope:** All targets must have a `scope.json` in their target directory. Out-of-scope requests are blocked by hook.

## Primitive Cache

Unified store at `targets/<TARGET>/cache/primitives.jsonl`. Both flows write here. Schema: see `core/primitive_cache.py`.

**Closed set of primitive classes:** file_read, file_write, secret_read, ssrf, sqli, rce, deser, idor_read, idor_write, stored_xss, auth_bypass, race_condition, path_traversal, open_redirect. Hunters must not invent new classes.

## Anti-Bias (mandatory for both flows)

- **Off-prior 20%:** ≥20% of hunt slices target non-obvious families
- **Godhand:** Once taint found, trace to sink. No jumping mid-trace.
- **R/I/A labels:** Every claim tagged READ/INFERRED/ASSUMED
- **Family rotation:** No 3+ consecutive rounds on same family
- **Critic reconciliation:** Critic based on ASSUMED evidence → keep finding

## Evidence Rules

- `oracle_ran: true` required before any finding enters a report
- Evidence labels: READ (observed), INFERRED (pattern-based), ASSUMED (hypothesis)
- >50% ASSUMED in a chain → downgrade severity
- M/D/E stamps required: Mechanism, Demonstration, Exploitability

## Knowledge Store

| Component | Location |
|-----------|----------|
| Per-target data | `targets/<TARGET>/brain.json` |
| Shared patterns | `knowledge/brain-patterns.json` |
| Sink tables | `knowledge/sink-tables/<lang>.json` |
| Memory Store | `targets/<TARGET>/memory_store.json` |
| Budget | `targets/<TARGET>/budget.json` |

## Directory Layout

```
sharingan/
├── CLAUDE.md                    ← you are here
├── coordinator.md               ← multi-agent coordinator prompt
├── .claude/hooks/               ← runtime enforcement hooks
├── .claude/commands/            ← slash commands
├── agents/web/                  ← web flow agent prompts
├── agents/src/                  ← whitebox flow agent prompts
├── core/                        ← Python infrastructure
├── src/                         ← SharinganV2 recon/scanner (existing)
├── mcp-servers/                 ← MCP server implementations
├── knowledge/                   ← attack patterns, sink tables, oracle configs
├── targets/                     ← per-target working directories
├── config/                      ← UA profiles, rate limits, budgets
├── tools/                       ← shared utilities
└── scripts/                     ← brain sync, infra health
```

## Cross-Flow Bridge

When both flows active (`/dual`), findings correlate:
- Same vuln found by both → **DUAL-CONFIRMED** (highest confidence)
- Whitebox taint chain → web exploitation roadmap
- Web oracle confirmation → upgrade whitebox from static-only to runtime-validated

## Invariants (20 rules — violations are bugs)

1. Coordinator never hunts
2. "Model says vulnerable" ≠ evidence
3. Missing graph edge ≠ safe
4. Reporter never hunts
5. ≥20% off-prior slices
6. Unclosed family ≠ not attempted
7. R/I/A labels on every claim
8. Dedup before cache write
9. Constraint-aware chain matching
10. Recon incremental on re-runs
11. Normalize is polyglot (parallel)
12. Oracle protocol per-class
13. Hunters broadcast via cache
14. Graph thread stays alive
15. Chain-hunter must run end-to-end PoC
16. Session budget is hard
17. RESIDUAL entries keep chains_to
18. UA enforcement on all outbound web requests
19. Cross-flow primitives require constraint check
20. DUAL-CONFIRMED > SINGLE-CONFIRMED > RESIDUAL
