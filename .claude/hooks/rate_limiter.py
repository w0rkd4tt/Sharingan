#!/usr/bin/env python3
"""PreToolUse hook: token-bucket rate limiter for outbound requests.

Prevents WAF triggers by limiting requests per second. Reads RATE_LIMIT_RPS
from env (default 10). State stored in /tmp/sharingan_rate_state.json.
"""
import json, os, sys, time, re

STATE_FILE = "/tmp/sharingan_rate_state.json"
URL_RE = re.compile(r'https?://[^\s\'"<>]+', re.I)
LOCAL = re.compile(
    r"(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[?::1\]?"
    r"|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[01])\.\d+\.\d+)", re.I)

NEVER_LIMIT = {"pip", "pip3", "npm", "git", "gh", "docker", "kubectl",
               "python", "python3", "node", "grep", "find", "ls", "cat"}

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    if data.get("tool_name") != "Bash":
        return

    cmd = (data.get("tool_input") or {}).get("command", "")
    if not cmd.strip():
        return

    first_word = cmd.strip().split()[0].split("/")[-1] if cmd.strip() else ""
    if first_word in NEVER_LIMIT:
        return

    if not URL_RE.search(cmd):
        return

    urls = URL_RE.findall(cmd)
    if all(LOCAL.search(u) for u in urls):
        return

    rps = int(os.environ.get("RATE_LIMIT_RPS", "10"))
    now = time.time()

    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except Exception:
        state = {"tokens": rps, "last": now}

    elapsed = now - state.get("last", now)
    tokens = min(rps, state.get("tokens", rps) + elapsed * rps)

    if tokens < 1:
        wait = (1 - tokens) / rps
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason":
                f"RATE LIMITER: too many requests. Wait {wait:.1f}s. "
                f"Current rate: {rps} RPS. Set RATE_LIMIT_RPS to adjust.",
        }}))
        return

    tokens -= 1
    with open(STATE_FILE, "w") as f:
        json.dump({"tokens": tokens, "last": now}, f)

try:
    main()
except Exception:
    pass
sys.exit(0)
