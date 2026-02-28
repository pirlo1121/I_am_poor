"""
Declaración de herramientas (tools) para AI Function Calling.
"""

from google.genai import types
from settings import logger
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
    unmark_payment_done,
    find_recurring_by_name,
    get_expenses_by_month,
    compare_monthly_expenses,
    get_paid_payments,
    get_all_monthly_bills,
    get_financial_summary,
    # Metas de Ahorro
    add_savings_goal,
    get_savings_goals,
    add_contribution_to_goal,
    find_savings_goal_by_name,
    # Análisis Predictivo
    get_spending_prediction,
    get_financial_insights,
    # Ingresos
    set_fixed_salary,
    add_extra_income,
    get_extra_incomes,
    get_income_summary,
    # CRUD Imports
    update_expense, delete_expense,
    update_recurring_expense, delete_recurring_expense,
    update_savings_goal, delete_savings_goal,
    update_income, delete_income,
    # Recordatorios personalizados
    add_reminder
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

        types.FunctionDeclaration(
            name="update_expense",
            description="Actualiza un gasto existente. Necesitas el ID (que puedes ver en get_recent_expenses o get_expenses_by_day).",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "expense_id": types.Schema(type=types.Type.INTEGER, description="ID del gasto a actualizar"),
                    "amount": types.Schema(type=types.Type.NUMBER, description="Nuevo monto (opcional)"),
                    "description": types.Schema(type=types.Type.STRING, description="Nueva descripción (opcional)"),
                    "category": types.Schema(type=types.Type.STRING, description="Nueva categoría (opcional)")
                },
                required=["expense_id"]
            )
        ),

        types.FunctionDeclaration(
            name="delete_expense",
            description="Elimina un gasto por su ID. VERIFICA BIEN EL ID ANTES DE BORRAR.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "expense_id": types.Schema(type=types.Type.INTEGER, description="ID del gasto a eliminar")
                },
                required=["expense_id"]
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
            name="update_recurring_expense",
            description="Actualiza un gasto fijo existente. Requiere ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID del gasto fijo"),
                    "description": types.Schema(type=types.Type.STRING, description="Nueva descripción (opcional)"),
                    "amount": types.Schema(type=types.Type.NUMBER, description="Nuevo monto (opcional)"),
                    "day_of_month": types.Schema(type=types.Type.INTEGER, description="Nuevo día de pago (opcional)"),
                    "category": types.Schema(type=types.Type.STRING, description="Nueva categoría (opcional)")
                },
                required=["id"]
            )
        ),

        types.FunctionDeclaration(
            name="delete_recurring_expense",
            description="Elimina (desactiva) un gasto fijo por su ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID del gasto fijo a eliminar")
                },
                required=["id"]
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
        
        # === MARCAR / DESMARCAR PAGOS ===
        
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
            description="Busca un gasto fijo por nombre y LO MARCA COMO PAGADO automáticamente. Usa cuando digan 'pagué X', 'X pagado'.",
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
            name="find_recurring_by_name_for_unmark",
            description="Busca un gasto fijo por nombre y LO DESMARCA (quita el pago) del mes actual. Usa cuando digan 'no pagué X', 'desmarcar X', 'quitar pago X'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Nombre del gasto fijo a desmarcar (ej: 'arriendo', 'luz', 'internet')"
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
        ),
        
        types.FunctionDeclaration(
            name="unmark_bill_paid",
            description="Desmarca una factura/gasto fijo como pagado este mes (revierte el pago). Usa cuando digan 'no pagué X' o 'desmarcar X'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "recurring_expense_id": types.Schema(
                        type=types.Type.INTEGER,
                        description="ID del gasto fijo a desmarcar"
                    )
                },
                required=["recurring_expense_id"]
            )
        ),
        
        # === FUNCIÓN OPTIMIZADA - RESUMEN RÁPIDO ===
        types.FunctionDeclaration(
            name="get_financial_summary",
            description="🚀 FUNCIÓN OPTIMIZADA - Obtiene TODO el resumen financiero del mes en UNA operación: gastos + mensualidades + balance. MUCHO MÁS RÁPIDO que llamar funciones separadas.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "budget": types.Schema(
                        type=types.Type.NUMBER,
                        description="Presupuesto mensual en COP. Ejemplo: 'tengo 3 millones' → budget=3000000"
                    )
                },
                required=[]
            )
        ),
        
        # === METAS DE AHORRO ===
        
        types.FunctionDeclaration(
            name="add_savings_goal",
            description="Crea una nueva meta de ahorro. Usa cuando el usuario diga que quiere ahorrar dinero para algo específico.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name": types.Schema(
                        type=types.Type.STRING,
                        description="Nombre de la meta (ej: 'Vacaciones', 'Laptop')"
                    ),
                    "target_amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto objetivo en COP. Convierte 'k' o 'millones': 2M = 2000000"
                    ),
                    "deadline": types.Schema(
                        type=types.Type.STRING,
                        description="Fecha límite en formato YYYY-MM-DD. Opcional."
                    ),
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría de la meta",
                        enum=["general", "viaje", "tecnología", "emergencia", "educación"]
                    )
                },
                required=["name", "target_amount"]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_savings_goals",
            description="Muestra todas las metas de ahorro activas con progreso. Usa cuando pregunten por metas o ahorros.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),

        types.FunctionDeclaration(
            name="update_savings_goal",
            description="Actualiza una meta de ahorro. Requiere ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID de la meta"),
                    "name": types.Schema(type=types.Type.STRING, description="Nuevo nombre (opcional)"),
                    "target_amount": types.Schema(type=types.Type.NUMBER, description="Nuevo monto objetivo (opcional)"),
                    "deadline": types.Schema(type=types.Type.STRING, description="Nueva fecha límite YYYY-MM-DD (opcional)")
                },
                required=["id"]
            )
        ),

        types.FunctionDeclaration(
            name="delete_savings_goal",
            description="Elimina una meta de ahorro por su ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID de la meta a eliminar")
                },
                required=["id"]
            )
        ),
        
        types.FunctionDeclaration(
            name="add_contribution_to_savings",
            description="Agrega dinero a una meta de ahorro. Usa cuando digan 'agregué X a meta Y' o 'ahorré X para Y'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "goal_name": types.Schema(
                        type=types.Type.STRING,
                        description="Nombre de la meta (buscaremos por coincidencia)"
                    ),
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto a agregar en COP"
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Descripción opcional del ahorro"
                    )
                },
                required=["goal_name", "amount"]
            )
        ),
        
        # === ANÁLISIS PREDICTIVO ===
        
        types.FunctionDeclaration(
            name="get_spending_prediction",
            description="Proyecta gastos futuros basándose en promedio de últimos 3 meses. Usa cuando pregunten 'cuánto voy a gastar' o pidan proyecciones.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "category": types.Schema(
                        type=types.Type.STRING,
                        description="Categoría opcional para proyectar solo esa categoría"
                    )
                },
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_financial_insights",
            description="Genera insights y análisis financieros automáticos. Usa cuando pidan análisis, insights, consejos o revisar finanzas.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={},
                required=[]
            )
        ),
        
        # === INGRESOS ===
        
        types.FunctionDeclaration(
            name="set_fixed_salary",
            description="Define o actualiza el salario fijo mensual. Usa cuando digan 'mi salario es X', 'gano X al mes'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Salario mensual en COP. Convierte: '2 millones' = 2000000, '1.5M' = 1500000"
                    )
                },
                required=["amount"]
            )
        ),
        
        types.FunctionDeclaration(
            name="add_extra_income",
            description="Registra un ingreso extra (fuera del salario). Usa cuando digan 'me ingresaron X', 'vendí algo por X', 'me pagaron X'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "amount": types.Schema(
                        type=types.Type.NUMBER,
                        description="Monto del ingreso extra en COP"
                    ),
                    "description": types.Schema(
                        type=types.Type.STRING,
                        description="Descripción del ingreso (ej: 'venta de celular', 'freelance'). Opcional."
                    )
                },
                required=["amount"]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_extra_incomes",
            description="Lista todos los ingresos extras del mes con fecha y descripción. Usa cuando digan 'ver ingresos extras', 'qué extras he tenido'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "month": types.Schema(
                        type=types.Type.INTEGER,
                        description="Mes (1-12). Opcional, default mes actual"
                    ),
                    "year": types.Schema(
                        type=types.Type.INTEGER,
                        description="Año. Opcional, default año actual"
                    )
                },
                required=[]
            )
        ),
        
        types.FunctionDeclaration(
            name="get_income_summary",
            description="Resumen de ingresos del mes: salario fijo + extras = total. Usa cuando pregunten 'cuánto he ganado', 'mis ingresos', 'resumen de ingresos'.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "month": types.Schema(
                        type=types.Type.INTEGER,
                        description="Mes (1-12). Opcional"
                    ),
                    "year": types.Schema(
                        type=types.Type.INTEGER,
                        description="Año. Opcional"
                    )
                },
                required=[]
            )
        ),

        types.FunctionDeclaration(
            name="update_income",
            description="Actualiza un ingreso (salario o extra). Requiere ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID del ingreso"),
                    "amount": types.Schema(type=types.Type.NUMBER, description="Nuevo monto (opcional)"),
                    "description": types.Schema(type=types.Type.STRING, description="Nueva descripción (opcional)")
                },
                required=["id"]
            )
        ),

        types.FunctionDeclaration(
            name="delete_income",
            description="Elimina un ingreso (salario o extra) por su ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "id": types.Schema(type=types.Type.INTEGER, description="ID del ingreso a eliminar")
                },
                required=["id"]
            )
        ),
        
        # === RECORDATORIOS PERSONALIZADOS ===
        types.FunctionDeclaration(
            name="add_reminder",
            description="Crea un recordatorio personalizado. Usa cuando digan 'recuérdame X', 'avísame X', 'recordatorio para X'. El mensaje se enviará en la fecha/hora indicada y luego se elimina automáticamente.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "message": types.Schema(
                        type=types.Type.STRING,
                        description="Mensaje del recordatorio (ej: 'Debes agendar clases de inglés')"
                    ),
                    "remind_at": types.Schema(
                        type=types.Type.STRING,
                        description="Fecha y hora en formato ISO 8601 CON zona horaria Colombia (ej: '2026-02-23T16:00:00-05:00'). SIEMPRE incluye '-05:00' al final. Calcula la fecha/hora a partir de lo que diga el usuario (ej: 'mañana a las 4 PM', 'en 20 minutos', 'el viernes a las 10 AM'). Si no especifica hora, usa 09:00. Para 'en X minutos/horas', suma X a la hora actual."
                    )
                },
                required=["message", "remind_at"]
            )
        )
    ]
)


async def execute_function(function_name: str, function_args: dict, chat_id: str = None) -> str:
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
            
        elif function_name == "update_expense":
            return update_expense(
                expense_id=function_args.get("expense_id"),
                amount=function_args.get("amount"),
                description=function_args.get("description"),
                category=function_args.get("category")
            )["message"]
            
        elif function_name == "delete_expense":
            return delete_expense(expense_id=function_args.get("expense_id"))["message"]
        
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

        elif function_name == "update_recurring_expense":
            return update_recurring_expense(
                id=function_args.get("id"),
                description=function_args.get("description"),
                amount=function_args.get("amount"),
                day_of_month=function_args.get("day_of_month"),
                category=function_args.get("category")
            )["message"]
            
        elif function_name == "delete_recurring_expense":
            return delete_recurring_expense(id=function_args.get("id"))["message"]
        
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
        
        elif function_name == "unmark_bill_paid":
            recurring_id = function_args.get("recurring_expense_id")
            result = unmark_payment_done(recurring_id)
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
                return f"❌ No encontré ningún gasto fijo con el nombre '{description}'."
        
        elif function_name == "find_recurring_by_name_for_unmark":
            description = function_args.get("description")
            recurring_id = find_recurring_by_name(description)
            
            if recurring_id:
                # Automáticamente desmarcar
                result = unmark_payment_done(recurring_id)
                return result["message"]
            else:
                return f"❌ No encontré ningún gasto fijo con el nombre '{description}'."
        
        # === FUNCIÓN OPTIMIZADA ===
        elif function_name == "get_financial_summary":
            budget = function_args.get("budget")
            return get_financial_summary(budget)
        
        # === METAS DE AHORRO ===
        elif function_name == "add_savings_goal":
            result = add_savings_goal(
                name=function_args.get("name"),
                target_amount=function_args.get("target_amount"),
                deadline=function_args.get("deadline"),
                category=function_args.get("category", "general")
            )
            return result["message"]
        
        elif function_name == "get_savings_goals":
            return get_savings_goals()

        elif function_name == "update_savings_goal":
            return update_savings_goal(
                id=function_args.get("id"),
                name=function_args.get("name"),
                target_amount=function_args.get("target_amount"),
                deadline=function_args.get("deadline")
            )["message"]
            
        elif function_name == "delete_savings_goal":
            return delete_savings_goal(id=function_args.get("id"))["message"]
        
        elif function_name == "add_contribution_to_savings":
            goal_name = function_args.get("goal_name")
            amount = function_args.get("amount")
            description = function_args.get("description", "")
            
            goal_id = find_savings_goal_by_name(goal_name)
            
            if goal_id:
                result = add_contribution_to_goal(goal_id, amount, description)
                return result["message"]
            else:
                return f"❌ No encontré ninguna meta con el nombre '{goal_name}'."
        
        # === ANÁLISIS PREDICTIVO ===
        elif function_name == "get_spending_prediction":
            category = function_args.get("category")
            return get_spending_prediction(category)
        
        elif function_name == "get_financial_insights":
            return get_financial_insights()
        
        # === INGRESOS ===
        elif function_name == "set_fixed_salary":
            amount = function_args.get("amount")
            result = set_fixed_salary(amount)
            return result["message"]
        
        elif function_name == "add_extra_income":
            amount = function_args.get("amount")
            description = function_args.get("description", "")
            result = add_extra_income(amount, description)
            return result["message"]
        
        elif function_name == "get_extra_incomes":
            month = function_args.get("month")
            year = function_args.get("year")
            return get_extra_incomes(month, year)
        
        elif function_name == "get_income_summary":
            month = function_args.get("month")
            year = function_args.get("year")
            return get_income_summary(month, year)

        elif function_name == "update_income":
            return update_income(
                id=function_args.get("id"),
                amount=function_args.get("amount"),
                description=function_args.get("description")
            )["message"]
            
        elif function_name == "delete_income":
            return delete_income(id=function_args.get("id"))["message"]
        
        # === RECORDATORIOS PERSONALIZADOS ===
        elif function_name == "add_reminder":
            message = function_args.get("message")
            remind_at = function_args.get("remind_at")
            # Usar el chat_id del usuario que envió el mensaje
            if not chat_id:
                from settings import REMINDER_CHAT_ID
                chat_id = REMINDER_CHAT_ID
            result = add_reminder(message=message, remind_at=remind_at, chat_id=str(chat_id))
            return result["message"]
            
        else:
            logger.warning(f"⚠️ Función desconocida: {function_name}")
            return "⚠️ No puedo procesar esa solicitud en este momento."
    
    except Exception as e:
        logger.error(f"Error ejecutando función {function_name}: {e}")
        return f"❌ Error ejecutando {function_name}: {str(e)}"


logger.info("✅ Herramientas de Gemini configuradas correctamente")
