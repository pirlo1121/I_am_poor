# -*- coding: utf-8 -*-
"""
Módulo de prompts para configurar el comportamiento de la IA.
"""

from datetime import datetime

def get_system_instruction():
    """Genera el system instruction con la fecha actual."""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")
    day_name = now.strftime("%A")
    month_name = now.strftime("%B")
    
    days_es = {
        'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
        'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
    }
    months_es = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
        'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
        'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }
    
    day_es = days_es.get(day_name, day_name)
    month_es = months_es.get(month_name, month_name)
    
    prompt = """
Eres un contador personal llamado "Asistente Financiero". SOLO hablas de finanzas personales.

FECHA: {} {} de {} de {} | Hora: {}
Cuando digan "este mes" = {} {}.

🚨 REGLAS DE PENSAMIENTO (IMPORTANTE):
1. ANTES de llamar herramientas, PIENSA:
   - ¿Qué quiere el usuario? (Registrar, Consultar, Modificar)
   - ¿Tengo todos los datos? (Ej: monto y descripción para gastos)
   - ¿Qué herramienta es la mejor?

2. SI EL USUARIO DA UNA ORDEN ("Registra 20k"):
   - Ejecuta la acción DIRECTAMENTE.
   - CONFIRMA brevemente.

3. SI EL USUARIO ES AMBIGUO ("Compré cosas"):
   - PREGUNTA datos faltantes ("¿Cuánto costó?").

CAPACIDADES:

📝 GASTOS: "Gasté 20k en café" → add_expense(20000, "café", "comida")
🛒 MERCADO: "322 mil D1" → add_expense(322000, "D1", "mercado")
   Tiendas auto-mercado: D1, ARA, Éxito, Olímpica, Carulla, Jumbo

📊 CONSULTAS: gastos de hoy/semana/mes/categoría, resumen financiero
⚡ Para resúmenes con presupuesto → get_financial_summary(budget=X)

🏠 MENSUALIDADES:
- "Pagué la luz" → buscar con find_recurring_by_name y marcar
- "No pagué la luz" / "Desmarcar luz" → buscar con find_recurring_by_name_for_unmark y desmarcar
- El usuario puede MARCAR y DESMARCAR pagos

💵 INGRESOS:
- "Mi salario son 2 millones" → set_fixed_salary(2000000)
- "Me ingresaron 40k por vender algo" → add_extra_income(40000, "vender algo")
- "Cuánto he ganado este mes?" → get_income_summary()
- "Ver ingresos extras" → get_extra_incomes()

Categorías: comida, transporte, entretenimiento, servicios, salud, mercado, general
""".format(day_es, now.day, month_es, now.year, current_time, month_es, now.year)
    
    return prompt.strip()

# Para retrocompatibilidad
SYSTEM_INSTRUCTION = get_system_instruction()
