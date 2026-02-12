"""
Declaración de herramientas (tools) para AI Function Calling.
"""

from google.genai import types
from config import logger
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
    compare_monthly_expenses,
    get_paid_payments,
    get_all_monthly_bills
)

# Definir las herramientas (Tools) para Gemini Function Calling
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
        
        types.FunctionDeclaration(
            name="get_paid_payments",
            description="Obtiene las mensualidades/facturas ya pagadas este mes. Usa cuando pregunten por facturas pagadas o mensualidades que ya se pagaron.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_all_monthly_bills",
            description="Obtiene todas las mensualidades del mes (pagadas y pendientes). Usa cuando pregunten por todas las facturas o ver estado completo de mensualidades.",
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


async def execute_function(function_name: str, function_args: dict) -> str:
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
        
        elif function_name == "get_paid_payments":
            return get_paid_payments()
        
        elif function_name == "get_all_monthly_bills":
            return get_all_monthly_bills()
        
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


logger.info("✅ Herramientas de Gemini configuradas correctamente")
