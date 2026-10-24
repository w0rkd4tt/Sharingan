# Sharingan + LLM API (Python)

Sử dụng Sharingan agent runtime như Python library — tích hợp vào pipeline, automation, CI/CD, hoặc custom tooling.

## Yêu cầu

- Python 3.10+
- `pip install anthropic openai httpx` (tuỳ backend)

## Cài đặt

```bash
git clone https://github.com/w0rkd4tt/Sharingan.git
cd Sharingan
pip install -r requirements-runtime.txt
```

## Quick Start

### Chạy pentest bằng Python script

```python
import asyncio
import sys
sys.path.insert(0, "/path/to/Sharingan")

from runtime.llm import create_backend
from runtime.coordinator import Coordinator
from runtime.tools.registry import ToolRegistry
from runtime.middleware import create_default_middleware


async def main():
    # 1. Tạo LLM backend
    llm = create_backend(
        "anthropic",
        model="claude-sonnet-4-20250514",
        api_key="sk-ant-...",
    )

    # 2. Tạo tools + middleware
    registry = ToolRegistry()
    tools = registry.create_pentest_tools(working_dir="/path/to/Sharingan")
    middleware = create_default_middleware(
        scope_file="targets/example.com/scope.json",
        rate_limit=10,
    )

    # 3. Tạo coordinator và chạy
    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)
    results = await coordinator.run_pentest(
        target="example.com",
        scope={"in_scope": ["*.example.com"], "out_of_scope": []},
        budget=100,
    )

    print(f"Findings: {results['summary']['total']}")
    print(f"Confirmed: {results['summary']['oracle_confirmed']}")

    await llm.close()

asyncio.run(main())
```

## Sử dụng từng component

### LLM Backend

```python
from runtime.llm import create_backend
from runtime.llm.base import ToolDefinition

# Anthropic
llm = create_backend("anthropic", model="claude-sonnet-4-20250514")

# OpenAI
llm = create_backend("openai", model="gpt-4o", api_key="sk-...")

# Ollama (local)
llm = create_backend("ollama", model="llama3.1", base_url="http://localhost:11434")

# Chat đơn giản
response = await llm.chat(
    messages=[{"role": "user", "content": "Analyze this HTTP response..."}],
    system="You are a security analyst.",
)
print(response.content)
print(response.usage)  # {"input_tokens": ..., "output_tokens": ...}

# Chat với tools
tools = [ToolDefinition(
    name="http_request",
    description="Make HTTP request",
    parameters={
        "type": "object",
        "properties": {"url": {"type": "string"}, "method": {"type": "string"}},
        "required": ["url"],
    },
)]
response = await llm.chat(messages=[...], tools=tools)
if response.has_tool_calls:
    for tc in response.tool_calls:
        print(f"Tool: {tc.name}, Args: {tc.arguments}")
```

### Agent (single agent)

```python
from runtime.agent import Agent, load_prompt
from runtime.llm import create_backend
from runtime.tools.registry import ToolRegistry

llm = create_backend("anthropic")
registry = ToolRegistry()
tools = registry.create_default_tools(".")

# Load prompt từ file
system = load_prompt("agents/web/hunter-web.md")

agent = Agent(
    name="hunter-web",
    system_prompt=system,
    llm=llm,
    tools=tools,
    max_turns=30,
    max_tokens_total=100_000,
)

result = await agent.run(
    task="Hunt for SSRF vulnerabilities on https://example.com/api/",
    context={"scope": {"in_scope": ["*.example.com"]}},
)

print(f"Content: {result.content}")
print(f"Tools used: {result.tool_calls_made}")
print(f"Tokens: {result.tokens_used}")
print(f"Duration: {result.duration_seconds:.1f}s")
```

### Session

```python
from runtime.session import Session

# Tạo session (tự tạo thư mục, init cache/budget/memory/brain)
session = Session(
    target_name="example.com",
    budget_total=100,
    scope={"in_scope": ["*.example.com"]},
)

# Lấy context cho agent
ctx = session.get_context(flow="web")
# → {"session_id": "...", "target": "example.com", "scope": {...},
#    "tech_stack": [], "cache_stats": {...}, "budget": {...}, ...}

# Dùng shared state
session.brain.update_tech_stack(["PHP", "MySQL", "Apache"])
session.cache.write_primitive({
    "class": "sqli",
    "path_line": "/api/search:param=q",
    "flow": "web",
    "evidence_label": "READ",
})
session.budget.spend("web", "sqli", 5, "SQL injection hunting")
session.memory.set_fact("has_waf", True, label="INFERRED")

# Kết thúc session
session.end()
```

### Middleware (custom)

```python
from runtime.middleware.base import Middleware

class CustomNotifier(Middleware):
    """Gửi Slack notification khi tìm thấy critical finding."""

    async def post_tool(self, agent_name, tool_name, args, result):
        if tool_name == "write_file" and "primitives.jsonl" in args.get("path", ""):
            # Parse finding, check severity
            await self.send_slack(f"[{agent_name}] New finding written")

    async def send_slack(self, message):
        # ... webhook logic
        pass


# Thêm vào middleware chain
from runtime.middleware import create_default_middleware
mw = create_default_middleware(scope_file="scope.json")
mw.append(CustomNotifier())
```

### Tools (custom)

```python
from runtime.tools.registry import Tool

class BurpScanTool(Tool):
    name = "burp_scan"
    description = "Launch Burp Suite active scan on a URL"
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Target URL"},
            "config": {"type": "string", "description": "Scan config name"},
        },
        "required": ["url"],
    }

    async def execute(self, args: dict) -> str:
        url = args["url"]
        # Call Burp REST API
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:1337/v0.1/scan",
                json={"urls": [url]},
            )
            return resp.text

# Đăng ký tool
from runtime.tools.registry import ToolRegistry
registry = ToolRegistry()
tools = registry.create_pentest_tools(".")
registry.register(BurpScanTool())
```

## Patterns nâng cao

### Multi-model pipeline

Dùng model khác nhau cho từng phase:

```python
from runtime.llm import create_backend

# Recon dùng model nhẹ (nhanh, rẻ)
llm_fast = create_backend("openai", model="gpt-4o-mini")

# Hunting dùng model mạnh (chính xác)
llm_strong = create_backend("anthropic", model="claude-sonnet-4-20250514")

# Tạo agent với LLM phù hợp
recon_agent = Agent("recon", recon_prompt, llm_fast, tools)
hunter_agent = Agent("hunter", hunter_prompt, llm_strong, tools)

await recon_agent.run("Enumerate attack surface for target.com")
await hunter_agent.run("Hunt for vulnerabilities based on recon data")
```

### Batch audit nhiều repo

```python
import asyncio
from runtime.coordinator import Coordinator

async def batch_audit(repos: list[str]):
    llm = create_backend("anthropic")
    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)

    tasks = [coordinator.run_audit(repo, budget=50) for repo in repos]
    results = await asyncio.gather(*tasks)

    for repo, result in zip(repos, results):
        print(f"{repo}: {result['summary']['total']} findings")

    await llm.close()

asyncio.run(batch_audit([
    "./repo-auth-service",
    "./repo-payment-api",
    "./repo-admin-panel",
]))
```

### CI/CD integration

```python
# ci_security_gate.py — chạy trong CI pipeline
import asyncio, sys, json
sys.path.insert(0, "/opt/sharingan")

from runtime.llm import create_backend
from runtime.coordinator import Coordinator
from runtime.tools.registry import ToolRegistry
from runtime.middleware import create_default_middleware

async def security_gate():
    llm = create_backend("anthropic", api_key=os.environ["ANTHROPIC_API_KEY"])
    registry = ToolRegistry()
    tools = registry.create_audit_tools(working_dir=os.environ["CI_PROJECT_DIR"])
    middleware = create_default_middleware()

    coordinator = Coordinator(llm=llm, tools=tools, middleware=middleware)
    results = await coordinator.run_audit(
        os.environ["CI_PROJECT_DIR"],
        budget=30,  # nhỏ cho CI
    )

    critical = results["summary"].get("oracle_confirmed", 0)
    if critical > 0:
        print(f"BLOCKED: {critical} confirmed vulnerabilities found")
        sys.exit(1)
    
    print("PASSED: No confirmed vulnerabilities")
    sys.exit(0)

asyncio.run(security_gate())
```

## API Reference

### `create_backend(provider, **kwargs) → LLMBackend`

| Param | Type | Default |
|-------|------|---------|
| `provider` | `"anthropic"` \| `"openai"` \| `"ollama"` | required |
| `model` | str | auto (env var hoặc default) |
| `api_key` | str | env var |
| `base_url` | str | provider default |
| `max_tokens` | int | 4096 |
| `temperature` | float | 0.0 |

### `Agent(name, system_prompt, llm, tools, middleware, max_turns, max_tokens_total)`

| Param | Type | Default |
|-------|------|---------|
| `name` | str | required |
| `system_prompt` | str | required |
| `llm` | LLMBackend | required |
| `tools` | list[Tool] | [] |
| `middleware` | list[Middleware] | [] |
| `max_turns` | int | 50 |
| `max_tokens_total` | int | 200,000 |

### `AgentResult`

| Field | Type | Description |
|-------|------|-------------|
| `content` | str | Final text response |
| `tool_calls_made` | int | Total tool calls executed |
| `tokens_used` | dict | `{"input": N, "output": N}` |
| `duration_seconds` | float | Wall clock time |
| `error` | str \| None | Error message if failed |

### `Coordinator(llm, tools, middleware)`

| Method | Params | Returns |
|--------|--------|---------|
| `run_pentest(target, scope, budget)` | str, dict, int | dict (phases + summary) |
| `run_audit(repo_path, budget)` | str, int | dict (phases + summary) |
| `run_dual(target, repo_path, scope, budget)` | str, str, dict, int | dict (web + src + dual_confirmed) |
