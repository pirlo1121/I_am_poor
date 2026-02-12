"""Módulo core del bot."""
from .session_manager import (
    get_or_create_session,
    clear_session,
    MAX_HISTORY_MESSAGES
)

__all__ = [
    'get_or_create_session',
    'clear_session',
    'MAX_HISTORY_MESSAGES'
]
