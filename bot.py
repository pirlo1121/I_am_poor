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

# AI Providers
import openai
from google import genai
from google.genai import types

# Database functions
from database import (
    add_expense, 
    get_recent_expenses,
    get_expenses_by_day,
    get_expenses_by_week,
    get_expenses_by_category,
    get_category_summary,
    add_recurring_expense,
    get_recurring_expenses,
    get_pending_payments,
    mark_payment_done,
    find_recurring_by_name,
    get_expenses_by_month,
    compare_monthly_expenses
)

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
CHATGPT_API_KEY: Final = os.getenv("CHATGPT_API_KEY", "")
GEMINI_API_KEY: Final = os.getenv("GEMINI_API_KEY", "")

# Validar Telegram token
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN debe estar configurado en .env")

# Determinar qué AI provider usar
USE_CHATGPT = bool(CHATGPT_API_KEY and CHATGPT_API_KEY.strip())

if USE_CHATGPT:
    logger.info("🤖 Usando ChatGPT como AI provider")
    openai.api_key = CHATGPT_API_KEY
    AI_PROVIDER = "chatgpt"
else:
    if not GEMINI_API_KEY:
        raise ValueError("❌ Debes configurar GEMINI_API_KEY o CHATGPT_API_KEY en .env")
    logger.info("🤖 Usando Gemini como AI provider")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    AI_PROVIDER = "gemini"

# System Instruction para Gemini (comportamiento del asistente)
SYSTEM_INSTRUCTION = """
Eres un contador personal estricto y profesional llamado "Asistente Financiero".

Tu trabajo es ayudar al usuario a:
1. Registrar gastos normales con DETECCIÓN INTELIGENTE de tiendas
2. Consultar gastos por diferentes períodos (día, semana, mes, categoría)
3. Analizar y comparar gastos entre meses
4. Gestionar gastos fijos mensuales (facturas recurrentes)
5. Marcar facturas como pagadas con LENGUAJE NATURAL

CAPACIDADES PRINCIPALES:

📝 REGISTRAR GASTOS CON SMART DETECTION:

**Gastos Normales:**
- "Gasté 20k en café" → add_expense(20000, "café", "comida")
- Formatos: "20k", "20mil", "20000" = 20,000 COP

**🛒 DETECCIÓN AUTOMÁTICA DE MERCADO:**
- "322 mil D1" → add_expense(322000, "D1", "mercado")
- "25 mil ara" → add_expense(25000, "ara", "mercado")
- "50k éxito" → add_expense(50000, "éxito", "mercado")
- Tiendas reconocidas: D1, ARA, Éxito, Olímpica, Carulla, Jumbo
- SIEMPRE categorizar compras de estas tiendas como "mercado"

📊 CONSULTAR GASTOS:
- "Cuánto gasté hoy?" → get_expenses_by_day(fecha_hoy)
- "Gastos de esta semana" → get_expenses_by_week()
- "Gastos de este mes" → get_expenses_by_month() [MES ACTUAL por defecto]
- "Gastos de enero" → get_expenses_by_month(1, 2026)
- "Cuánto he gastado en comida?" → get_expenses_by_category("comida")
- "Ver últimos gastos" → get_recent_expenses()

📈 ANÁLISIS Y COMPARACIONES:
- "En qué gasto más?" → get_category_summary()
- "Compara enero con febrero" → compare_monthly_expenses(1, 2026, 2, 2026)
- "Gastos de enero vs diciembre" → compare_monthly_expenses(12, 2025, 1, 2026)

💰 GASTOS FIJOS (FACTURAS RECURRENTES):

**Registrar:**
- "Registra internet de 60k el día 18" → add_recurring_expense("internet", 60000, "servicios", 18)
- "Luz de 45 mil el día 15" → add_recurring_expense("luz", 45000, "servicios", 15)

**Consultar:**
- "Qué facturas tengo?" → get_pending_payments()
- "Ver gastos fijos" → get_recurring_expenses()

**✅ MARCAR COMO PAGADO (LENGUAJE NATURAL):**
- "arriendo pagado" → Buscar gasto fijo "arriendo" y marcar como pagado
- "Pagué la luz" → Buscar gasto fijo "luz" y marcar como pagado
- "Internet pagado" → Buscar gasto fijo "internet" y marcar como pagado
- Proceso: Usa find_recurring_by_name() para encontrar el ID, luego mark_bill_paid()

REGLAS IMPORTANTES:
- Categorías válidas: comida, transporte, entretenimiento, servicios, salud, mercado, general
- **mercado** es SOLO para tiendas (D1, ARA, Éxito, etc.)
- **comida** es para restaurantes, cafés, snacks individuales
- Para gastos fijos, el día debe estar entre 1 y 31
- Todas las consultas muestran solo el mes actual por defecto
- Sé conciso, profesional y amigable

Ejemplos:
Usuario: "322 mil D1" → add_expense(322000, "D1", "mercado")
Usuario: "Gasté 5k en café" → add_expense(5000, "café", "comida")
Usuario: "arriendo pagado" → find_recurring_by_name("arriendo") → mark_bill_paid(id_encontrado)
Usuario: "Gastos de enero" → get_expenses_by_month(1, 2026)
Usuario: "Compara enero con diciembre" → compare_monthly_expenses(12, 2025, 1, 2026)
"""

# Definir las herramientas (Tools) para Gemini Function Calling - NUEVA SINTAXIS
all_tools = types.Tool(
    function_declarations=[
        # === GASTOS NORMALES ===
        types.FunctionDeclaration(
            name="add_expense",
            description="Registra un nuevo gasto en la base de datos. Usa cuando el usuario mencione que gastó dinero.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto en COP. Convierte 'k' o 'mil' a números: 20k = 20000"
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Descripción breve del gasto"
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría del gasto",
                        enum=["comida", "transporte", "entretenimiento", "servicios", "salud", "mercado", "general"]
                    )
                },
                required=["amount", "description", "category"]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_recent_expenses",
            description="Obtiene los últimos 5 gastos registrados.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        # === CONSULTAS POR PERÍODO ===
        types.FunctionDeclaration(
            name="get_expenses_by_day",
            description="Obtiene gastos de un día específico. Usa cuando pregunten 'cuánto gasté hoy' o por una fecha específica.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "date": types.Schema(
                        type=types.Type.STRING,
                        description="Fecha en formato YYYY-MM-DD. Si no se proporciona, usa el día actual"
                    )
                },
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_expenses_by_week",
            description="Obtiene gastos de los últimos 7 días. Usa cuando pregunten por gastos de la semana.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_expenses_by_category",
            description="Obtiene todos los gastos de una categoría específica.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría a consultar",
                        enum=["comida", "transporte", "entretenimiento", "servicios", "salud", "general"]
                    )
                },
                required=["category"]
            )
        ),
        
        # === ANÁLISIS ===
        types.FunctionDeclaration(
            name="get_category_summary",
            description="Analiza gastos por categoría ordenados de mayor a menor. Usa cuando pregunten en qué gastan más o análisis de categorías.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        # === GASTOS FIJOS / FACTURAS RECURRENTES ===
        types.FunctionDeclaration(
            name="add_recurring_expense",
            description="Registra un gasto fijo mensual (factura recurrente). Usa cuando digan 'registra X cada mes el día Y'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Descripción del gasto fijo (ej: 'internet', 'luz')"
                    ),
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto mensual en COP"
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría del gasto",
                        enum=["comida", "transporte", "entretenimiento", "servicios", "salud", "general"]
                    ),
                    "day_of_month": types.Schema(
                        type=types.Type.INTEGER,
                        description="Día del mes en que vence (1-31)"
                    )
                },
                required=["description", "amount", "category", "day_of_month"]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_recurring_expenses",
            description="Lista todos los gastos fijos mensuales configurados. Usa cuando pregunten por gastos fijos o facturas recurrentes.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_pending_payments",
            description="Obtiene facturas pendientes de pago del mes actual. Usa cuando pregunten qué facturas faltan por pagar.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        # === NUEVAS HERRAMIENTAS - MEJORAS ===
        
        types.FunctionDeclaration(
            name="get_expenses_by_month",
            description="Obtiene todos los gastos de un mes específico. Si no se especifica, muestra el mes actual.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "month": types.Schema(
                        type=types.Type.INTEGER,
                        description="Mes (1-12). Si es None, usa mes actual"
                    ),
                    "year": types.Schema(
                        type=types.Type.INTEGER,
                        description="Año (ej: 2026). Si es None, usa año actual"
                    )
                },
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="compare_monthly_expenses",
            description="Compara gastos entre dos meses. Muestra diferencias y análisis por categorías.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "month1": types.Schema(type=types.Type.INTEGER, description="Primer mes (1-12)"),
                    "year1": types.Schema(type=types.Type.INTEGER, description="Primer año"),
                    "month2": types.Schema(type=types.Type.INTEGER, description="Segundo mes (1-12)"),
                    "year2": types.Schema(type=types.Type.INTEGER, description="Segundo año")
                },
                required=["month1", "year1", "month2", "year2"]
            )
        ),
        
        types.FunctionDeclaration(
            name="find_recurring_by_name",
            description="Busca un gasto fijo por nombre (case-insensitive). Retorna el ID para usar con mark_bill_paid. Usa cuando digan 'X pagado' o 'pagué X'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Nombre del gasto fijo a buscar (ej: 'arriendo', 'luz', 'internet')"
                    )
                },
                required=["description"]
            )
        ),
        
        types.FunctionDeclaration(
            name="mark_bill_paid",
            description="Marca una factura/gasto fijo como pagado este mes. Usa cuando digan 'pagué X' refiriéndose a un gasto fijo.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "recurring_expense_id": types.Schema(
                        type=types.Type.INTEGER,
                        description="ID del gasto fijo a marcar como pagado (obtener de find_recurring_by_name o get_pending_payments)"
                    )
                },
                required=["recurring_expense_id"]
            )
        )
    ]
)

logger.info("✅ Herramientas de Gemini configuradas correctamente")


# ============================================
# AI WRAPPER - Función unificada para ambos providers
# ============================================

def generate_ai_response(user_message: str):
    """
    Genera una respuesta usando el AI provider configurado (Gemini o ChatGPT).
    Retorna un objeto unificado con la respuesta y function calls.
    """
    if AI_PROVIDER == "chatgpt":
        # ===== CHATGPT =====
        # Convertir tools al formato de OpenAI
        openai_tools = []
        for func_decl in all_tools.function_declarations:
            tool_def = {
                "type": "function",
                "function": {
                    "name": func_decl.name,
                    "description": func_decl.description,
                    "parameters": _gemini_schema_to_openai(func_decl.parameters)
                }
            }
            openai_tools.append(tool_def)
        
        # Llamar a ChatGPT
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Puedes usar gpt-4, gpt-3.5-turbo, etc.
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_message}
            ],
            tools=openai_tools,
            tool_choice="auto"
        )
        
        return response
    
    else:
        # ===== GEMINI =====
        response = gemini_client.models.generate_content(
            model='models/gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[all_tools],
                temperature=0.7
            )
        )
        
        return response


def _gemini_schema_to_openai(gemini_schema):
    """Convierte el schema de Gemini al formato de OpenAI."""
    if not gemini_schema:
        return {"type": "object", "properties": {}}
    
    openai_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    if hasattr(gemini_schema, 'properties') and gemini_schema.properties:
        for prop_name, prop_schema in gemini_schema.properties.items():
            prop_def = {}
            
            # Mapear tipo
            if prop_schema.type == types.Type.STRING:
                prop_def["type"] = "string"
            elif prop_schema.type == types.Type.NUMBER:
                prop_def["type"] = "number"
            elif prop_schema.type == types.Type.INTEGER:
                prop_def["type"] = "integer"
            elif prop_schema.type == types.Type.BOOLEAN:
                prop_def["type"] = "boolean"
            else:
                prop_def["type"] = "string"
            
            # Añadir descripción
            if hasattr(prop_schema, 'description'):
                prop_def["description"] = prop_schema.description
            
            # Añadir enum si existe
            if hasattr(prop_schema, 'enum') and prop_schema.enum:
                prop_def["enum"] = list(prop_schema.enum)
            
            openai_schema["properties"][prop_name] = prop_def
    
    # Añadir campos requeridos
    if hasattr(gemini_schema, 'required') and gemini_schema.required:
        openai_schema["required"] = list(gemini_schema.required)
    
    return openai_schema


# ============================================
# TELEGRAM COMMAND HANDLERS
# ============================================


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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja todos los mensajes del usuario usando AI (Gemini o ChatGPT) con Function Calling
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Usuario {user_id}: {user_message}")
    
    try:
        # Generar respuesta con el AI provider configurado
        response = generate_ai_response(user_message)
        
        # ===== PROCESAR RESPUESTA SEGÚN PROVIDER =====
        if AI_PROVIDER == "chatgpt":
            # CHATGPT: Revisar tool_calls
            message = response.choices[0].message
            
            if message.tool_calls:
                # Hay llamadas a funciones
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    import json
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🤖 ChatGPT llama a función: {function_name} con args: {function_args}")
                    
                    # Ejecutar función
                    await _execute_function(function_name, function_args, update)
            
            elif message.content:
                # Respuesta de texto normal
                await update.message.reply_text(message.content, parse_mode='Markdown')
            else:
                await update.message.reply_text(
                    "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
                )
        
        else:
            # GEMINI: Revisar function_call en parts
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    # Si hay una llamada a función
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)
                        
                        logger.info(f"🤖 Gemini llama a función: {function_name} con args: {function_args}")
                        
                        # Ejecutar función
                        await _execute_function(function_name, function_args, update)
                    
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
            "❌ MY nigga, hay un error, lea el codigo"
        )


async def _execute_function(function_name: str, function_args: dict, update: Update):
    """Ejecuta la función correspondiente basado en el nombre y argumentos."""
    
    # === GASTOS NORMALES ===
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
    
    # === CONSULTAS POR PERÍODO ===
    elif function_name == "get_expenses_by_day":
        date = function_args.get("date")
        result = get_expenses_by_day(date)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "get_expenses_by_week":
        result = get_expenses_by_week()
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "get_expenses_by_category":
        category = function_args.get("category")
        result = get_expenses_by_category(category)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    # === ANÁLISIS ===
    elif function_name == "get_category_summary":
        result = get_category_summary()
        await update.message.reply_text(result, parse_mode='Markdown')
    
    # === GASTOS FIJOS / FACTURAS ===
    elif function_name == "add_recurring_expense":
        result = add_recurring_expense(
            description=function_args.get("description"),
            amount=function_args.get("amount"),
            category=function_args.get("category"),
            day_of_month=function_args.get("day_of_month")
        )
        await update.message.reply_text(result["message"])
    
    elif function_name == "get_recurring_expenses":
        result = get_recurring_expenses()
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "get_pending_payments":
        result = get_pending_payments()
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "mark_bill_paid":
        recurring_id = function_args.get("recurring_expense_id")
        result = mark_payment_done(recurring_id)
        await update.message.reply_text(result["message"])
    
    # === NUEVAS FUNCIONES - MEJORAS ===
    elif function_name == "get_expenses_by_month":
        month = function_args.get("month")
        year = function_args.get("year")
        result = get_expenses_by_month(month, year)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "compare_monthly_expenses":
        month1 = function_args.get("month1")
        year1 = function_args.get("year1")
        month2 = function_args.get("month2")
        year2 = function_args.get("year2")
        result = compare_monthly_expenses(month1, year1, month2, year2)
        await update.message.reply_text(result, parse_mode='Markdown')
    
    elif function_name == "find_recurring_by_name":
        description = function_args.get("description")
        recurring_id = find_recurring_by_name(description)
        
        if recurring_id:
            # Automáticamente marcar como pagado
            result = mark_payment_done(recurring_id)
            await update.message.reply_text(result["message"])
        else:
            await update.message.reply_text(
                f"❌ No encontré ningún gasto fijo con el nombre '{description}'.\n"
                f"Usa /fijos o 'ver gastos fijos' para ver la lista completa."
            )
        
    else:
        logger.warning(f"⚠️ Función desconocida: {function_name}")
        await update.message.reply_text(
            "⚠️ No puedo procesar esa solicitud en este momento."
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
    application.add_handler(CommandHandler("resumen", resumen_command))
    application.add_handler(CommandHandler("facturas", facturas_command))
    
    # Handler para mensajes de texto (mensajes normales del usuario)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Iniciar bot
    logger.info("✅ Bot iniciado correctamente. Esperando mensajes...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
