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

## Agent Runtime Layer

Standalone Python runtime — runs Sharingan without Claude Code. Supports any LLM backend.

### CLI Usage

```bash
# Configure backend
python sharingan_cli.py config --provider anthropic --model claude-sonnet-4-20250514
python sharingan_cli.py config --provider ollama --model llama3.1 --base-url http://localhost:11434

# Run assessments
python sharingan_cli.py pentest <target> --scope scope.json
python sharingan_cli.py audit <repo_path>
python sharingan_cli.py dual <target> <repo_path> --scope scope.json --budget 200
```

### LLM Backends

| Provider | Class | API |
|----------|-------|-----|
| `anthropic` | `AnthropicBackend` | Messages API (Claude) |
| `openai` | `OpenAIBackend` | Chat Completions (GPT-4, Azure, Together) |
| `ollama` | `OllamaBackend` | Ollama native + OpenAI-compat (vLLM, llama.cpp, LM Studio) |

### Middleware (replaces .claude/hooks/ in standalone mode)

| Middleware | Replaces Hook | What |
|-----------|--------------|------|
| `ScopeGuardMiddleware` | `scope_guard.py` | Block out-of-scope hosts |
| `UAInjectorMiddleware` | `force_user_agent.py` | Inject Chrome UA |
| `RateLimiterMiddleware` | `rate_limiter.py` | Token-bucket RPS |
| `DestructiveGuardMiddleware` | `destructive_guard.py` | Block dangerous commands |
| `AuditLoggerMiddleware` | `finding_logger.py` | JSONL audit trail |

### Architecture

```
sharingan_cli.py → Coordinator → Agent(s) → LLM Backend
                                    ↓
                              Tool Registry → Middleware → Tool Execution
                                    ↓
                              core/ (PrimitiveCache, Budget, Memory, Brain, AntiBias)
```

## Directory Layout

```
sharingan/
├── CLAUDE.md                    ← you are here
├── sharingan_cli.py             ← standalone CLI entry point
├── coordinator.md               ← multi-agent coordinator prompt
├── .claude/hooks/               ← Claude Code enforcement hooks
├── .claude/commands/            ← Claude Code slash commands
├── runtime/                     ← agent runtime layer
│   ├── llm/                     ← LLM backend abstraction (anthropic, openai, ollama)
│   ├── tools/                   ← tool registry (shell, file_ops, web, scanners)
│   ├── middleware/              ← enforcement middleware (scope, rate, UA, destructive)
│   ├── agent.py                 ← Agent class (tool-use loop)
│   ├── session.py               ← hunt session manager
│   └── coordinator.py           ← multi-agent orchestrator
├── agents/web/                  ← web flow agent prompts
├── agents/src/                  ← whitebox flow agent prompts
├── core/                        ← Python infrastructure (cache, budget, memory, brain)
├── src/                         ← SharinganV2 recon/scanner (existing)
├── mcp-servers/                 ← MCP server implementations
├── knowledge/                   ← attack patterns, sink tables, oracle configs
├── targets/                     ← per-target working directories
├── config/                      ← UA profiles, rate limits, budgets, sharingan.json
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
