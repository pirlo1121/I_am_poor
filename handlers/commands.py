"""
Handlers para los comandos del bot de Telegram.
"""

from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from database import (
    get_recent_expenses,
    get_category_summary,
    get_pending_payments
)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /start"""
    welcome_message = """
👋 ¡Hola! Soy tu **Asistente Financiero Personal**.

Puedo ayudarte a:
📝 Registrar tus gastos
📊 Consultar tus gastos recientes
💡 Darte consejos sobre tus finanzas

**Ejemplos de uso:**
• "Gasté 20k en uvas"
• "Pagué 50 mil de Uber"
• "Muéstrame mis gastos"
• "¿Cuánto he gastado?"

¡Comienza a registrar tus gastos ahora! 💰
    """
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /help"""
    help_text = """
🤖 **Asistente Financiero - Guía Completa**

📝 **REGISTRAR GASTOS:**
• "Gasté 15k en café"
• "Pagué 80 mil de taxi"
• "Compré comida por 25000"

📊 **CONSULTAR GASTOS:**
• "Cuánto gasté hoy?"
• "Muéstrame los gastos de esta semana"
• "Cuánto he gastado en comida?"
• "Ver mis últimos gastos"

📈 **ANÁLISIS:**
• "En qué categoría gasto más?"
• "Resumen por categorías"

💰 **GASTOS FIJOS (FACTURAS):**
• "Registra internet de 60k el día 18"
• "Qué facturas tengo pendientes?"
• "Ver mis gastos fijos"
• "Pagué la luz" (marcar como pagada)

**Comandos:**
/start - Iniciar bot
/help - Esta ayuda
/gastos - Ver últimos gastos
/resumen - Análisis de categorías
/facturas - Facturas pendientes

¡Prueba preguntarme en lenguaje natural! 🎉
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def gastos_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /gastos - muestra los gastos recientes"""
    try:
        expenses_text = get_recent_expenses()
        await update.message.reply_text(expenses_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en /gastos: {e}")
        await update.message.reply_text(
            "❌ Error al consultar los gastos. Intenta de nuevo más tarde."
        )


async def resumen_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /resumen - muestra análisis por categorías"""
    try:
        summary_text = get_category_summary()
        await update.message.reply_text(summary_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en /resumen: {e}")
        await update.message.reply_text(
            "❌ Error al generar el resumen. Intenta de nuevo más tarde."
        )


async def facturas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja el comando /facturas - muestra facturas pendientes"""
    try:
        pending_text = get_pending_payments()
        await update.message.reply_text(pending_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en /facturas: {e}")
        await update.message.reply_text(
            "❌ Error al consultar facturas. Intenta de nuevo más tarde."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja errores del bot"""
    logger.error(f"Update {update} causó error: {context.error}")
