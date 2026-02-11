"""
bot.py - Bot de Telegram con IA (Asistente Financiero Personal)
Bot que interpreta lenguaje natural usando Gemini Pro para registrar gastos
y consultar información financiera en una base de datos PostgreSQL (Supabase).
"""

import os
import logging
from typing import Final
from dotenv import load_dotenv

# Telegram imports
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Google Generative AI (Gemini) - NUEVA LIBRERÍA
from google import genai
from google.genai import types

# Database functions
from database import add_expense, get_recent_expenses

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración
TELEGRAM_TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY: Final = os.getenv("GEMINI_API_KEY", "")

# Validar credenciales
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN y GEMINI_API_KEY deben estar configurados en .env")

# Configurar cliente de Gemini AI
client = genai.Client(api_key=GEMINI_API_KEY)

# System Instruction para Gemini (comportamiento del asistente)
SYSTEM_INSTRUCTION = """
Eres un contador personal estricto y profesional llamado "Asistente Financiero".

Tu trabajo es ayudar al usuario a:
1. Registrar gastos cuando mencione que ha gastado dinero
2. Consultar sus gastos recientes cuando lo solicite
3. Responder preguntas relacionadas con finanzas personales

REGLAS IMPORTANTES:
- Cuando el usuario diga que gastó dinero (ej: "gasté 20k en uvas"), DEBES llamar a la función add_expense
- Los montos pueden estar en formato: "20k", "20mil", "20000", "20.000" - todos significan 20,000 COP
- Si el usuario pregunta por sus gastos o quiere ver un resumen, llama a get_recent_expenses
- Sé conciso, profesional y amigable
- Si no estás seguro de la categoría, usa "general"
- Las categorías comunes son: comida, transporte, entretenimiento, servicios, salud, general

Ejemplos de conversación:
Usuario: "Gasté 20k en uvas"
→ Llamas add_expense(20000, "uvas", "comida")

Usuario: "Pagué 50 mil de Uber"
→ Llamas add_expense(50000, "Uber", "transporte")

Usuario: "Muéstrame mis gastos"
→ Llamas get_recent_expenses()
"""

# Definir las herramientas (Tools) para Gemini Function Calling - NUEVA SINTAXIS
add_expense_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="add_expense",
            description="Registra un nuevo gasto en la base de datos. Usa esta función cuando el usuario mencione que ha gastado dinero.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto del gasto en pesos colombianos (COP). Convierte 'k' o 'mil' a números completos. Ejemplo: 20k = 20000"
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Descripción breve del gasto (ej: 'uvas', 'taxi', 'almuerzo')"
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría del gasto",
                        enum=["comida", "transporte", "entretenimiento", "servicios", "salud", "general"]
                    )
                },
                required=["amount", "description", "category"]
            )
        ),
        types.FunctionDeclaration(
            name="get_recent_expenses",
            description="Obtiene los últimos 5 gastos registrados. Usa esta función cuando el usuario quiera ver sus gastos recientes o un resumen.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        )
    ]
)

logger.info("✅ Herramientas de Gemini configuradas correctamente")


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
🤖 **Comandos disponibles:**

/start - Iniciar el bot
/help - Mostrar esta ayuda
/gastos - Ver tus últimos gastos

**Cómo usar el bot:**

📝 Para registrar un gasto, simplemente escribe:
• "Gasté 15k en café"
• "Pagué 80 mil de taxi"
• "Compré comida por 25000"

📊 Para ver tus gastos:
• "Muéstrame mis gastos"
• "¿Cuánto he gastado?"
• Usa el comando /gastos

¡Así de fácil! 🎉
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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja todos los mensajes del usuario usando Gemini AI con Function Calling
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Usuario {user_id}: {user_message}")
    
    try:
        # Enviar mensaje del usuario a Gemini con la NUEVA API
        # NOTA: Usar 'models/gemini-2.5-flash' que es el modelo disponible
        response = client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[add_expense_tool],
                temperature=0.7
            )
        )
        
        # Verificar si hay function calls en la respuesta
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                # Si hay una llamada a función
                if hasattr(part, 'function_call') and part.function_call:
                    function_call = part.function_call
                    function_name = function_call.name
                    function_args = dict(function_call.args)
                    
                    logger.info(f"🤖 Gemini llama a función: {function_name} con args: {function_args}")
                    
                    # Ejecutar la función correspondiente
                    if function_name == "add_expense":
                        result = add_expense(
                            amount=function_args.get("amount"),
                            description=function_args.get("description"),
                            category=function_args.get("category")
                        )
                        await update.message.reply_text(result["message"])
                        
                    elif function_name == "get_recent_expenses":
                        expenses_text = get_recent_expenses()
                        await update.message.reply_text(expenses_text, parse_mode='Markdown')
                        
                    else:
                        logger.warning(f"⚠️ Función desconocida: {function_name}")
                        await update.message.reply_text(
                            "⚠️ No puedo procesar esa solicitud en este momento."
                        )
                
                # Si es solo texto (respuesta normal sin función)
                elif hasattr(part, 'text') and part.text:
                    await update.message.reply_text(part.text, parse_mode='Markdown')
        
        # Si no hay partes en la respuesta
        else:
            await update.message.reply_text(
                "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
            )
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje: {e}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(
            "❌ Hubo un error procesando tu mensaje. Por favor, intenta de nuevo."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja errores del bot"""
    logger.error(f"Update {update} causó error: {context.error}")


def main() -> None:
    """
    Función principal - Inicializa y ejecuta el bot
    """
    logger.info("🚀 Iniciando Asistente Financiero Bot...")
    
    # Crear aplicación del bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registrar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("gastos", gastos_command))
    
    # Handler para mensajes de texto (mensajes normales del usuario)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("✅ Bot iniciado correctamente. Esperando mensajes...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
