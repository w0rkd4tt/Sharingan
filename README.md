# Sharingan

**Dual-flow security harness** — Web/Host blackbox pentest + Whitebox source code audit, powered by any LLM.

```
sharingan pentest <target>     # Web/Host blackbox pentest
sharingan audit <repo>         # Whitebox source code audit
sharingan dual <target> <repo> # Both flows + cross-flow correlation
```

## Architecture

```
┌─ CLI ──────────────────────────────────────────────┐
│  sharingan_cli.py | Claude Code /pentest /audit     │
└──────────────────────────┬─────────────────────────┘
                           │
┌─ Coordinator ────────────┴─────────────────────────┐
│  Recon → Mapper → Hunter(s) → Exploiter → Reporter │
│  Session: PrimitiveCache + Budget + Memory + Brain  │
│  Anti-Bias: off-prior 20%, godhand, R/I/A labels    │
└──────────────────────────┬─────────────────────────┘
                           │
┌─ Agent Runtime ──────────┴─────────────────────────┐
│  Agent (system prompt + tool-use loop)              │
│  Tools: shell, http, nuclei, ffuf, katana, semgrep  │
│  Middleware: scope → destructive → UA → rate → audit │
└──────────────────────────┬─────────────────────────┘
                           │
┌─ LLM Backend ────────────┴─────────────────────────┐
│  Anthropic (Claude) │ OpenAI (GPT-4) │ Ollama/vLLM │
└────────────────────────────────────────────────────┘
```

## 4 cách sử dụng

| Phương pháp | Mô tả | Doc |
|-------------|-------|-----|
| **Claude Code** | Slash commands + hooks + MCP servers | [docs/usage-claude-code.md](docs/usage-claude-code.md) |
| **Codex / OpenAI CLI** | GPT-4o, o3, Azure, Together, Groq | [docs/usage-codex-cli.md](docs/usage-codex-cli.md) |
| **Python API** | Library cho pipeline, CI/CD, automation | [docs/usage-api.md](docs/usage-api.md) |
| **Local Models** | Ollama, vLLM, llama.cpp — 100% offline | [docs/usage-local-model.md](docs/usage-local-model.md) |

## Quick Start

### Claude Code (nhanh nhất)

```bash
git clone https://github.com/w0rkd4tt/Sharingan.git
cd Sharingan
# Trong Claude Code:
/pentest example.com
```

### Standalone CLI

```bash
git clone https://github.com/w0rkd4tt/Sharingan.git
cd Sharingan
pip install -r requirements-runtime.txt

# Config backend
export ANTHROPIC_API_KEY="sk-ant-..."
python sharingan_cli.py config --provider anthropic

# Hoặc dùng local model
python sharingan_cli.py config --provider ollama --model llama3.1

# Tạo scope
mkdir -p targets/example.com
echo '{"in_scope": ["*.example.com"]}' > targets/example.com/scope.json

# Chạy
python sharingan_cli.py pentest example.com
python sharingan_cli.py audit ./my-repo
python sharingan_cli.py dual example.com ./my-repo --budget 200
```

## Flows

### Flow 1: Web/Host Blackbox Pentest

```
/pentest target → recon-web → mapper → hunter-web ×N → exploiter → reporter-web
```

5 agents chạy tuần tự. Hunter chạy loop (tối đa 5 rounds), anti-bias enforce family rotation.

### Flow 2: Whitebox Source Code Audit

```
/audit repo → recon-src → normalize → graph → hunter-src ×N → reporter-src
```

5 agents. Normalize parse code thành function catalog. Graph build data flow graph. Hunter trace taint source→sink.

### Dual Flow

```
/dual target repo → [web flow || src flow] → cross-flow bridge → unified report
```

Cả 2 flows chạy song song. Cross-flow bridge:
- Same vuln class found by both → **DUAL-CONFIRMED** (highest confidence)
- Whitebox taint chain → web exploitation roadmap
- Web oracle confirmation → upgrade whitebox static-only → runtime-validated

## Core Components

| Component | File | Vai trò |
|-----------|------|---------|
| **PrimitiveCache** | `core/primitive_cache.py` | JSONL store cho findings, dedup, chain matching |
| **BudgetGovernor** | `core/budget.py` | Per-flow spend tracking, hard stop |
| **MemoryStore** | `core/memory_store.py` | Cross-session state (hunt_state, hypotheses) |
| **AntiBiasEngine** | `core/anti_bias.py` | Off-prior 20%, family rotation, R/I/A validation |
| **Brain** | `core/brain.py` | Per-target knowledge (tech_stack, api_map, discoveries) |

## Enforcement

Mọi tool call đi qua middleware chain (hoặc hooks trong Claude Code):

| Enforcement | Hành vi |
|-------------|---------|
| **Scope Guard** | Chặn request tới host ngoài scope.json |
| **Destructive Guard** | Chặn `rm -rf`, `sqlmap --os-shell`, `msfconsole`, ... |
| **UA Injector** | Inject Chrome User-Agent cho mọi HTTP request |
| **Rate Limiter** | Token-bucket, default 10 RPS |
| **Audit Logger** | JSONL log mọi tool call |

## Primitive Classes (closed set)

```
file_read, file_write, secret_read, ssrf, sqli, rce, deser,
idor_read, idor_write, stored_xss, auth_bypass,
race_condition, path_traversal, open_redirect
```

Hunters không được invent class mới. Mỗi finding phải có `oracle_ran: true` trước khi vào report.

## Directory Layout

```
Sharingan/
├── sharingan_cli.py              # standalone CLI
├── CLAUDE.md                     # project rules (20 invariants)
├── runtime/                      # agent runtime layer
│   ├── llm/                      #   LLM backends (anthropic, openai, ollama)
│   ├── tools/                    #   tool registry + implementations
│   ├── middleware/                #   enforcement middleware
│   ├── agent.py                  #   Agent class (tool-use loop)
│   ├── session.py                #   hunt session manager
│   └── coordinator.py            #   multi-agent orchestrator
├── agents/web/                   # web flow agent prompts (5 agents)
├── agents/src/                   # src flow agent prompts (5 agents)
├── core/                         # shared infra (cache, budget, memory, brain)
├── .claude/hooks/                # Claude Code enforcement hooks
├── .claude/commands/             # Claude Code slash commands
├── mcp-servers/                  # MCP server implementations
├── knowledge/                    # sink tables, oracle configs, brain patterns
├── config/                       # UA profiles, rate limits, sharingan.json
├── targets/                      # per-target working directories
├── src/                          # SharinganV2 recon/scanner tools
├── tools/                        # shared utilities
├── scripts/                      # brain sync, infra health
└── docs/                         # usage guides per method
```

## LLM Backend Support

| Provider | Models | Tool Calling | Setup |
|----------|--------|-------------|-------|
| **Anthropic** | Claude Sonnet/Opus/Haiku | Native tool_use | `ANTHROPIC_API_KEY` |
| **OpenAI** | GPT-4o, o3, GPT-4o-mini | Function calling | `OPENAI_API_KEY` |
| **Azure OpenAI** | GPT-4 deployments | Function calling | `--base-url` |
| **Together / Groq** | Llama, Mixtral, ... | Function calling | `--base-url` + key |
| **Ollama** | Llama 3.1, Qwen, DeepSeek, ... | Ollama native | Local, no key |
| **vLLM** | Any HuggingFace model | OpenAI-compat | Local GPU server |
| **llama.cpp** | GGUF models | OpenAI-compat | Local, CPU ok |
| **LM Studio** | Any supported model | OpenAI-compat | Local GUI |

## License

MIT
