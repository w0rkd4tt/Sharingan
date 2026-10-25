"""Sharingan Agent Runtime — LLM-agnostic multi-agent orchestration."""
from .agent import Agent, AgentResult, load_prompt
from .session import Session
from .coordinator import Coordinator
from .reactive import ReactiveLoop, ReactiveEvent, ReactiveAction
