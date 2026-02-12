"""Módulo de integración con AI."""
from .prompts import SYSTEM_INSTRUCTION
from .tools import all_tools, execute_function
from .providers import generate_ai_response

__all__ = [
    'SYSTEM_INSTRUCTION',
    'all_tools',
    'execute_function',
    'generate_ai_response'
]
