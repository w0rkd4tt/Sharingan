# Sharingan + Local Models

Sử dụng Sharingan hoàn toàn offline với local LLM — Ollama, vLLM, llama.cpp, LM Studio. Không cần API key, không gửi data ra ngoài.

## Tại sao dùng local model?

- **Bảo mật**: Source code và findings không rời máy
- **Không giới hạn**: Không rate limit, không cost per token
- **Offline**: Hoạt động không cần internet (sau khi tải model)
- **Custom**: Fine-tune model cho security domain

## Yêu cầu

### Phần cứng tối thiểu

| Model size | RAM | VRAM (GPU) | Disk |
|-----------|-----|------------|------|
| 7-8B (Llama 3.1 8B) | 16GB | 8GB | 5GB |
| 13B (CodeLlama 13B) | 32GB | 16GB | 8GB |
| 70B (Llama 3.1 70B) | 64GB+ | 48GB+ (hoặc CPU) | 40GB |

### Phần mềm

- Python 3.10+
- Một trong các inference servers:
  - [Ollama](https://ollama.ai) (dễ nhất)
  - [vLLM](https://github.com/vllm-project/vllm) (nhanh nhất)
  - [llama.cpp](https://github.com/ggml-org/llama.cpp) (nhẹ nhất)
  - [LM Studio](https://lmstudio.ai) (GUI)

## Cài đặt

### Option A: Ollama (khuyến nghị cho beginners)

```bash
# Cài Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Tải model
ollama pull llama3.1          # 8B — đủ cho recon + basic hunting
ollama pull llama3.1:70b      # 70B — mạnh hơn, cần nhiều RAM
ollama pull deepseek-coder-v2 # code-specialized — tốt cho audit flow
ollama pull qwen2.5-coder:32b # code-specialized — balance tốt

# Verify
ollama list
ollama run llama3.1 "Hello"
```

### Option B: vLLM (nhanh nhất, cần GPU)

```bash
pip install vllm

# Chạy server
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --port 8000 \
  --max-model-len 32768 \
  --enable-auto-tool-choice \
  --tool-call-parser llama3_json
```

### Option C: llama.cpp (CPU-friendly)

```bash
# Build
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp && make -j

# Tải GGUF model
# (từ HuggingFace, chọn Q4_K_M hoặc Q5_K_M quantization)

# Chạy server (OpenAI-compatible)
./llama-server \
  -m models/llama-3.1-8b-instruct-q5_k_m.gguf \
  --port 8000 \
  -c 32768 \
  -ngl 35  # số GPU layers
```

### Option D: LM Studio (GUI)

1. Tải [LM Studio](https://lmstudio.ai)
2. Search và tải model (vd: `Meta Llama 3.1 8B Instruct`)
3. Start local server (tab "Local Server") → mặc định port 1234
4. Enable "Tool Use" trong server settings

## Config Sharingan

### Ollama (native API)

```bash
python sharingan_cli.py config \
  --provider ollama \
  --model llama3.1
```

Mặc định kết nối `http://localhost:11434`. Nếu Ollama chạy ở port/host khác:

```bash
python sharingan_cli.py config \
  --provider ollama \
  --model llama3.1 \
  --base-url http://192.168.1.100:11434
```

### vLLM / llama.cpp / LM Studio (OpenAI-compatible)

Các server này expose OpenAI-compatible API. Dùng Ollama backend ở chế độ `openai_compat`:

```python
# Python API
from runtime.llm.ollama_backend import OllamaBackend

llm = OllamaBackend(
    model="meta-llama/Llama-3.1-8B-Instruct",
    base_url="http://localhost:8000",  # vLLM/llama.cpp port
    mode="openai_compat",              # dùng /v1/chat/completions
)
```

Hoặc dùng OpenAI backend trực tiếp:

```bash
python sharingan_cli.py config \
  --provider openai \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --base-url http://localhost:8000/v1 \
  --api-key "not-needed"
```

## Sử dụng

### Pentest

```bash
# Tạo scope
mkdir -p targets/my-app
cat > targets/my-app/scope.json << 'EOF'
{"in_scope": ["*.my-app.local"], "out_of_scope": []}
EOF

# Chạy pentest (local model)
python sharingan_cli.py pentest my-app \
  --scope targets/my-app/scope.json \
  --provider ollama \
  --model llama3.1 \
  --budget 50
```

### Audit

```bash
python sharingan_cli.py audit ./my-project \
  --provider ollama \
  --model deepseek-coder-v2 \
  --budget 80
```

### Dual

```bash
python sharingan_cli.py dual my-app ./my-project \
  --scope targets/my-app/scope.json \
  --provider ollama \
  --model qwen2.5-coder:32b \
  --budget 150
```

## Model khuyến nghị theo task

### Web Pentest Flow

| Phase | Model khuyến nghị | Lý do |
|-------|-------------------|-------|
| Recon | `llama3.1` (8B) | Đơn giản, chỉ cần enumerate |
| Mapping | `llama3.1` (8B) | Crawl + parse, không cần reasoning sâu |
| Hunting | `qwen2.5-coder:32b` hoặc `llama3.1:70b` | Cần hiểu logic vuln, tool chaining |
| Exploitation | `llama3.1:70b` | Cần reasoning chain dài |
| Reporting | `llama3.1` (8B) | Template-based, đơn giản |

### Source Audit Flow

| Phase | Model khuyến nghị | Lý do |
|-------|-------------------|-------|
| Recon | `llama3.1` (8B) | File listing + language detection |
| Normalize | `deepseek-coder-v2` | Code parsing cần code-specialized model |
| Graph | `deepseek-coder-v2` | Data flow analysis |
| Hunting | `qwen2.5-coder:32b` | Hiểu sink/source, taint analysis |
| Reporting | `llama3.1` (8B) | Tổng hợp + format |

### Multi-model pipeline (nâng cao)

```python
from runtime.llm import create_backend
from runtime.agent import Agent, load_prompt
from runtime.tools.registry import ToolRegistry

# Model nhẹ cho recon
llm_light = create_backend("ollama", model="llama3.1")
# Model mạnh cho hunting
llm_heavy = create_backend("ollama", model="qwen2.5-coder:32b")

registry = ToolRegistry()
tools = registry.create_pentest_tools(".")

# Recon agent dùng model nhẹ
recon = Agent("recon", load_prompt("agents/web/recon-web.md"), llm_light, tools)
await recon.run("Enumerate attack surface for my-app.local")

# Hunter agent dùng model mạnh
hunter = Agent("hunter", load_prompt("agents/web/hunter-web.md"), llm_heavy, tools)
await hunter.run("Hunt for SSRF and IDOR vulnerabilities")
```

## Troubleshooting

### Model không hỗ trợ tool calling

Một số model cũ không hỗ trợ tool/function calling. Dấu hiệu: agent không gọi tools, chỉ output text.

**Fix**: Dùng model có tool calling support:
- Ollama: `llama3.1`, `qwen2.5-coder`, `mistral-large`
- vLLM: thêm `--enable-auto-tool-choice --tool-call-parser llama3_json`

### Out of memory

```
Error: CUDA out of memory
```

**Fix**:
- Dùng model nhỏ hơn: `llama3.1` (8B) thay vì 70B
- Dùng quantized model: Q4_K_M thay vì Q8
- Giảm context: `--max-model-len 16384` (vLLM)
- Dùng CPU offloading: `-ngl 20` thay vì `-ngl 99` (llama.cpp)

### Response quá chậm

**Fix**:
- Dùng GPU inference thay CPU
- vLLM nhanh hơn Ollama cho batch requests
- Giảm `max_tokens` trong config
- Dùng model nhỏ hơn cho recon/report phases

### Tool calls bị parse sai

Một số model output tool call format không chuẩn.

**Fix**:
- Dùng `llama3.1` hoặc `qwen2.5-coder` — tool calling ổn định nhất
- Nếu dùng vLLM, đảm bảo `--tool-call-parser` match model family
- Giảm `temperature` xuống 0.0 (mặc định)

## Ưu điểm

- **100% offline** — source code không rời máy
- **Không cost** — không API fee
- **Không rate limit** — chạy bao nhiêu tuỳ ý
- **Privacy** — phù hợp cho proprietary code audit
- **Customizable** — có thể fine-tune model cho security tasks

## Hạn chế

- **Quality thấp hơn** cloud models (GPT-4o, Claude) — đặc biệt cho complex reasoning
- **Tool calling** không ổn định bằng API models
- **Cần hardware** — GPU mạnh cho model lớn
- **Chậm hơn** — local inference chậm hơn cloud API
- **Context window** nhỏ hơn — hầu hết local models chỉ 32K-128K tokens

## So sánh tổng quan

| Tiêu chí | Ollama | vLLM | llama.cpp | LM Studio |
|----------|--------|------|-----------|-----------|
| Setup | Dễ | Trung bình | Khó | Rất dễ |
| Tốc độ | Trung bình | Nhanh | Chậm (CPU) | Trung bình |
| GPU support | Có | Có (cần) | Tuỳ chọn | Có |
| Tool calling | Có | Có | Có (server) | Có |
| API format | Ollama native | OpenAI-compat | OpenAI-compat | OpenAI-compat |
| Best for | Dev/testing | Production | Low-resource | Beginners |
