"""Módulo de configuración del bot."""
from .settings import (
    TELEGRAM_TOKEN,
    AI_PROVIDER,
    logger,
    gemini_client,
    openai,
    SUPABASE_URL,
    SUPABASE_KEY,
    REMINDER_CHAT_ID
)

__all__ = [
    'TELEGRAM_TOKEN',
    'AI_PROVIDER',
    'logger',
    'gemini_client',
    'openai',
    'SUPABASE_URL',
    'SUPABASE_KEY',
    'REMINDER_CHAT_ID'
]
