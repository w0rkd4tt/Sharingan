#!/usr/bin/env python3
"""PreToolUse hook: force a real browser User-Agent on every outbound request.

Standing rule for this project: anything that leaves the box towards a target
identifies as Chrome or Firefox. Default scanner UAs (`curl/8.x`,
`Wget/1.21`, `Mozilla/5.0 (nuclei ...)`, `Fuzz Faster U Fool`, `sqlmap/1.9`)
are a free signature for a WAF to block on and make traffic obviously
automated in the client's logs.

Mechanism: PreToolUse supports `updatedInput`, so this rewrites the command
rather than denying it - a deny would just move the work onto the operator.

Scope of the rewrite:
  * Bash commands - a UA flag is inserted after the tool token for curl, wget,
    httpx, nuclei, ffuf, katana, gobuster, feroxbuster, dirsearch, sqlmap,
    ghauri, nikto and whatweb. See NO_FLAG for the ones left alone on purpose.
  * The Python side is handled elsewhere (tools/ua_site/sitecustomize.py on
    PYTHONPATH), so `python3 -c "import requests..."` is already covered and
    this hook leaves it alone.

It does NOT touch:
  * a command that already carries a UA - "unless directly specified" (§)
  * loopback / RFC1918 targets (SiYuan, interactsh, Burp, Pi 5)
  * package managers and VCS (pip, npm, apt, go, git, gh, docker)
  * any command containing the opt-out marker  # ua:keep

Fail-open on anything unexpected: exit 0 and let the original command through.
"""
import json
import os
import re
import shlex
import sys

# ---------------------------------------------------------------- config ----

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, os.pardir, os.pardir,
                      "pentest-agents", "config", "user-agents.json")

FALLBACK_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def load_ua():
    """(user_agent, [extra header strings])."""
    try:
        with open(CONFIG, "r", encoding="utf-8") as fh:
            cfg = json.load(fh)
    except Exception:
        cfg = {}
    env = os.environ.get("PENTEST_UA", "").strip()
    if env:
        ua = env
    else:
        name = (os.environ.get("PENTEST_UA_PROFILE")
                or cfg.get("default_profile") or "chrome")
        ua = (cfg.get("profiles") or {}).get(name) or FALLBACK_UA
    extra = []
    if cfg.get("shell_client_hints") and "Chrome/" in ua and "Firefox/" not in ua:
        extra = ["%s: %s" % (k, v)
                 for k, v in (cfg.get("sec_ch_ua") or {}).items()
                 if not k.startswith("_")]
    return ua, extra


# ----------------------------------------------------------- tool matrix ----
# tool -> template for the flag to insert. {ua} is substituted, then the whole
# thing is placed immediately after the tool token, already shell-quoted.

TOOLS = {
    "curl":        ("-A {q}", None),
    "wget":        ("--user-agent={q}", None),
    "wget2":       ("--user-agent={q}", None),
    "httpx":       ("-H {hq}", None),
    "nuclei":      ("-H {hq}", None),
    "katana":      ("-H {hq}", None),
    "ffuf":        ("-H {hq}", None),
    "feroxbuster": ("-a {q}", None),
    "dirsearch":   ("--user-agent={q}", None),
    "sqlmap":      ("--user-agent={q}", None),
    "ghauri":      ("--user-agent={q}", None),
    "nikto":       ("-useragent {q}", None),
    "whatweb":     ("--user-agent={q}", None),
    # -a exists on the HTTP subcommands only (`gobuster dns` rejects it), and
    # gobuster demands the subcommand first - so the flag goes AFTER it.
    "gobuster":    ("-a {q}", re.compile(r"\s*(dir|vhost|fuzz|s3|gcs)\b")),
}

# Deliberately NOT rewritten - their UA flag is ambiguous or means something
# else, and a wrong flag breaks the command:
#   wafw00f  -H is a path to a headers FILE, not an inline header
#   arjun    --headers semantics vary by version (Python -> sitecustomize covers it)
#   gospider -u is the UA flag but -s is the URL; too easy to corrupt
#   hakrawler -h is help in most builds
#   gau / waybackurls / subfinder / dnsx / naabu / tlsx - passive or non-HTTP
NO_FLAG = {"wafw00f", "arjun", "gospider", "hakrawler", "gau", "waybackurls",
           "subfinder", "dnsx", "naabu", "tlsx", "waymore"}

# Commands that are never target traffic.
NEVER = {
    "pip", "pip3", "npm", "npx", "yarn", "pnpm", "apt", "apt-get", "brew",
    "go", "cargo", "gem", "git", "gh", "docker", "kubectl", "aws", "gcloud",
    "az", "scp", "rsync", "ssh", "python", "python3", "node", "deno", "bun",
    "jq", "grep", "sed", "awk", "cat", "ls", "echo", "mkdir", "cp", "mv",
}

OPT_OUT = re.compile(r"#\s*ua:keep", re.I)

# An existing UA in any form -> leave the segment alone.
HAS_UA = re.compile(
    r"(^|\s)(-A|--user-agent|-useragent|--useragent|--random-agent|--ua)(=|\s)"
    r"|user[-_]agent\s*[:=]"
    r"|(^|\s)-a\s+[\"']?Mozilla",
    re.I)

# Local / private infrastructure: a browser UA buys nothing there.
LOCAL = re.compile(
    r"(?:^|[/@])(?:localhost|127(?:\.\d+){3}|0\.0\.0\.0|\[::1\]|::1"
    r"|10(?:\.\d+){3}|192\.168(?:\.\d+){2}"
    r"|172\.(?:1[6-9]|2\d|3[01])(?:\.\d+){2}"
    r"|host\.docker\.internal)(?::\d+)?(?:[/\s\"']|$)",
    re.I)

# curl reading flags from a file - we cannot see what is in it, so do not guess.
CURL_CONFIG = re.compile(r"(^|\s)(-K|--config)(=|\s)")

SPLIT = re.compile(r"(\|\||&&|[;|&\n]|\$\(|\)|`)")

HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def inert_spans(cmd: str):
    """Byte ranges that are text, not shell code: heredoc bodies and
    single-quoted strings.

    Without this the hook rewrites shell-looking text inside a heredoc - e.g. a
    `curl -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'` line in a Python script being written to disk - and corrupts the
    literal it was sitting in. (Observed: this hook broke its own installer.)
    """
    spans = []
    for m in HEREDOC.finditer(cmd):
        nl = cmd.find("\n", m.end())
        if nl == -1:
            continue
        term = re.compile(r"^\s*" + re.escape(m.group(2)) + r"\s*$", re.M)
        t = term.search(cmd, nl + 1)
        spans.append((nl + 1, t.start() if t else len(cmd)))

    def covered(i):
        return any(a <= i < b for a, b in spans)

    i, n = 0, len(cmd)
    while i < n:
        c = cmd[i]
        if c == "\\":
            i += 2
            continue
        if c == "'" and not covered(i):
            j = cmd.find("'", i + 1)
            if j == -1:
                break
            spans.append((i, j + 1))
            i = j + 1
            continue
        i += 1
    return spans


def has_ua(segment: str) -> bool:
    if HAS_UA.search(segment):
        return True
    # -H/--header carrying a User-Agent, in any quoting style
    for m in re.finditer(r"(?:-H|--header)(?:=|\s+)(\"[^\"]*\"|'[^']*'|\S+)", segment):
        if "user-agent" in m.group(1).lower():
            return True
    return False


def first_token(segment: str):
    """(basename, end_offset) of the command word, skipping VAR=x prefixes and
    wrappers like sudo / env / timeout / nohup / stdbuf."""
    pos = 0
    wrappers = {"sudo", "env", "nohup", "stdbuf", "nice", "ionice", "time",
                "timeout", "proxychains", "proxychains4", "command", "exec",
                "xargs"}
    # Shell keywords that can sit in front of a real command position.
    keywords = {"do", "then", "else", "elif", "if", "for", "while", "until",
                "!", "{", "("}
    while True:
        m = re.compile(r"\s*").match(segment, pos)
        pos = m.end()
        m = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S*)\s+").match(segment, pos)
        if m:
            pos = m.end()
            continue
        m = re.compile(r"(\S+)").match(segment, pos)
        if not m:
            return None, None
        tok = m.group(1)
        base = os.path.basename(tok.strip("\"'"))
        if base in keywords:
            pos = m.end()
            continue
        if base in wrappers:
            pos = m.end()
            # skip a flag-ish argument of the wrapper (e.g. `timeout 30`)
            m2 = re.compile(r"\s+(-\S+|\d+[smhd]?)").match(segment, pos)
            if m2:
                pos = m2.end()
            continue
        return base, m.end()


def rewrite_segment(seg: str, ua: str, extra):
    base, end = first_token(seg)
    if not base:
        return seg, None
    base = base.split(".")[0] if base.endswith((".exe", ".sh")) else base
    if base in NEVER:
        return seg, None
    entry = TOOLS.get(base)
    if not entry:
        return seg, None
    tmpl, guard = entry
    if guard is not None:
        # Anchored at the token right after the tool name (pattern.match(s, pos)
        # anchors at pos - do NOT put a ^ in the guard, that binds to string start).
        # It both vets the subcommand and moves the insertion point past it.
        m = guard.match(seg, end)
        if not m:
            return seg, None
        end = m.end()
    if has_ua(seg):
        return seg, None
    if base == "curl" and CURL_CONFIG.search(seg):
        return seg, None
    if LOCAL.search(seg):
        return seg, None

    flag = tmpl.format(q=shlex.quote(ua), hq=shlex.quote("User-Agent: " + ua))
    if extra:
        if "{hq}" in tmpl:                      # -H style: repeat the flag
            hflag = tmpl.split()[0]
            flag += "".join(" %s %s" % (hflag, shlex.quote(h)) for h in extra)
        elif base in ("curl", "wget", "wget2"):  # these take -H/--header too
            hflag = "-H" if base == "curl" else "--header="
            sep = " " if base == "curl" else ""
            flag += "".join(" %s%s%s" % (hflag, sep, shlex.quote(h)) for h in extra)
    return seg[:end] + " " + flag + seg[end:], base


def rewrite(command: str, ua: str, extra):
    """Split on shell operators, rewrite each command position, reassemble.

    Segments that start inside a heredoc body or a single-quoted string are
    text, not commands, and are left exactly as written.
    """
    inert = inert_spans(command)

    def is_inert(i):
        return any(a <= i < b for a, b in inert)

    parts = SPLIT.split(command)
    touched = []
    offset = 0
    for i, part in enumerate(parts):
        if i % 2 == 0:                          # even indices are segments
            lead = len(part) - len(part.lstrip())
            if not is_inert(offset + lead):
                new, tool = rewrite_segment(part, ua, extra)
                if tool:
                    parts[i] = new
                    touched.append(tool)
        offset += len(part)
    return "".join(parts), touched


# ------------------------------------------------------------------ main ----

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    if data.get("tool_name") != "Bash":
        return

    ti = data.get("tool_input") or {}
    cmd = ti.get("command")
    if not isinstance(cmd, str) or not cmd.strip():
        return
    if OPT_OUT.search(cmd):
        return

    ua, extra = load_ua()
    new_cmd, touched = rewrite(cmd, ua, extra)
    if not touched or new_cmd == cmd:
        return

    updated = dict(ti)
    updated["command"] = new_cmd
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason":
            "Browser User-Agent forced on: " + ", ".join(sorted(set(touched)))
            + " (project rule; bypass this command with '# ua:keep')",
        "updatedInput": updated,
    }}))


try:
    main()
except Exception:
    pass
sys.exit(0)
