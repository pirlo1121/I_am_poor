"""
Configuración y variables de entorno del bot.
"""

import os
import logging
from typing import Final
from dotenv import load_dotenv
# No AI SDKs needed here because Bot only uses Telegram

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de tokens
TELEGRAM_TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHATGPT_API_KEY: Final = os.getenv("CHATGPT_API_KEY", "")
GEMINI_API_KEY: Final = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL: Final = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: Final = os.getenv("SUPABASE_KEY", "")
REMINDER_CHAT_ID: Final = os.getenv("REMINDER_CHAT_ID", "")  # Chat ID for bill reminders

# Validar Telegram token
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN debe estar configurado en .env")

# AI variables are not checked by the Bot
