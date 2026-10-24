#!/usr/bin/env python3
"""MCP Server: SiYuan Brain — cross-target knowledge graph.

5 tools for querying the SiYuan knowledge base.
Full implementation syncs brain.json to SiYuan blocks.
"""
import json

TOOLS = [
    {"name": "brain_search", "description": "Full-text search across all target brains in SiYuan"},
    {"name": "brain_untested", "description": "Untested API endpoints sorted by priority"},
    {"name": "brain_related", "description": "Find shared attack patterns between targets"},
    {"name": "brain_suggest", "description": "Attack suggestions from patterns + tech stack"},
    {"name": "brain_query", "description": "Raw SQL query against SiYuan database"},
]

if __name__ == "__main__":
    print(json.dumps({"name": "siyuan-brain", "version": "0.1.0", "tools": TOOLS}))
