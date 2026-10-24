"""Crawler tools — katana, waybackurls wrappers."""
import asyncio
from .registry import Tool


class KatanaTool(Tool):
    name = "katana"
    description = "Run katana web crawler for URL discovery and JavaScript parsing."
    parameters = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "Target URL"},
            "depth": {"type": "integer", "description": "Crawl depth", "default": 3},
            "js_crawl": {"type": "boolean", "description": "Enable JavaScript parsing", "default": True},
            "rate_limit": {"type": "integer", "default": 10},
        },
        "required": ["target"],
    }

    async def execute(self, args: dict) -> str:
        target = args["target"]
        depth = args.get("depth", 3)
        rate = args.get("rate_limit", 10)
        js = "-jc" if args.get("js_crawl", True) else ""

        cmd = (f"katana -u '{target}' -d {depth} {js} "
               f"-rl {rate} -silent 2>/dev/null | head -500")

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=300)
        return stdout.decode("utf-8", errors="replace") or "(no URLs found)"


class WaybackTool(Tool):
    name = "waybackurls"
    description = "Fetch known URLs from Wayback Machine for a domain."
    parameters = {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "Target domain"},
        },
        "required": ["domain"],
    }

    async def execute(self, args: dict) -> str:
        domain = args["domain"]
        cmd = f"echo '{domain}' | waybackurls 2>/dev/null | sort -u | head -500"

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=120)
        return stdout.decode("utf-8", errors="replace") or "(no URLs found)"
