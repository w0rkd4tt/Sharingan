# Sharingan + Claude Code

Sử dụng Sharingan trực tiếp trong Claude Code (CLI/Desktop/IDE) — agent hoạt động qua slash commands, hooks tự động enforce scope/rate/UA.

## Yêu cầu

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) đã cài đặt
- Python 3.10+
- Các external tools cần thiết (tuỳ flow):
  - Web flow: `katana`, `waybackurls`, `nuclei`, `ffuf`, `httpx`
  - Src flow: `semgrep` (hoặc `codeql`)

## Cài đặt

```bash
git clone https://github.com/w0rkd4tt/Sharingan.git
cd Sharingan
pip install -r requirements-runtime.txt
```

Không cần config thêm — Claude Code đọc `.claude/settings.json` và `.mcp.json` tự động.

## Cách hoạt động

Claude Code chạy Sharingan qua 3 thành phần:

| Thành phần | Vai trò |
|------------|---------|
| **Slash commands** (`.claude/commands/`) | Trigger flow — `/pentest`, `/audit`, `/dual` |
| **Hooks** (`.claude/hooks/`) | Enforce runtime — scope guard, UA, rate limit, destructive guard |
| **Agent prompts** (`agents/`) | System prompt cho từng role — recon, mapper, hunter, reporter |

### Luồng dữ liệu

```
User → /pentest target → Claude Code
  → loads agents/web/*.md prompts
  → hooks intercept mỗi tool call:
      scope_guard.py    → chặn out-of-scope
      force_user_agent.py → inject Chrome UA
      rate_limiter.py   → token-bucket RPS
      destructive_guard.py → chặn rm -rf, sqlmap --os-shell
  → agent thực thi tools (Bash, curl, nuclei, ...)
  → finding_logger.py ghi audit log
  → kết quả → targets/<TARGET>/cache/primitives.jsonl
```

## Sử dụng

### 1. Tạo scope cho target

```bash
mkdir -p targets/example.com
cat > targets/example.com/scope.json << 'EOF'
{
  "in_scope": ["*.example.com"],
  "out_of_scope": ["admin.example.com"],
  "notes": "Bug bounty program"
}
EOF
```

### 2. Chạy pentest (web blackbox)

Trong Claude Code terminal:

```
/pentest example.com
```

Claude Code sẽ:
1. Load scope + brain (nếu có session cũ)
2. Spawn recon-web → mapper → hunter(s) → exploiter → reporter
3. Ghi findings vào `targets/example.com/cache/primitives.jsonl`
4. Output report

### 3. Chạy audit (whitebox source)

```
/audit /path/to/repo
```

Pipeline: recon-src → normalize → graph → hunter-src(s) → reporter-src

### 4. Chạy dual flow

```
/dual example.com /path/to/repo
```

Chạy cả web + src song song, cross-flow bridge tìm DUAL-CONFIRMED findings.

### 5. Các command khác

| Command | Mô tả |
|---------|-------|
| `/attack-tree` | Vẽ attack tree từ findings |
| `/attack-coverage` | Báo cáo coverage theo vuln family |
| `/brain-sync` | Sync brain.json lên SiYuan |
| `/0day` | Deep-dive hunting 0day targets |

## Enforcement (tự động, không bypass được)

Hooks chạy ở **PreToolUse** — trước MỌI tool call:

| Hook | File | Hành vi |
|------|------|---------|
| Scope Guard | `.claude/hooks/scope_guard.py` | Chặn request tới host ngoài scope.json |
| Browser UA | `.claude/hooks/force_user_agent.py` | Inject Chrome UA cho mọi HTTP request |
| Rate Limiter | `.claude/hooks/rate_limiter.py` | Token-bucket, default 10 RPS |
| Email Guard | `.claude/hooks/block_platform_emails.py` | Chặn gửi email (RoE enforcement) |
| Destructive Guard | `.claude/hooks/destructive_guard.py` | Chặn `rm -rf`, `sqlmap --os-shell`, `msfconsole`, ... |
| Audit Logger | `.claude/hooks/finding_logger.py` | PostToolUse — log mọi cache/brain write |

## MCP Servers

Claude Code kết nối 4 MCP servers (config trong `.mcp.json`):

| Server | Mô tả |
|--------|-------|
| `pentest-tools` | Wrapper cho nuclei, ffuf, katana, httpx |
| `siyuan-brain` | Sync findings với SiYuan Notes |
| `burp-proxy` | Proxy qua Burp Suite REST API |
| `code-analysis` | Semgrep + CodeQL integration |

## Ưu điểm

- **Zero config** — clone repo, chạy `/pentest`, hooks tự enforce
- **Full context** — Claude Code giữ context dài, hiểu codebase
- **Interactive** — hỏi thêm thông tin, điều chỉnh strategy realtime
- **MCP integration** — kết nối Burp, SiYuan, code analysis tools

## Hạn chế

- Chỉ dùng được model Claude (Anthropic)
- Cần Claude Code license
- Không tự động hoá hoàn toàn (cần user approve một số tool calls)
- Session state phụ thuộc Claude Code context window

## Tips

- Dùng `/pentest` cho bug bounty targets đã có scope
- Dùng `/audit` cho code review trước merge
- Dùng `/dual` khi có cả source code + live instance
- Check `targets/<TARGET>/cache/primitives.jsonl` để xem raw findings
- Dùng `/brain-sync` để lưu findings vào SiYuan cho cross-session
