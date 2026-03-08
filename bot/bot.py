"""
bot.py - Bot de Telegram (Cliente)
Bot que envía y recibe mensajes consumiendo una API centralizada en FastAPI.
"""
from datetime import time, timezone, timedelta
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)

from config.settings import TELEGRAM_TOKEN, REMINDER_CHAT_ID, logger
from handlers.commands import (
    start_command,
    help_command,
    gastos_command,
    resumen_command,
    facturas_command
)
from handlers.messages import (
    handle_message,
    handle_voice_message,
    error_handler
)

from api_client import get_due_bills, get_custom_reminders, delete_custom_reminder

# ============================================
# RECORDATORIOS AUTOMÁTICOS
# ============================================

async def send_bill_reminders(context) -> None:
    """
    Job diario: verifica facturas que vencen mañana y envía recordatorio.
    Se ejecuta todos los días a las 8:00 AM consultando al Backend.
    """
    if not REMINDER_CHAT_ID:
        logger.warning("⚠️ REMINDER_CHAT_ID no configurado. Saltando recordatorios.")
        return
    
    try:
        upcoming = await get_due_bills(days_ahead=1)
        
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
        logger.info(f"📨 Recordatorio de facturas enviado: {len(upcoming)} facturas")
        
    except Exception as e:
        logger.error(f"❌ Error enviando recordatorios de facturas: {e}")

async def send_custom_reminders(context) -> None:
    """
    Job periódico: verifica recordatorios personalizados que ya llegaron a su hora
    y los envía interactuando con el Backend. Se ejecuta cada 60 segundos.
    """
    try:
        due_reminders = await get_custom_reminders()
        
        if not due_reminders:
            return
        
        for reminder in due_reminders:
            try:
                chat_id = reminder.get('chat_id')
                message = reminder.get('message', 'Recordatorio')
                reminder_id = reminder.get('id')
                
                msg = f"⏰ **Recordatorio**\n\n📌 {message}"
                
                await context.bot.send_message(
                    chat_id=int(chat_id),
                    text=msg,
                    parse_mode='Markdown'
                )
                
                # Eliminar recordatorio en el backend después de enviarlo
                await delete_custom_reminder(reminder_id)
                logger.info(f"📨 Recordatorio enviado y eliminado: '{message}' (ID: {reminder_id})")
                
            except Exception as e:
                logger.error(f"❌ Error enviando recordatorio {reminder.get('id')}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error en job de recordatorios personalizados: {e}")


def main() -> None:
    """
    Función principal - Inicializa y ejecuta el bot cliente.
    """
    logger.info("🚀 Iniciando Cliente Bot Telegram...")
    
    # Crear aplicación del bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gastos", gastos_command))
    application.add_handler(CommandHandler("resumen", resumen_command))
    application.add_handler(CommandHandler("facturas", facturas_command))
    
    # Handler para mensajes de texto
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
            logger.info("ℹ️ REMINDER_CHAT_ID no configurado para facturas.")
            
        # Recordatorios personalizados cada 60 segundos
        job_queue.run_repeating(
            send_custom_reminders,
            interval=60,    # Cada 60 segundos
            first=10,       # Primera ejecución en 10 segundos
            name="custom_reminders"
        )
        logger.info("⏰ Job de recordatorios personalizados programado (cada 60s)")
    else:
        logger.warning("⚠️ JobQueue no disponible. Instala con: pip install 'python-telegram-bot[job-queue]'")
    
    # Iniciar bot
    logger.info("✅ Bot cliente iniciado correctamente. Conectado al Backend.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
