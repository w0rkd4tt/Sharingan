#!/usr/bin/env python3
"""MCP Server: Code Analysis tools (CodeQL, semgrep wrappers).

Provides tools for the whitebox flow to run static analysis queries.
"""
import json
import os
import subprocess
import sys

CODEQL_HOME = os.environ.get("CODEQL_HOME", "")
SEMGREP_RULES = os.environ.get("SEMGREP_RULES", "p/security-audit")


def run_semgrep(target_path: str, rules: str = "", lang: str = "") -> dict:
    """Run semgrep on target path with specified rules."""
    cmd = ["semgrep", "--json", "--config", rules or SEMGREP_RULES]
    if lang:
        cmd.extend(["--lang", lang])
    cmd.append(target_path)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return json.loads(result.stdout) if result.stdout else {"results": [], "errors": [result.stderr]}
    except subprocess.TimeoutExpired:
        return {"error": "semgrep timed out after 300s"}
    except FileNotFoundError:
        return {"error": "semgrep not installed"}
    except Exception as e:
        return {"error": str(e)}


def run_codeql_query(database: str, query: str) -> dict:
    """Run a CodeQL query on a database."""
    if not CODEQL_HOME:
        return {"error": "CODEQL_HOME not set"}

    codeql = os.path.join(CODEQL_HOME, "codeql")
    cmd = [codeql, "query", "run", "--database", database, query]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
    except Exception as e:
        return {"error": str(e)}


def list_languages(target_path: str) -> list:
    """Detect languages in a repository."""
    extensions = {}
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'venv', '__pycache__', '.tox')]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1

    lang_map = {
        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
        '.java': 'java', '.go': 'go', '.rb': 'ruby',
        '.php': 'php', '.cs': 'csharp', '.rs': 'rust',
        '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala',
    }

    detected = []
    for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
        if ext in lang_map and count >= 3:
            detected.append({"language": lang_map[ext], "extension": ext, "file_count": count})

    return detected


if __name__ == "__main__":
    print(json.dumps({
        "name": "code-analysis",
        "version": "0.1.0",
        "tools": [
            {"name": "semgrep_scan", "description": "Run semgrep security scan"},
            {"name": "codeql_query", "description": "Run CodeQL query"},
            {"name": "detect_languages", "description": "Detect repository languages"},
        ]
    }))
