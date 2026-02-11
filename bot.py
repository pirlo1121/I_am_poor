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
Eres un contador personal amigable y dinámico llamado "Asistente Financiero".

🎯 PERSONALIDAD:
- Habla de manera natural, conversacional y amigable
- Usa emojis para hacer las respuestas más dinámicas  
- Evita respuestas robóticas o muy técnicas
- Sé entusiasta y positivo cuando registres gastos exitosamente
- Muestra empatía cuando los gastos sean altos
- Celebra cuando ahorren dinero

IMPORTANTE: NO copies literalmente el formato de las respuestas del backend. 
Cuando recibas datos de la base de datos, reformúlalos de manera NATURAL y CONVERSACIONAL.

EJEMPLOS DE CÓMO RESPONDER:

❌ MAL (robótico):
"✅ Gasto registrado: 20000 COP - café - categoría: comida"

✅ BIEN (natural):
"¡Listo! 😊 Registré tu café de $20,000 en comida. Espero que haya estado delicioso ☕"

❌ MAL (frío):
"📊 Gastos del día:
- Café: 20,000 COP
- Uber: 15,000 COP
Total: 35,000 COP"

✅ BIEN (cálido):
"Hoy has gastado $35,000 💰
Veo que compraste café ($20k) y tomaste un Uber ($15k). ¡Un día bastante normal! 😊"

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
- SIEMPRE reformula las respuestas del backend de manera natural
- Usa emojis para hacerlo más amigable: 💰 📊 ✅ 🎉 😊 ☕ 🚕 🛒
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

# ============================================
# GESTIÓN DE SESIONES POR USUARIO
# ============================================
# Diccionario para guardar el historial de chat de cada usuario
user_sessions = {}

# Límite de mensajes en el historial (para evitar que crezca infinitamente)
# Se mantienen los últimos N mensajes para tener contexto útil sin sobrecargar la API
MAX_HISTORY_MESSAGES = 20  # 10 intercambios (usuario + asistente)

logger.info("✅ Herramientas de Gemini configuradas correctamente")


# ============================================
# AI WRAPPER - Función unificada para ambos providers
# ============================================

def generate_ai_response(user_message: str, chat_session=None):
    """
    Genera una respuesta usando el AI provider configurado (Gemini o ChatGPT).
    Retorna un objeto unificado con la respuesta y function calls.
    
    Args:
        user_message: El mensaje del usuario
        chat_session: Para Gemini: sesión de chat. Para ChatGPT: lista de mensajes de historial
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
        
        # Construir mensajes con historial
        messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        
        # Si hay historial, agregarlo
        if chat_session and isinstance(chat_session, list):
            messages.extend(chat_session)
        
        # Agregar mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        # Llamar a ChatGPT
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=openai_tools,
            tool_choice="auto"
        )
        
        return response
    
    else:
        # ===== GEMINI =====
        # Si hay una sesión de chat existente, usar send_message
        if chat_session:
            response = chat_session.send_message(user_message)
        else:
            # Modo stateless (para compatibilidad hacia atrás)
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
    y gestión de sesiones por usuario para mantener contexto conversacional.
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Usuario {user_id}: {user_message}")
    
    # ============================================
    # GESTIÓN DE SESIÓN DE CHAT POR USUARIO
    # ============================================
    
    # Verificar si el usuario ya tiene una sesión
    if user_id not in user_sessions:
        # Si NO existe: Crear una nueva sesión de chat
        if AI_PROVIDER == "gemini":
            logger.info(f"🆕 Creando nueva sesión Gemini para usuario {user_id}")
            # Crear sesión de chat con historial vacío
            model = gemini_client.models.get_generative_model(
                model='models/gemini-2.5-flash',
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[all_tools],
                    temperature=0.7
                )
            )
            chat_session = model.start_chat(history=[])
            user_sessions[user_id] = chat_session
        else:
            # Para ChatGPT, guardamos el historial de mensajes como lista
            logger.info(f"🆕 Creando nuevo historial ChatGPT para usuario {user_id}")
            user_sessions[user_id] = []  # Lista vacía de mensajes
    else:
        # Si SÍ existe: Recuperar la sesión guardada
        logger.info(f"♻️ Usando sesión existente para usuario {user_id}")
    
    try:
        # Obtener la sesión del usuario
        chat_session = user_sessions.get(user_id)
        
        # Generar respuesta con el AI provider configurado
        response = generate_ai_response(user_message, chat_session)
        
        # ===== PROCESAR RESPUESTA SEGÚN PROVIDER =====
        if AI_PROVIDER == "chatgpt":
            # CHATGPT: Revisar tool_calls
            message = response.choices[0].message
            
            # Guardar mensaje del usuario en el historial
            user_sessions[user_id].append({"role": "user", "content": user_message})
            
            # Limitar el historial a los últimos MAX_HISTORY_MESSAGES mensajes
            if len(user_sessions[user_id]) > MAX_HISTORY_MESSAGES:
                # Mantener solo los últimos mensajes (ventana deslizante)
                user_sessions[user_id] = user_sessions[user_id][-MAX_HISTORY_MESSAGES:]
                logger.info(f"📦 Historial limitado a {MAX_HISTORY_MESSAGES} mensajes para usuario {user_id}")
            
            if message.tool_calls:
                # Hay llamadas a funciones - recopilar resultados
                function_results = []
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    import json
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🤖 ChatGPT llama a función: {function_name} con args: {function_args}")
                    
                    # Ejecutar función y obtener resultado
                    function_result = await _execute_function(function_name, function_args, update)
                    function_results.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_result
                    })
                
                # Guardar mensaje del asistente con tool_calls en historial
                user_sessions[user_id].append({
                    "role": "assistant",
                    "content": message.content if message.content else "",
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    } for tc in message.tool_calls]
                })
                
                # Agregar resultados de funciones al historial
                user_sessions[user_id].extend(function_results)
                
                # Hacer segunda llamada a ChatGPT para que procese los resultados y genere respuesta natural
                logger.info("🔄 Enviando resultados a ChatGPT para generar respuesta natural")
                second_response = generate_ai_response("", user_sessions[user_id])
                final_message = second_response.choices[0].message
                
                if final_message.content:
                    await update.message.reply_text(final_message.content, parse_mode='Markdown')
                    user_sessions[user_id].append({"role": "assistant", "content": final_message.content})
            
            elif message.content:
                # Respuesta de texto normal
                await update.message.reply_text(message.content, parse_mode='Markdown')
                
                # Guardar respuesta del asistente en el historial
                user_sessions[user_id].append({"role": "assistant", "content": message.content})
            else:
                await update.message.reply_text(
                    "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
                )
                user_sessions[user_id].append({
                    "role": "assistant", 
                    "content": "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
                })
        
        else:
            # GEMINI: Revisar function_call en parts
            if response.candidates and response.candidates[0].content.parts:
                # Buscar si hay function calls y recopilar resultados
                function_calls_found = []
                text_responses = []
                
                for part in response.candidates[0].content.parts:
                    # Si hay una llamada a función
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)
                        
                        logger.info(f"🤖 Gemini llama a función: {function_name} con args: {function_args}")
                        
                        # Ejecutar función y guardar resultado
                        function_result = await _execute_function(function_name, function_args, update)
                        function_calls_found.append({
                            "name": function_name,
                            "result": function_result
                        })
                    
                    # Si es solo texto
                    elif hasattr(part, 'text') and part.text:
                        text_responses.append(part.text)
                
                # Si hubo function calls, enviar resultados de vuelta a Gemini para respuesta natural
                if function_calls_found:
                    logger.info("🔄 Enviando resultados a Gemini para generar respuesta natural")
                    
                    # Construir mensaje con los resultados de las funciones
                    for fc in function_calls_found:
                        # Enviar resultado de función de vuelta al chat
                        function_response_part = types.Part.from_function_response(
                            name=fc["name"],
                            response={"result": fc["result"]}
                        )
                        
                        # Obtener respuesta final de Gemini procesando el resultado
                        final_response = chat_session.send_message(function_response_part)
                        
                        # Enviar la respuesta natural al usuario
                        if final_response.candidates and final_response.candidates[0].content.parts:
                            for final_part in final_response.candidates[0].content.parts:
                                if hasattr(final_part, 'text') and final_part.text:
                                    await update.message.reply_text(final_part.text, parse_mode='Markdown')
                
                # Si solo hay texto (sin function calls)
                elif text_responses:
                    for text in text_responses:
                        await update.message.reply_text(text, parse_mode='Markdown')
            
            # Si no hay partes en la respuesta
            else:
                await update.message.reply_text(
                    "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
                )
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje (user_id={user_id}): {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        # ============================================
        # MANEJO DE ERRORES INTELIGENTE
        # ============================================
        # Solo reiniciar sesión si es un error crítico de API
        # Errores menores no deberían borrar el historial
        
        error_str = str(e).lower()
        critical_errors = [
            'invalid api key',
            'quota exceeded',
            'rate limit',
            'authentication',
            'unauthorized',
            'invalid_request_error'
        ]
        
        # Verificar si es un error crítico que requiere reinicio
        is_critical = any(err in error_str for err in critical_errors)
        
        if is_critical:
            # Error crítico: Reiniciar sesión
            logger.warning(f"🔄 Error CRÍTICO detectado. Reiniciando sesión para usuario {user_id}")
            
            if user_id in user_sessions:
                del user_sessions[user_id]
            
            # Crear nueva sesión
            if AI_PROVIDER == "gemini":
                model = gemini_client.models.get_generative_model(
                    model='models/gemini-2.5-flash',
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        tools=[all_tools],
                        temperature=0.7
                    )
                )
                user_sessions[user_id] = model.start_chat(history=[])
            else:
                user_sessions[user_id] = []
            
            await update.message.reply_text(
                "⚠️ Hubo un error crítico con la API. He reiniciado tu sesión de chat.\n"
                "Tu historial se ha borrado, pero puedes continuar desde aquí."
            )
        else:
            # Error menor: Mantener sesión pero informar al usuario
            logger.warning(f"⚠️ Error menor detectado. Manteniendo sesión para usuario {user_id}")
            await update.message.reply_text(
                "❌ Hubo un problema procesando tu mensaje. Tu historial se mantiene intacto.\n"
                "Por favor, intenta de nuevo o reformula tu pregunta."
            )


async def _execute_function(function_name: str, function_args: dict, update: Update) -> str:
    """
    Ejecuta la función correspondiente y RETORNA el resultado como string.
    La respuesta será procesada por la IA para generar una respuesta natural.
    """
    
    try:
        # === GASTOS NORMALES ===
        if function_name == "add_expense":
            result = add_expense(
                amount=function_args.get("amount"),
                description=function_args.get("description"),
                category=function_args.get("category")
            )
            return result["message"]
            
        elif function_name == "get_recent_expenses":
            return get_recent_expenses()
        
        # === CONSULTAS POR PERÍODO ===
        elif function_name == "get_expenses_by_day":
            date = function_args.get("date")
            return get_expenses_by_day(date)
        
        elif function_name == "get_expenses_by_week":
            return get_expenses_by_week()
        
        elif function_name == "get_expenses_by_category":
            category = function_args.get("category")
            return get_expenses_by_category(category)
        
        # === ANÁLISIS ===
        elif function_name == "get_category_summary":
            return get_category_summary()
        
        # === GASTOS FIJOS / FACTURAS ===
        elif function_name == "add_recurring_expense":
            result = add_recurring_expense(
                description=function_args.get("description"),
                amount=function_args.get("amount"),
                category=function_args.get("category"),
                day_of_month=function_args.get("day_of_month")
            )
            return result["message"]
        
        elif function_name == "get_recurring_expenses":
            return get_recurring_expenses()
        
        elif function_name == "get_pending_payments":
            return get_pending_payments()
        
        elif function_name == "mark_bill_paid":
            recurring_id = function_args.get("recurring_expense_id")
            result = mark_payment_done(recurring_id)
            return result["message"]
        
        # === NUEVAS FUNCIONES - MEJORAS ===
        elif function_name == "get_expenses_by_month":
            month = function_args.get("month")
            year = function_args.get("year")
            return get_expenses_by_month(month, year)
        
        elif function_name == "compare_monthly_expenses":
            month1 = function_args.get("month1")
            year1 = function_args.get("year1")
            month2 = function_args.get("month2")
            year2 = function_args.get("year2")
            return compare_monthly_expenses(month1, year1, month2, year2)
        
        elif function_name == "find_recurring_by_name":
            description = function_args.get("description")
            recurring_id = find_recurring_by_name(description)
            
            if recurring_id:
                # Automáticamente marcar como pagado
                result = mark_payment_done(recurring_id)
                return result["message"]
            else:
                return f"❌ No encontré ningún gasto fijo con el nombre '{description}'. Usa /fijos o 'ver gastos fijos' para ver la lista completa."
            
        else:
            logger.warning(f"⚠️ Función desconocida: {function_name}")
            return "⚠️ No puedo procesar esa solicitud en este momento."
    
    except Exception as e:
        logger.error(f"Error ejecutando función {function_name}: {e}")
        return f"❌ Error ejecutando {function_name}: {str(e)}"


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
