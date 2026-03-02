"""
Configuración y variables de entorno del bot.
"""

import os
import logging
from typing import Final
from dotenv import load_dotenv
import openai
from google import genai

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

TELEGRAM_TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Fallback a Gemini siempre ya que la key de ChatGPT es invalida.
USE_CHATGPT = False

# Always initialize Gemini client (for voice transcription or fallback)
if GEMINI_API_KEY:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
else:
    gemini_client = None

if USE_CHATGPT:
    logger.info("🤖 Usando ChatGPT como AI provider")
    openai.api_key = CHATGPT_API_KEY
    AI_PROVIDER = "chatgpt"
else:
    if not GEMINI_API_KEY:
        raise ValueError("❌ Debes configurar GEMINI_API_KEY o CHATGPT_API_KEY en .env")
    logger.info("🤖 Usando Gemini como AI provider")
    AI_PROVIDER = "gemini"
