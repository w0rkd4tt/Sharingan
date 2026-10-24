#!/usr/bin/env python3
"""PreToolUse hook: block destructive commands for both web and whitebox flows."""
import json, re, sys

DENY_PATTERNS = [
    (r"\brm\s+(-[rR]f|--recursive)\s+/", "recursive delete of root"),
    (r"\bdd\s+if=", "raw disk write"),
    (r"\bmkfs\b", "filesystem format"),
    (r"\bshutdown\b", "system shutdown"),
    (r"\breboot\b", "system reboot"),
    (r"\bsqlmap\b.*--dump-all\b", "sqlmap full dump"),
    (r"\bsqlmap\b.*--os-shell\b", "sqlmap OS shell"),
    (r"\bsqlmap\b.*--file-write\b", "sqlmap file write"),
    (r"\bsqlmap\b.*--file-read\b", "sqlmap file read"),
    (r"\bmsfconsole\b", "metasploit console"),
    (r"\bmsfvenom\b", "metasploit payload generator"),
    (r"\b:(){ :\|:& };:", "fork bomb"),
    (r"\b>\s*/dev/sd[a-z]", "raw device write"),
]

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

    for pattern, desc in DENY_PATTERNS:
        if re.search(pattern, cmd, re.I):
            print(json.dumps({"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    f"DESTRUCTIVE GUARD: blocked '{desc}'. "
                    f"This command is on the deny list for safety.",
            }}))
            return

try:
    main()
except Exception:
    pass
sys.exit(0)
