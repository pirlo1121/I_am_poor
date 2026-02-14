"""
bot.py - Bot de Telegram con IA (Asistente Financiero Personal)
Bot que interpreta lenguaje natural usando Gemini Pro/ChatGPT para registrar gastos
y consultar información financiera en una base de datos PostgreSQL (Supabase).
"""

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from config import TELEGRAM_TOKEN, logger
from handlers import (
    start_command,
    help_command,
    gastos_command,
    resumen_command,
    facturas_command,
    error_handler,
    handle_message,
    handle_voice_message
)



def main() -> None:
    """
    Función principal - Inicializa y ejecuta el bot.
    """
    logger.info("🚀 Iniciando Asistente Financiero Bot...")
    
    # Crear aplicación del bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gastos", gastos_command))
    application.add_handler(CommandHandler("resumen", resumen_command))
    application.add_handler(CommandHandler("facturas", facturas_command))
    
    
    # Handler para mensajes de texto (mensajes normales del usuario)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Handler para mensajes de voz
    application.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("✅ Bot iniciado correctamente. Esperando mensajes...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
