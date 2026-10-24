"""Tool registry — base class and discovery for all agent tools."""
import json
from abc import ABC, abstractmethod
from typing import Optional

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from runtime.llm.base import ToolDefinition


class Tool(ABC):
    """Base class for all agent tools."""
    name: str = ""
    description: str = ""
    parameters: dict = {}

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    @abstractmethod
    async def execute(self, args: dict) -> str:
        """Execute the tool and return result as string."""


class ToolRegistry:
    """Registry of available tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def get_definitions(self) -> list[ToolDefinition]:
        return [t.definition for t in self._tools.values()]

    def create_default_tools(self, working_dir: str = ".") -> list[Tool]:
        """Create and register the standard tool set."""
        from .shell import ShellTool
        from .file_ops import ReadFileTool, WriteFileTool, ListDirTool, GrepTool
        from .web import HttpRequestTool

        tools = [
            ShellTool(working_dir=working_dir),
            ReadFileTool(working_dir=working_dir),
            WriteFileTool(working_dir=working_dir),
            ListDirTool(working_dir=working_dir),
            GrepTool(working_dir=working_dir),
            HttpRequestTool(),
        ]
        for t in tools:
            self.register(t)
        return tools

    def create_pentest_tools(self, working_dir: str = ".") -> list[Tool]:
        """Create tools for web pentest flow."""
        tools = self.create_default_tools(working_dir)
        from .scanner import NucleiTool, FfufTool
        from .crawler import KatanaTool, WaybackTool

        extra = [
            NucleiTool(),
            FfufTool(),
            KatanaTool(),
            WaybackTool(),
        ]
        for t in extra:
            self.register(t)
        tools.extend(extra)
        return tools

    def create_audit_tools(self, working_dir: str = ".") -> list[Tool]:
        """Create tools for whitebox audit flow."""
        tools = self.create_default_tools(working_dir)
        from .code_analysis import SemgrepTool

        extra = [SemgrepTool()]
        for t in extra:
            self.register(t)
        tools.extend(extra)
        return tools
