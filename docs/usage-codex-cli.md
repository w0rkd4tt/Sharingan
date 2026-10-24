# Sharingan + OpenAI Codex CLI

Sử dụng Sharingan với [OpenAI Codex CLI](https://github.com/openai/codex) — agent runtime chạy qua OpenAI models (GPT-4o, o3, ...) thay vì Claude.

## Yêu cầu

- Python 3.10+
- OpenAI API key (hoặc Azure OpenAI endpoint)
- `pip install openai httpx`
- External tools tuỳ flow (katana, nuclei, semgrep, ...)

## Cài đặt

```bash
git clone https://github.com/w0rkd4tt/Sharingan.git
cd Sharingan
pip install -r requirements-runtime.txt

# Set OpenAI API key
export OPENAI_API_KEY="sk-..."

# Config Sharingan dùng OpenAI
python sharingan_cli.py config --provider openai --model gpt-4o
```

## Cách hoạt động

Sharingan agent runtime thay thế Claude Code:

```
sharingan_cli.py
  → Coordinator (orchestrator)
    → Agent (system_prompt + tools + OpenAIBackend)
      → OpenAI Chat Completions API (tool calling)
        → Middleware chain (scope, rate, UA, destructive guard)
          → Tool execution (shell, http, nuclei, ...)
            → core/ (PrimitiveCache, Budget, Memory, Brain)
```

Agent prompts từ `agents/web/*.md` và `agents/src/*.md` trở thành system prompt cho OpenAI model. Tool calling dùng OpenAI function calling format tự động.

## Sử dụng

### 1. Config

```bash
# Dùng GPT-4o (default)
python sharingan_cli.py config --provider openai --model gpt-4o

# Dùng GPT-4o-mini (rẻ hơn)
python sharingan_cli.py config --provider openai --model gpt-4o-mini

# Dùng o3 (reasoning, chậm hơn nhưng sâu hơn)
python sharingan_cli.py config --provider openai --model o3

# Dùng Azure OpenAI
python sharingan_cli.py config \
  --provider openai \
  --model my-gpt4-deployment \
  --base-url https://my-resource.openai.azure.com/openai/deployments/my-gpt4/
  --api-key "azure-key..."
```

### 2. Tạo scope

```bash
mkdir -p targets/example.com
cat > targets/example.com/scope.json << 'EOF'
{
  "in_scope": ["*.example.com"],
  "out_of_scope": ["admin.example.com"]
}
EOF
```

### 3. Chạy pentest

```bash
python sharingan_cli.py pentest example.com --scope targets/example.com/scope.json
```

### 4. Chạy audit

```bash
python sharingan_cli.py audit /path/to/repo --budget 150
```

### 5. Chạy dual flow

```bash
python sharingan_cli.py dual example.com /path/to/repo \
  --scope targets/example.com/scope.json \
  --budget 200
```

### 6. Override model per-run

```bash
# Pentest bằng o3 (reasoning sâu cho complex targets)
python sharingan_cli.py pentest example.com \
  --provider openai --model o3 --budget 50

# Audit bằng GPT-4o-mini (đủ cho static analysis)
python sharingan_cli.py audit ./repo --provider openai --model gpt-4o-mini
```

## Kết hợp Codex CLI

OpenAI Codex CLI cũng là agent runtime. Có 2 cách dùng:

### Cách 1: Sharingan runtime (khuyến nghị)

Dùng `sharingan_cli.py` — đã có sẵn orchestration, middleware, tools:

```bash
python sharingan_cli.py pentest target.com --provider openai
```

### Cách 2: Codex CLI + Sharingan prompts

Dùng Codex CLI trực tiếp, load Sharingan prompts làm context:

```bash
# Trong Codex CLI session, trỏ tới Sharingan repo
cd /path/to/Sharingan

# Codex đọc CLAUDE.md tự động (tương thích)
# Dùng slash commands nếu Codex hỗ trợ
```

**Lưu ý**: Codex CLI không có hooks system như Claude Code, nên enforcement (scope guard, rate limit, ...) sẽ dựa vào CLAUDE.md instructions thay vì runtime hooks. Dùng cách 1 (sharingan_cli.py) để có enforcement chắc chắn.

## OpenAI-compatible APIs

OpenAIBackend hoạt động với mọi API tương thích OpenAI Chat Completions:

| Service | Config |
|---------|--------|
| **OpenAI** | `--provider openai --model gpt-4o` |
| **Azure OpenAI** | `--provider openai --base-url https://xxx.openai.azure.com/...` |
| **Together AI** | `--provider openai --base-url https://api.together.xyz/v1 --model meta-llama/Llama-3-70b-chat-hf` |
| **Groq** | `--provider openai --base-url https://api.groq.com/openai/v1 --model llama-3.1-70b-versatile` |
| **Fireworks** | `--provider openai --base-url https://api.fireworks.ai/inference/v1 --model accounts/fireworks/models/llama-v3p1-70b-instruct` |

```bash
# Ví dụ: dùng Together AI
export OPENAI_API_KEY="together-key..."
python sharingan_cli.py config \
  --provider openai \
  --model meta-llama/Llama-3-70b-chat-hf \
  --base-url https://api.together.xyz/v1

python sharingan_cli.py pentest target.com
```

## Ưu điểm

- Dùng được GPT-4o, o3, và mọi OpenAI-compatible model
- Tool calling native (function calling format)
- Compatible với Azure, Together, Groq, Fireworks
- Fully automated — không cần user approval cho tool calls
- Middleware enforce scope/rate/UA ở runtime level

## Hạn chế

- Cần API key (có cost)
- GPT-4o context window nhỏ hơn Claude (128K vs 200K)
- Tool calling quality phụ thuộc model — GPT-4o-mini có thể miss complex tool sequences
- Không có MCP server integration (dùng tools trực tiếp qua shell)

## So sánh model cho security tasks

| Model | Recon | Hunting | Source Audit | Cost |
|-------|-------|---------|-------------|------|
| `gpt-4o` | Tốt | Tốt | Tốt | $$$ |
| `gpt-4o-mini` | Tốt | Trung bình | Trung bình | $ |
| `o3` | Rất tốt | Rất tốt | Rất tốt | $$$$ |
| `o3-mini` | Tốt | Tốt | Tốt | $$ |
