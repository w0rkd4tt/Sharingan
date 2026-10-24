#!/usr/bin/env python3
"""PostToolUse hook: audit log for Primitive Cache writes and brain.json changes."""
import json, os, sys, time

LOG_DIR = os.environ.get("SHARINGAN_LOG_DIR", "/tmp/sharingan_audit")

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    tool = data.get("tool_name", "")
    if tool not in ("Bash", "Write", "Edit"):
        return

    tool_input = data.get("tool_input") or {}
    tool_result = data.get("tool_result") or {}

    target_files = []
    if tool == "Write":
        fp = tool_input.get("file_path", "")
        if "primitives.jsonl" in fp or "chains.jsonl" in fp or "brain.json" in fp:
            target_files.append(fp)
    elif tool == "Edit":
        fp = tool_input.get("file_path", "")
        if "primitives.jsonl" in fp or "chains.jsonl" in fp or "brain.json" in fp:
            target_files.append(fp)

    if not target_files:
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, "audit.jsonl")

    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool,
        "files": target_files,
        "agent": os.environ.get("SHARINGAN_AGENT_ID", "unknown"),
    }

    with open(log_file, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

try:
    main()
except Exception:
    pass
sys.exit(0)
