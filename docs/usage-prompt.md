# Sharingan + Prompt (Claude.ai / ChatGPT / bất kỳ LLM)

Kích hoạt Sharingan bằng prompt — không cần cài đặt, không cần CLI, không cần API key. Paste prompt vào bất kỳ LLM chat nào là dùng được.

## Cách hoạt động

Thay vì agent tự chạy tools (như runtime layer), **prompt mode** hoạt động interactive:

```
User paste prompt → Claude hiểu role + rules
User nói target   → Claude hướng dẫn từng bước
User chạy lệnh    → paste output lại cho Claude
Claude phân tích   → đề xuất bước tiếp theo
Lặp lại            → đến khi xong assessment
```

Claude đóng vai **Coordinator** — lên kế hoạch, phân tích, tổng hợp. User đóng vai **Tool Executor** — chạy commands mà Claude yêu cầu.

## 4 prompt levels

| Prompt | File | Dùng cho | Độ dài |
|--------|------|----------|--------|
| **Quick Hunt** | [quick-hunt.md](prompts/quick-hunt.md) | Quick check, context nhỏ, mọi LLM | ~50 dòng |
| **Web Pentest** | [pentest-web.md](prompts/pentest-web.md) | Full web pentest pipeline | ~130 dòng |
| **Source Audit** | [audit-src.md](prompts/audit-src.md) | Full whitebox source audit | ~130 dòng |
| **Coordinator** | [coordinator-full.md](prompts/coordinator-full.md) | Dual flow (web + src + cross-flow) | ~200 dòng |

## Sử dụng

### Cách 1: Claude.ai (đơn giản nhất)

1. Mở [claude.ai](https://claude.ai)
2. Copy nội dung prompt file (vd: `prompts/pentest-web.md`)
3. Paste vào ô chat
4. Gửi tiếp message đầu tiên:

```
TARGET: example.com
SCOPE: *.example.com
```

5. Claude sẽ bắt đầu hướng dẫn chạy từng command
6. Chạy command trong terminal, paste output lại
7. Lặp lại đến khi xong

### Cách 2: Claude.ai Projects (persistent)

1. Tạo Project mới trên claude.ai
2. Thêm prompt file vào **Project Knowledge**
3. Mỗi conversation trong project tự động có Sharingan context
4. Không cần paste lại prompt mỗi lần

### Cách 3: Claude API (system prompt)

```python
import anthropic

client = anthropic.Anthropic()

# Đọc prompt file
with open("docs/prompts/pentest-web.md") as f:
    system_prompt = f.read()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=system_prompt,
    messages=[{
        "role": "user",
        "content": "TARGET: example.com\nSCOPE: *.example.com"
    }],
)
print(response.content[0].text)
```

### Cách 4: ChatGPT / GPT-4

Prompt tương thích với mọi LLM hỗ trợ chat. Paste vào:
- ChatGPT (chat.openai.com)
- GPT-4 API (system message)
- Custom GPT (Instructions field)

### Cách 5: Local model (Ollama + Open WebUI)

1. Cài [Open WebUI](https://github.com/open-webui/open-webui)
2. Tạo **Model** mới, paste prompt vào System Prompt
3. Chat với local model có Sharingan personality

```bash
# Hoặc dùng Ollama CLI trực tiếp
ollama run llama3.1 "$(cat docs/prompts/quick-hunt.md)

TARGET: my-app.local
SCOPE: *.my-app.local"
```

## Ví dụ session

### Web Pentest

```
User: [paste pentest-web.md prompt]

User: TARGET: testphp.vulnweb.com SCOPE: *.vulnweb.com

Claude: Starting Phase 1 — Recon.
  RUN: httpx -u testphp.vulnweb.com -tech-detect -status-code -title -silent
  WHY: Identify technology stack and verify target is alive

User: [paste output]
  testphp.vulnweb.com [200] [Acunetix] [PHP/5.6.40, Apache/2.4.7]

Claude: BRAIN UPDATE:
  - tech_stack: [PHP 5.6.40, Apache 2.4.7]
  - note: PHP 5.6 is EOL — high chance of known vulns
  
  Next:
  RUN: katana -u http://testphp.vulnweb.com -d 3 -jc -silent
  WHY: Discover all endpoints and parameters

User: [paste output]
  http://testphp.vulnweb.com/login.php
  http://testphp.vulnweb.com/search.php?test=query
  http://testphp.vulnweb.com/artists.php?artist=1
  ...

Claude: Found 3 interesting endpoints with parameters. Moving to Phase 3.
  
  HUNT [round 1] [sqli]:
  Endpoint: /artists.php?artist=1
  Test: SQL injection via integer parameter
  RUN: sqlmap -u "http://testphp.vulnweb.com/artists.php?artist=1" --batch --level 3 --random-agent
  WHY: Integer param in query — classic SQLi target
```

### Source Audit

```
User: [paste audit-src.md prompt]

User: AUDIT this Flask app:
  [paste app.py code]

Claude: ATTACK SURFACE:
  - Language: Python/Flask
  - Entry points: 4 routes (/login, /search, /upload, /profile/<id>)
  - Auth: session-based, no CSRF protection visible
  - Database: SQLite via raw cursor.execute()
  
  NEED FILE: templates/ (to check XSS in rendered templates)
  
  Finding during initial scan:
  
  ## [HIGH] SQLi — Raw SQL in search endpoint
  
  **Class:** sqli
  **Location:** app.py:34
  **Evidence:** READ
  
  ### Vulnerable Code
  ```python
  @app.route('/search')
  def search():
      q = request.args.get('q')
      cursor.execute(f"SELECT * FROM products WHERE name LIKE '%{q}%'")
  ```
  
  ### Taint Trace
  1. request.args.get('q') — user input SOURCE
  2. f-string into SQL — NO sanitization
  3. cursor.execute() — SQL SINK
  
  ### Fix
  cursor.execute("SELECT * FROM products WHERE name LIKE ?", [f"%{q}%"])
```

## So sánh Prompt Mode vs Runtime Mode

| Tiêu chí | Prompt Mode | Runtime Mode (CLI) |
|----------|-------------|-------------------|
| **Setup** | Zero — paste prompt | Cài Python + dependencies |
| **Tự động** | Semi-manual (user chạy commands) | Full auto (agent chạy tools) |
| **Enforcement** | Rules trong prompt (có thể bypass) | Middleware code (không bypass được) |
| **Model** | Bất kỳ LLM nào | Anthropic / OpenAI / Ollama |
| **Cost** | Tuỳ model (Claude.ai free tier ok) | API cost |
| **Best for** | Quick check, learning, demo | Production assessment |
| **Scope guard** | Dựa vào rules trong prompt | Code-enforced middleware |
| **Rate limit** | User tự control | Token-bucket tự động |
| **Audit log** | Không | JSONL audit trail |

## Tips

- **Quick Hunt** đủ cho 80% use cases. Dùng prompt dài hơn khi cần systematic assessment.
- Dùng **Claude.ai Projects** để không phải paste prompt lại mỗi lần.
- Với **Claude.ai**, upload code files trực tiếp (kéo thả) thay vì paste — giữ được file structure.
- Kết hợp: dùng **Prompt Mode** để plan, rồi switch sang **Runtime Mode** để execute.
- Prompts tương thích với **Claude, GPT-4, Llama 3.1, Qwen, DeepSeek** — bất kỳ model nào hiểu tool-use instructions.

## Khi nào dùng Prompt Mode vs CLI

| Tình huống | Nên dùng |
|-----------|----------|
| Quick security review 1 file | Prompt (Quick Hunt) |
| Bug bounty target mới | Prompt (Pentest) → nếu tìm được gì → CLI cho deep dive |
| Full code audit trước release | CLI (audit) — systematic, tracked |
| Demo cho team | Prompt — dễ show, không cần setup |
| CI/CD integration | CLI (Python API) |
| Offline / air-gapped | CLI + Local model |
| Đang mobile / không có terminal | Prompt (Claude.ai trên phone) |
