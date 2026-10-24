#!/usr/bin/env python3
"""PreToolUse hook: block requests to out-of-scope targets.

Reads SCOPE_FILE env var (path to scope.json). If the Bash command targets
a host not in scope, deny the tool call. Loopback and RFC1918 addresses
are always allowed (local infrastructure).
"""
import json, os, re, sys
from urllib.parse import urlparse

LOCAL = re.compile(
    r"(?:^|[/@])(?:localhost|127(?:\.\d+){3}|0\.0\.0\.0|\[::1\]|::1"
    r"|10(?:\.\d+){3}|192\.168(?:\.\d+){2}"
    r"|172\.(?:1[6-9]|2\d|3[01])(?:\.\d+){2}"
    r"|host\.docker\.internal)(?::\d+)?(?:[/\s\"']|$)", re.I)

URL_RE = re.compile(r'https?://[^\s\'"<>]+', re.I)

def load_scope():
    scope_file = os.environ.get("SCOPE_FILE", "")
    if not scope_file or not os.path.exists(scope_file):
        return None
    with open(scope_file, "r") as f:
        return json.load(f)

def extract_hosts(command: str) -> list:
    hosts = []
    for m in URL_RE.finditer(command):
        try:
            parsed = urlparse(m.group())
            if parsed.netloc:
                host = parsed.netloc.split(":")[0].lower()
                if host and not LOCAL.search(m.group()):
                    hosts.append(host)
        except Exception:
            pass
    return hosts

def is_in_scope(host: str, scope: dict) -> bool:
    in_scope = scope.get("in_scope", scope.get("domains", []))
    out_scope = scope.get("out_of_scope", [])

    for pattern in out_scope:
        if isinstance(pattern, dict):
            pattern = pattern.get("asset", pattern.get("domain", ""))
        pattern = pattern.lower().strip()
        if pattern and (host == pattern or host.endswith("." + pattern)):
            return False

    for pattern in in_scope:
        if isinstance(pattern, dict):
            pattern = pattern.get("asset", pattern.get("domain", ""))
        pattern = pattern.lower().strip()
        if pattern.startswith("*."):
            if host.endswith(pattern[1:]) or host == pattern[2:]:
                return True
        elif host == pattern or host.endswith("." + pattern):
            return True

    return len(in_scope) == 0

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

    scope = load_scope()
    if scope is None:
        return

    hosts = extract_hosts(cmd)
    blocked = [h for h in hosts if not is_in_scope(h, scope)]

    if blocked:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason":
                f"SCOPE GUARD: blocked request to out-of-scope host(s): {', '.join(blocked)}. "
                f"Check scope.json or add host to in_scope.",
        }}))

try:
    main()
except Exception:
    pass
sys.exit(0)
