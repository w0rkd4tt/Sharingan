"""File operation tools — read, write, list, grep."""
import asyncio
import os
import re
from .registry import Tool


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read contents of a file. Returns the file text with line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"},
            "offset": {"type": "integer", "description": "Start line (0-indexed)", "default": 0},
            "limit": {"type": "integer", "description": "Max lines to read", "default": 500},
        },
        "required": ["path"],
    }

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def execute(self, args: dict) -> str:
        path = args["path"]
        if not os.path.isabs(path):
            path = os.path.join(self.working_dir, path)

        if not os.path.exists(path):
            return f'{{"error": "File not found: {path}"}}'

        offset = args.get("offset", 0)
        limit = args.get("limit", 500)

        try:
            with open(path, "r", errors="replace") as f:
                lines = f.readlines()

            total = len(lines)
            selected = lines[offset:offset + limit]
            numbered = []
            for i, line in enumerate(selected, start=offset + 1):
                numbered.append(f"{i}\t{line.rstrip()}")

            result = "\n".join(numbered)
            if offset + limit < total:
                result += f"\n\n[... {total - offset - limit} more lines]"
            return result
        except Exception as e:
            return f'{{"error": "{str(e)}"}}'


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file. Creates parent directories if needed."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    }

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def execute(self, args: dict) -> str:
        path = args["path"]
        if not os.path.isabs(path):
            path = os.path.join(self.working_dir, path)

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(args["content"])
        return f"Written {len(args['content'])} bytes to {path}"


class ListDirTool(Tool):
    name = "list_dir"
    description = "List files and directories in a path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path", "default": "."},
            "recursive": {"type": "boolean", "description": "List recursively", "default": False},
        },
        "required": [],
    }

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def execute(self, args: dict) -> str:
        path = args.get("path", ".")
        if not os.path.isabs(path):
            path = os.path.join(self.working_dir, path)

        if not os.path.isdir(path):
            return f'{{"error": "Not a directory: {path}"}}'

        recursive = args.get("recursive", False)
        entries = []

        if recursive:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', 'venv', '__pycache__')]
                for f in sorted(files):
                    rel = os.path.relpath(os.path.join(root, f), path)
                    entries.append(rel)
                if len(entries) > 1000:
                    entries.append("... (truncated at 1000 entries)")
                    break
        else:
            for name in sorted(os.listdir(path)):
                full = os.path.join(path, name)
                suffix = "/" if os.path.isdir(full) else ""
                entries.append(f"{name}{suffix}")

        return "\n".join(entries) or "(empty directory)"


class GrepTool(Tool):
    name = "grep"
    description = "Search for a pattern in files. Returns matching lines with file paths and line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "Directory or file to search in", "default": "."},
            "include": {"type": "string", "description": "File glob pattern (e.g. '*.py')", "default": ""},
        },
        "required": ["pattern"],
    }

    def __init__(self, working_dir: str = "."):
        self.working_dir = os.path.abspath(working_dir)

    async def execute(self, args: dict) -> str:
        pattern = args["pattern"]
        path = args.get("path", ".")
        include = args.get("include", "")

        if not os.path.isabs(path):
            path = os.path.join(self.working_dir, path)

        cmd = f"grep -rn --color=never"
        if include:
            cmd += f" --include='{include}'"
        cmd += f" '{pattern}' '{path}' 2>/dev/null | head -100"

        proc = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        result = stdout.decode("utf-8", errors="replace")
        return result or "(no matches)"
