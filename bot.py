"""
bot.py - Bot de Telegram con IA (Asistente Financiero Personal)
Bot que interpreta lenguaje natural usando Gemini Pro/ChatGPT para registrar gastos
y consultar información financiera en una base de datos PostgreSQL (Supabase).
"""

from datetime import time, timezone, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from config import TELEGRAM_TOKEN, REMINDER_CHAT_ID, logger
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
from database import check_upcoming_bills
from core.session_manager import user_sessions


# ============================================
# RECORDATORIOS AUTOMÁTICOS
# ============================================

async def send_bill_reminders(context) -> None:
    """
    Job diario: verifica facturas que vencen mañana y envía recordatorio.
    Se ejecuta todos los días a las 8:00 AM.
    """
    if not REMINDER_CHAT_ID:
        logger.warning("⚠️ REMINDER_CHAT_ID no configurado. Saltando recordatorios.")
        return
    
    try:
        upcoming = check_upcoming_bills(days_ahead=1)
        
        if not upcoming:
            logger.info("✅ No hay facturas por vencer mañana.")
            return
        
        # Construir mensaje de recordatorio
        total = sum(b['amount'] for b in upcoming)
        msg = "⏰ **Recordatorio de Facturas**\n\n"
        msg += "📋 Las siguientes facturas vencen **mañana**:\n\n"
        
        for b in upcoming:
            msg += f"• {b['description']} - ${b['amount']:,.0f} (día {b['day_of_month']})\n"
        
        msg += f"\n💰 **Total: ${total:,.0f}**\n"
        msg += "\n💡 Recuerda marcarlas como pagadas cuando las pagues."
        
        await context.bot.send_message(
            chat_id=int(REMINDER_CHAT_ID),
            text=msg,
            parse_mode='Markdown'
        )
        logger.info(f"📨 Recordatorio enviado: {len(upcoming)} facturas por vencer mañana")
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorios: {e}")


async def cleanup_inactive_sessions(context) -> None:
    """
    Job periódico: limpia sesiones de usuarios inactivos para liberar memoria.
    Se ejecuta cada 2 horas.
    """
    if not user_sessions:
        return
    
    # Limpiar sesiones (el dict se mantiene en memoria)
    count = len(user_sessions)
    if count > 50:
        # Si hay muchas sesiones, limpiar las más antiguas
        # Simple approach: clear all (sessions se recrean al primer mensaje)
        user_sessions.clear()
        logger.info(f"🧹 Limpiadas {count} sesiones inactivas")


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
    
    # ============================================
    # JOBS PROGRAMADOS
    # ============================================
    job_queue = application.job_queue
    
    if job_queue is not None:
        # Recordatorio diario de facturas a las 8:00 AM (hora local Colombia UTC-5)
        colombia_tz = timezone(timedelta(hours=-5))
        if REMINDER_CHAT_ID:
            job_queue.run_daily(
                send_bill_reminders,
                time=time(hour=8, minute=0, second=0, tzinfo=colombia_tz),
                name="bill_reminders"
            )
            logger.info("⏰ Recordatorio diario de facturas programado (8:00 AM)")
        else:
            logger.info("ℹ️ REMINDER_CHAT_ID no configurado. Recordatorios desactivados.")
        
        # Limpieza de sesiones cada 2 horas
        job_queue.run_repeating(
            cleanup_inactive_sessions,
            interval=7200,  # 2 horas en segundos
            first=3600,     # Primera ejecución en 1 hora
            name="session_cleanup"
        )
    else:
        logger.warning("⚠️ JobQueue no disponible. Instala con: pip install 'python-telegram-bot[job-queue]'")
    
    # Iniciar bot
    logger.info("✅ Bot iniciado correctamente. Esperando mensajes...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
