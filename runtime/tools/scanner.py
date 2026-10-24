"""Scanner tools — nuclei, ffuf wrappers."""
import asyncio
import json
from .registry import Tool


class NucleiTool(Tool):
    name = "nuclei"
    description = "Run nuclei vulnerability scanner against a target URL or list."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Target URL or file with URLs"},
            "templates": {"type": "string", "description": "Template tags or paths (e.g. 'cve,sqli')", "default": ""},
            "severity": {"type": "string", "description": "Severity filter (e.g. 'critical,high')", "default": ""},
            "rate_limit": {"type": "integer", "description": "Requests per second", "default": 10},
        },
        "required": ["target"],
    }

    async def execute(self, args: dict) -> str:
        target = args["target"]
        cmd = f"nuclei -u '{target}' -silent -json"

        if args.get("templates"):
            cmd += f" -tags '{args['templates']}'"
        if args.get("severity"):
            cmd += f" -severity '{args['severity']}'"
        cmd += f" -rate-limit {args.get('rate_limit', 10)}"
        cmd += " 2>/dev/null | head -50"

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        result = stdout.decode("utf-8", errors="replace")
        return result or "(no findings)"


class FfufTool(Tool):
    name = "ffuf"
    description = "Run ffuf web fuzzer for directory/parameter discovery."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Target URL with FUZZ keyword"},
            "wordlist": {"type": "string", "description": "Path to wordlist"},
            "method": {"type": "string", "default": "GET"},
            "rate": {"type": "integer", "description": "Requests per second", "default": 10},
            "mc": {"type": "string", "description": "Match HTTP codes (e.g. '200,301,403')", "default": "200,301,302,403"},
        },
        "required": ["url", "wordlist"],
    }

    async def execute(self, args: dict) -> str:
        url = args["url"]
        wordlist = args["wordlist"]
        method = args.get("method", "GET")
        rate = args.get("rate", 10)
        mc = args.get("mc", "200,301,302,403")

        cmd = (f"ffuf -u '{url}' -w '{wordlist}' -X {method} "
               f"-rate {rate} -mc {mc} -json -silent 2>/dev/null | head -100")

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        return stdout.decode("utf-8", errors="replace") or "(no results)"
