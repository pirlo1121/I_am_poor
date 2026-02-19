import os
import functools
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import calendar
from supabase import create_client, Client
from config import logger, SUPABASE_URL, SUPABASE_KEY

# ============================================
# CONFIGURACIÓN GLOBAL
# ============================================

# Inicializar cliente Supabase globalmente (Singleton implícito)
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Retorna la instancia global del cliente Supabase."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
             raise ValueError("⚠️ SUPABASE_URL y SUPABASE_KEY son requeridos en .env")
        try:
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Conexión a Supabase inicializada")
        except Exception as e:
            logger.error(f"❌ Error conectando a Supabase: {e}")
            raise
    return _supabase_client

def safe_db_operation(operation: str) -> Dict:
    """
    Decorador/Helper para manejar errores de base de datos de forma centralizada.
    Executa una función y maneja excepciones estándar.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error en {operation}: {e}")
                return {
                    "success": False, 
                    "message": f"❌ Error al procesar {operation}: {str(e)}",
                    "data": None
                }
        return wrapper
    return decorator

# ============================================
# GASTOS VARIABLES (expenses)
# ============================================

@safe_db_operation("registrar gasto")
def add_expense(amount: float, description: str, category: str) -> Dict:
    """Registra un nuevo gasto."""
    client = get_supabase_client()
    data = {
        "amount": float(amount),
        "description": description.strip(),
        "category": category.strip().lower()
    }
    response = client.table("gastos").insert(data).execute()
    logger.info(f"✅ Gasto registrado: ${amount} - {description}")
    return {
        "success": True, 
        "message": f"✅ Gasto registrado: ${amount:,.0f} en {category}",
        "data": response.data
    }

def get_recent_expenses(limit: int = 5) -> str:
    """Obtiene los últimos gastos registrados."""
    try:
        client = get_supabase_client()
        response = client.table("gastos").select("*").order("created_at", desc=True).limit(limit).execute()
        
        if not response.data:
            return "📭 No tienes gastos registrados recientemente."
            
        result = f"📊 **Últimos {len(response.data)} gastos:**\n\n"
        for idx, expense in enumerate(response.data, 1):
            date_str = expense.get("created_at", "").split("T")[0]
            result += f"{idx}. 💰 ${expense['amount']:,.0f} - {expense['description']}\n"
            result += f"   🏷️ {expense['category'].title()} - 📅 {date_str} (ID: {expense['id']})\n\n"
            
        return result
    except Exception as e:
        logger.error(f"Error getting expenses: {e}")
        return "❌ Error al consultar gastos."

@safe_db_operation("actualizar gasto")
def update_expense(expense_id: int, amount: float = None, description: str = None, category: str = None) -> Dict:
    """Actualiza un gasto existente."""
    client = get_supabase_client()
    updates = {}
    if amount is not None: updates["amount"] = float(amount)
    if description: updates["description"] = description.strip()
    if category: updates["category"] = category.strip().lower()
    
    if not updates:
        return {"success": False, "message": "⚠️ Nada para actualizar."}
        
    response = client.table("gastos").update(updates).eq("id", expense_id).execute()
    if not response.data:
        return {"success": False, "message": f"❌ No encontrado ID {expense_id}"}
    return {"success": True, "message": f"✅ Gasto actualizado (ID: {expense_id})"}

@safe_db_operation("eliminar gasto")
def delete_expense(expense_id: int) -> Dict:
    """Elimina un gasto."""
    client = get_supabase_client()
    response = client.table("gastos").delete().eq("id", expense_id).execute()
    if not response.data:
        return {"success": False, "message": f"❌ No encontrado ID {expense_id}"}
    
    item = response.data[0]
    return {"success": True, "message": f"🗑️ Gasto eliminado: {item.get('description')} (${item.get('amount',0):,.0f})"}

# ============================================
# CONSULTAS POR TIEMPO
# ============================================

def get_expenses_by_day(date_str: str = None) -> str:
    """Gastos de un día específico."""
    try:
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        client = get_supabase_client()
        # Filtro de fecha para el día completo (UTC conversion consideration may be needed depending on DB)
        # Asumiendo DATE o timestamp simple por ahora
        start = f"{date_str}T00:00:00"
        end = f"{date_str}T23:59:59"
        
        response = client.table("gastos").select("*")\
            .gte("created_at", start)\
            .lte("created_at", end)\
            .order("created_at", desc=True).execute()
            
        if not response.data:
            return f"📅 No hay gastos registrados para el {date_str}."
            
        total = sum(e['amount'] for e in response.data)
        result = f"📅 **Gastos del {date_str}:**\n\n"
        for e in response.data:
            result += f"• ${e['amount']:,.0f} - {e['description']} ({e['category']}) [ID:{e['id']}]\n"
        
        result += f"\n💰 **Total: ${total:,.0f}**"
        return result
    except Exception as e:
        logger.error(f"Error daily expenses: {e}")
        return "❌ Error consultando gastos del día."

def get_expenses_by_week() -> str:
    """Gastos de los últimos 7 días."""
    try:
        end = datetime.now()
        start = end - timedelta(days=7)
        client = get_supabase_client()
        
        response = client.table("gastos").select("*")\
            .gte("created_at", start.isoformat())\
            .lte("created_at", end.isoformat())\
            .execute()
            
        if not response.data:
             return "📅 No hay gastos en los últimos 7 días."
             
        total = sum(e['amount'] for e in response.data)
        return f"📅 **Gastos (últimos 7 días):** ${total:,.0f} COP"
    except Exception as e:
        return f"❌ Error: {e}"

def get_expenses_by_month(month: int = None, year: int = None) -> str:
    """Gastos de un mes."""
    try:
        now = datetime.now()
        month = int(month) if month else now.month
        year = int(year) if year else now.year
        
        _, last_day = calendar.monthrange(year, month)
        start = f"{year}-{month:02d}-01T00:00:00"
        end = f"{year}-{month:02d}-{last_day}T23:59:59"
        
        client = get_supabase_client()
        response = client.table("gastos").select("*").gte("created_at", start).lte("created_at", end).execute()
        
        if not response.data:
            return f"📅 Sin gastos en {month}/{year}."
            
        total = sum(e['amount'] for e in response.data)
        
        # Agrupar por categoría
        cats = {}
        for e in response.data:
            c = e['category']
            cats[c] = cats.get(c, 0) + e['amount']
            
        result = f"📅 **Resumen {month}/{year}**\n💰 Total: ${total:,.0f}\n\n"
        for c, amt in sorted(cats.items(), key=lambda x: x[1], reverse=True):
             result += f"• {c.title()}: ${amt:,.0f}\n"
             
        return result
    except Exception as e:
        return f"❌ Error: {e}"

# ============================================
# ANÁLISIS
# ============================================

def get_category_summary() -> str:
    """Resumen histórico por categorías."""
    try:
        client = get_supabase_client()
        # Supabase free tier doesn't support complex aggregations easily via simple JS client sometimes,
        # but Python client returns all data if not too large. Ideally use RPC.
        # For optimization, we fetch minimal fields.
        response = client.table("gastos").select("category,amount").execute()
        
        if not response.data:
            return "📭 No hay datos suficientes."
            
        cats = {}
        total_global = 0
        for e in response.data:
            c = e['category'] or "otros"
            amt = e['amount']
            cats[c] = cats.get(c, 0) + amt
            total_global += amt
            
        result = "📊 **Gastos por Categoría (Histórico):**\n\n"
        for c, amt in sorted(cats.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total_global * 100) if total_global > 0 else 0
            result += f"• **{c.title()}**: ${amt:,.0f} ({pct:.1f}%)\n"
            
        return result
    except Exception as e:
        return f"❌ Error generando resumen: {e}"

# ============================================
# GASTOS FIJOS (RECURRING)
# ============================================

@safe_db_operation("registrar gasto fijo")
def add_recurring_expense(description: str, amount: float, category: str, day_of_month: int) -> Dict:
    client = get_supabase_client()
    data = {
        "description": description.strip(),
        "amount": float(amount),
        "category": category.strip().lower(),
        "day_of_month": int(day_of_month),
        "active": True
    }
    client.table("gastos_fijos").insert(data).execute()
    return {"success": True, "message": f"✅ Gasto fijo registrado: {description} (${amount:,.0f}) día {day_of_month}"}

def get_recurring_expenses() -> str:
    try:
        client = get_supabase_client()
        response = client.table("gastos_fijos").select("*").eq("active", True).order("day_of_month").execute()
        
        if not response.data:
             return "📋 No tienes gastos fijos activos."
             
        result = "**Gastos Fijos Activos:**\n\n"
        total = 0
        for e in response.data:
            result += f"• Día {e['day_of_month']}: {e['description']} - ${e['amount']:,.0f} [ID:{e['id']}]\n"
            total += e['amount']
        result += f"\n💰 Total Mensual Fijo: ${total:,.0f}"
        return result
    except Exception as e:
        return f"❌ Error: {e}"

@safe_db_operation("actualizar gasto fijo")
def update_recurring_expense(id: int, description: str = None, amount: float = None, day_of_month: int = None, category: str = None) -> Dict:
    client = get_supabase_client()
    updates = {}
    if description: updates["description"] = description.strip()
    if amount: updates["amount"] = float(amount)
    if day_of_month: updates["day_of_month"] = int(day_of_month)
    if category: updates["category"] = category.strip().lower()

    if not updates: return {"success": False, "message": "⚠️ Nada para actualizar."}

    response = client.table("gastos_fijos").update(updates).eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ No encontrado ID {id}"}
    return {"success": True, "message": f"✅ Gasto fijo actualizado (ID: {id})"}

@safe_db_operation("eliminar gasto fijo")
def delete_recurring_expense(id: int) -> Dict:
    client = get_supabase_client()
    # Logical delete
    response = client.table("gastos_fijos").update({"active": False}).eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ No encontrado ID {id}"}
    return {"success": True, "message": f"🗑️ Gasto fijo desactivado (ID: {id})"}

# ============================================
# PAGOS (Bills)
# ============================================

def get_pending_payments() -> str:
    """Facturas pendientes del mes actual."""
    try:
        now = datetime.now()
        client = get_supabase_client()
        
        # 1. Obtener gastos fijos activos
        recurring = client.table("gastos_fijos").select("*").eq("active", True).execute().data
        if not recurring: return "✅ No tienes gastos fijos configurados."
        
        # 2. Obtener pagos ya realizados este mes
        paid = client.table("pagos_realizados").select("gasto_fijo_id")\
            .eq("month", now.month).eq("year", now.year).execute().data
        paid_ids = {p['gasto_fijo_id'] for p in paid}
        
        # 3. Filtrar pendientes
        pending = [r for r in recurring if r['id'] not in paid_ids]
        
        if not pending: return "🎉 ¡Todo pagado este mes!"
        
        result = "⚠️ **Facturas Pendientes:**\n\n"
        total = 0
        pending.sort(key=lambda x: x['day_of_month'])
        
        for p in pending:
            result += f"• Día {p['day_of_month']}: {p['description']} (${p['amount']:,.0f}) [ID:{p['id']}]\n"
            total += p['amount']
            
        result += f"\n💰 Total pendiente: ${total:,.0f}"
        return result
    except Exception as e:
        return f"❌ Error: {e}"

@safe_db_operation("marcar pago")
def mark_payment_done(recurring_id: int) -> Dict:
    client = get_supabase_client()
    now = datetime.now()
    
    # Verificar si existe y monto
    rec = client.table("gastos_fijos").select("amount, description").eq("id", recurring_id).single().execute()
    if not rec.data: return {"success": False, "message": "❌ Gasto fijo no existe."}
    
    # Verificar si ya está pago
    check = client.table("pagos_realizados").select("*")\
        .eq("gasto_fijo_id", recurring_id)\
        .eq("month", now.month).eq("year", now.year).execute()
        
    if check.data: return {"success": True, "message": f"✅ Ya estaba marcado como pagado: {rec.data['description']}"}
    
    # Registrar pago (paid_at se maneja con DEFAULT NOW() en el schema)
    data = {
        "gasto_fijo_id": recurring_id,
        "amount": rec.data['amount'],
        "month": now.month,
        "year": now.year
    }
    client.table("pagos_realizados").insert(data).execute()
    return {"success": True, "message": f"✅ Marcado como pagado: {rec.data['description']}"}

@safe_db_operation("desmarcar pago")
def unmark_payment_done(recurring_id: int) -> Dict:
    client = get_supabase_client()
    now = datetime.now()
    
    response = client.table("pagos_realizados").delete()\
        .eq("gasto_fijo_id", recurring_id)\
        .eq("month", now.month).eq("year", now.year).execute()
        
    if not response.data: return {"success": False, "message": "❌ No se encontró pago registrado este mes para desmarcar."}
    return {"success": True, "message": "✅ Pago desmarcado/revertido."}

# ============================================
# UTILS (Helpers for AI)
# ============================================

def find_recurring_by_name(name: str) -> Optional[int]:
    """Busca ID por coincidencia de nombre."""
    try:
        client = get_supabase_client()
        # Búsqueda simple (ilike si fuera SQL directo, aquí filtramos en memoria o exacto)
        # Supabase py client ilike support:
        recurrings = client.table("gastos_fijos").select("id, description").eq("active", True).execute().data
        
        name_lower = name.lower()
        for r in recurrings:
            if name_lower in r['description'].lower():
                return r['id']
        return None
    except:
        return None

# ============================================
# METAS DE AHORRO
# ============================================

@safe_db_operation("crear meta")
def add_savings_goal(name: str, target_amount: float, deadline: str = None, category: str = "general") -> Dict:
    client = get_supabase_client()
    data = {
        "name": name.strip(),
        "target_amount": float(target_amount),
        "current_amount": 0.0,
        "category": category.lower(),
        "active": True
    }
    if deadline: data["deadline"] = deadline
    
    client.table("savings_goals").insert(data).execute()
    
    suggestion = ""
    if deadline:
        try:
            d_date = datetime.strptime(deadline, "%Y-%m-%d")
            months = max(1, (d_date.year - datetime.now().year) * 12 + d_date.month - datetime.now().month)
            monthly = target_amount / months
            suggestion = f"\n💡 Ahorra ${monthly:,.0f}/mes x {months} meses."
        except: pass
        
    return {"success": True, "message": f"🎯 Meta creada: {name} (${target_amount:,.0f}){suggestion}"}

def get_savings_goals() -> str:
    try:
        client = get_supabase_client()
        goals = client.table("savings_goals").select("*").eq("active", True).execute().data
        
        if not goals: return "🎯 No tienes metas de ahorro activas."
        
        result = "🎯 **Metas de Ahorro:**\n\n"
        for g in goals:
            pct = (g['current_amount'] / g['target_amount'] * 100) if g['target_amount'] > 0 else 0
            bar = "█" * int(pct/10) + "░" * (10 - int(pct/10))
            result += f"**{g['name']}** (ID: {g['id']})\n"
            result += f"💰 ${g['current_amount']:,.0f} / ${g['target_amount']:,.0f} ({pct:.1f}%)\n"
            result += f"[{bar}]\n\n"
            
        return result
    except Exception as e:
        return f"❌ Error: {e}"

@safe_db_operation("actualizar meta")
def update_savings_goal(id: int, name: str = None, target_amount: float = None, deadline: str = None) -> Dict:
    client = get_supabase_client()
    updates = {}
    if name: updates["name"] = name.strip()
    if target_amount: updates["target_amount"] = float(target_amount)
    if deadline: updates["deadline"] = deadline
    
    if not updates: return {"success": False, "message": "⚠️ Nada para actualizar."}
    
    response = client.table("savings_goals").update(updates).eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ Meta no encontrada ID {id}"}
    return {"success": True, "message": f"✅ Meta actualizada (ID: {id})"}

@safe_db_operation("eliminar meta")
def delete_savings_goal(id: int) -> Dict:
    client = get_supabase_client()
    response = client.table("savings_goals").update({"active": False}).eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ Meta no encontrada ID {id}"}
    return {"success": True, "message": f"🗑️ Meta eliminada (ID: {id})"}

@safe_db_operation("aportar ahorro")
def add_contribution_to_goal(goal_id: int, amount: float, description: str = "") -> Dict:
    # Nota: Esto requiere lógica transaccional idealmente, pero haremos simple update + insert
    client = get_supabase_client()
    
    # 1. Get current
    goal = client.table("savings_goals").select("current_amount, name").eq("id", goal_id).single().execute()
    if not goal.data: return {"success": False, "message": "❌ Meta no encontrada."}
    
    new_total = goal.data['current_amount'] + float(amount)
    
    # 2. Update goal
    client.table("savings_goals").update({"current_amount": new_total}).eq("id", goal_id).execute()
    
    # 3. Log contribution (opcional, si existiera tabla de historial de ahorros)
    
    return {"success": True, "message": f"✅ Aporte de ${amount:,.0f} a '{goal.data['name']}'. Nuevo total: ${new_total:,.0f}"}

def find_savings_goal_by_name(name: str) -> Optional[int]:
    try:
        client = get_supabase_client()
        goals = client.table("savings_goals").select("id, name").eq("active", True).execute().data
        for g in goals:
            if name.lower() in g['name'].lower():
                return g['id']
        return None
    except: return None

# ============================================
# INGRESOS (Income)
# ============================================

@safe_db_operation("definir salario")
def set_fixed_salary(amount: float) -> Dict:
    client = get_supabase_client()
    now = datetime.now()
    
    # Check si ya existe salario este mes (tipo 'salary')
    existing = client.table("ingresos").select("id")\
        .eq("month", now.month).eq("year", now.year).eq("type", "salary").execute()
    
    data = {"amount": float(amount), "type": "salary", "description": "Salario Fijo", "month": now.month, "year": now.year}
    
    if existing.data:
        client.table("ingresos").update(data).eq("id", existing.data[0]['id']).execute()
        msg = "✅ Salario actualizado"
    else:
        client.table("ingresos").insert(data).execute()
        msg = "✅ Salario registrado"
        
    return {"success": True, "message": f"{msg}: ${amount:,.0f}"}

@safe_db_operation("ingreso extra")
def add_extra_income(amount: float, description: str = "") -> Dict:
    client = get_supabase_client()
    now = datetime.now()
    data = {
        "amount": float(amount),
        "type": "extra",
        "description": description or "Ingreso Extra",
        "month": now.month,
        "year": now.year
    }
    client.table("ingresos").insert(data).execute()
    return {"success": True, "message": f"✅ Extra registrado: ${amount:,.0f} ({description})"}

def get_income_summary(month: int = None, year: int = None) -> str:
    try:
        now = datetime.now()
        m = month or now.month
        y = year or now.year
        client = get_supabase_client()
        
        incomes = client.table("ingresos").select("*").eq("month", m).eq("year", y).execute().data
        if not incomes: return f"📉 No hay ingresos registrados en {m}/{y}."
        
        salary = sum(i['amount'] for i in incomes if i['type'] == 'salary')
        extras = sum(i['amount'] for i in incomes if i['type'] == 'extra')
        
        return f"💰 **Ingresos {m}/{y}:**\n\n🏢 Salario: ${salary:,.0f}\n💸 Extras: ${extras:,.0f}\n🚀 **TOTAL: ${salary+extras:,.0f}**"
    except Exception as e:
        return f"❌ Error: {e}"

def get_extra_incomes(month: int = None, year: int = None) -> str:
    """Lista detallada de ingresos extras del mes."""
    try:
        now = datetime.now()
        m = month or now.month
        y = year or now.year
        client = get_supabase_client()
        
        extras = client.table("ingresos").select("*").eq("month", m).eq("year", y).eq("type", "extra").order("created_at", desc=True).execute().data
        if not extras:
            return f"📭 No hay ingresos extras registrados en {m}/{y}."
        
        total = sum(e['amount'] for e in extras)
        result = f"💸 **Ingresos Extras {m}/{y}:**\n\n"
        for idx, e in enumerate(extras, 1):
            date_str = e.get("created_at", "").split("T")[0]
            result += f"{idx}. ${e['amount']:,.0f} - {e.get('description', 'Sin descripción')} ({date_str})\n"
        result += f"\n💰 **Total extras: ${total:,.0f}**"
        return result
    except Exception as e:
        return f"❌ Error: {e}"

@safe_db_operation("actualizar ingreso")
def update_income(id: int, amount: float = None, description: str = None) -> Dict:
    client = get_supabase_client()
    updates = {}
    if amount: updates["amount"] = float(amount)
    if description: updates["description"] = description.strip()
    if not updates: return {"success": False, "message": "⚠️ Nada para actualizar."}
    
    response = client.table("ingresos").update(updates).eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ ID {id} no encontrado."}
    return {"success": True, "message": f"✅ Ingreso actualizado (ID: {id})"}

@safe_db_operation("eliminar ingreso")
def delete_income(id: int) -> Dict:
    client = get_supabase_client()
    response = client.table("ingresos").delete().eq("id", id).execute()
    if not response.data: return {"success": False, "message": f"❌ ID {id} no encontrado."}
    return {"success": True, "message": f"🗑️ Ingreso eliminado (ID: {id})"}


# ============================================
# AGGREGATE SUMMARY (Legacy support + Optimized)
# ============================================

def get_financial_summary(budget: float = None) -> str:
    """Resumen completo."""
    try:
        # Aquí llamarías a las funciones de arriba o harías una query unificada.
        # Por brevedad, reutilizamos logic existente:
        now = datetime.now()
        exp_str = get_expenses_by_month(now.month, now.year) # Contains total expenses
        bills_str = get_pending_payments()
        inc_str = get_income_summary(now.month, now.year)
        
        return f"📊 **BALANCE GENERAL**\n\n{inc_str}\n\n{exp_str}\n\n{bills_str}"
    except Exception as e:
        return f"❌ Error: {e}"

# ============================================
# CONSULTAS AVANZADAS
# ============================================

def get_expenses_by_category(cat: str) -> str:
    """Gastos de una categoría específica en el mes actual."""
    try:
        now = datetime.now()
        _, last_day = calendar.monthrange(now.year, now.month)
        start = f"{now.year}-{now.month:02d}-01T00:00:00"
        end = f"{now.year}-{now.month:02d}-{last_day}T23:59:59"
        
        client = get_supabase_client()
        response = client.table("gastos").select("*")\
            .eq("category", cat.lower())\
            .gte("created_at", start).lte("created_at", end)\
            .order("created_at", desc=True).execute()
        
        if not response.data:
            return f"📭 No hay gastos en '{cat}' este mes ({now.month}/{now.year})."
        
        total = sum(e['amount'] for e in response.data)
        result = f"📊 **Gastos en {cat.title()} ({now.month}/{now.year}):**\n\n"
        for e in response.data:
            date_str = e.get("created_at", "").split("T")[0]
            result += f"• ${e['amount']:,.0f} - {e['description']} ({date_str})\n"
        result += f"\n💰 **Total: ${total:,.0f}** ({len(response.data)} gastos)"
        return result
    except Exception as e:
        return f"❌ Error: {e}"


def get_paid_payments() -> str:
    """Facturas ya pagadas del mes actual."""
    try:
        now = datetime.now()
        client = get_supabase_client()
        
        paid = client.table("pagos_realizados").select("*, gastos_fijos(description, amount, day_of_month)")\
            .eq("month", now.month).eq("year", now.year).execute().data
        
        if not paid:
            return "📭 No has pagado ninguna factura este mes."
        
        result = "✅ **Facturas Pagadas este mes:**\n\n"
        total = 0
        for p in paid:
            gf = p.get('gastos_fijos', {})
            desc = gf.get('description', 'Desconocido') if gf else 'Desconocido'
            amt = p.get('amount', 0)
            date_str = p.get('paid_at', '').split('T')[0] if p.get('paid_at') else ''
            result += f"• ✅ {desc} - ${amt:,.0f} (pagado: {date_str})\n"
            total += amt
        
        result += f"\n💰 **Total pagado: ${total:,.0f}**"
        return result
    except Exception as e:
        return f"❌ Error: {e}"


def get_all_monthly_bills() -> str:
    """Vista completa de todas las mensualidades: pagadas + pendientes."""
    try:
        now = datetime.now()
        client = get_supabase_client()
        
        # Gastos fijos activos
        recurring = client.table("gastos_fijos").select("*").eq("active", True).order("day_of_month").execute().data
        if not recurring:
            return "📋 No tienes gastos fijos configurados."
        
        # Pagos realizados este mes
        paid = client.table("pagos_realizados").select("gasto_fijo_id, paid_at")\
            .eq("month", now.month).eq("year", now.year).execute().data
        paid_map = {p['gasto_fijo_id']: p.get('paid_at', '').split('T')[0] for p in paid}
        
        total_fijo = 0
        total_pagado = 0
        result = f"📋 **Mensualidades {now.month}/{now.year}:**\n\n"
        
        for r in recurring:
            is_paid = r['id'] in paid_map
            status = "✅" if is_paid else "⏰"
            extra = f" (pagado: {paid_map[r['id']]})" if is_paid else f" (vence día {r['day_of_month']})"
            result += f"{status} {r['description']} - ${r['amount']:,.0f}{extra}\n"
            total_fijo += r['amount']
            if is_paid:
                total_pagado += r['amount']
        
        pendiente = total_fijo - total_pagado
        result += f"\n💰 Total fijo: ${total_fijo:,.0f}\n"
        result += f"✅ Pagado: ${total_pagado:,.0f}\n"
        result += f"⏰ Pendiente: ${pendiente:,.0f}"
        return result
    except Exception as e:
        return f"❌ Error: {e}"


def get_spending_prediction(cat: str = None) -> str:
    """Proyecta gastos del mes basándose en promedio de últimos 3 meses."""
    try:
        now = datetime.now()
        client = get_supabase_client()
        
        # Recopilar datos de los últimos 3 meses
        monthly_totals = []
        for i in range(1, 4):
            m = now.month - i
            y = now.year
            if m <= 0:
                m += 12
                y -= 1
            _, last_day = calendar.monthrange(y, m)
            start = f"{y}-{m:02d}-01T00:00:00"
            end = f"{y}-{m:02d}-{last_day}T23:59:59"
            
            query = client.table("gastos").select("amount")
            if cat:
                query = query.eq("category", cat.lower())
            data = query.gte("created_at", start).lte("created_at", end).execute().data
            total = sum(e['amount'] for e in data) if data else 0
            monthly_totals.append({"month": m, "year": y, "total": total})
        
        if not any(t['total'] > 0 for t in monthly_totals):
            return "📭 No hay datos suficientes para predecir (se necesita al menos 1 mes previo)."
        
        avg = sum(t['total'] for t in monthly_totals) / len(monthly_totals)
        
        # Gastos actuales del mes
        _, last_day_now = calendar.monthrange(now.year, now.month)
        start_now = f"{now.year}-{now.month:02d}-01T00:00:00"
        end_now = f"{now.year}-{now.month:02d}-{last_day_now}T23:59:59"
        query_now = client.table("gastos").select("amount")
        if cat:
            query_now = query_now.eq("category", cat.lower())
        current_data = query_now.gte("created_at", start_now).lte("created_at", end_now).execute().data
        current_total = sum(e['amount'] for e in current_data) if current_data else 0
        
        # Proyección lineal
        days_passed = now.day
        days_in_month = last_day_now
        projected = (current_total / days_passed * days_in_month) if days_passed > 0 else 0
        
        cat_label = f" en {cat.title()}" if cat else ""
        result = f"🔮 **Proyección de Gastos{cat_label}:**\n\n"
        result += f"📊 Promedio últimos 3 meses: ${avg:,.0f}\n"
        for t in monthly_totals:
            result += f"   • {t['month']}/{t['year']}: ${t['total']:,.0f}\n"
        result += f"\n📅 Mes actual (día {days_passed}/{days_in_month}): ${current_total:,.0f}\n"
        result += f"🔮 Proyectado fin de mes: ${projected:,.0f}\n"
        
        if projected > avg * 1.2:
            result += "\n⚠️ Vas un 20%+ por encima del promedio. ¡Cuidado!"
        elif projected < avg * 0.8:
            result += "\n🎉 Vas por debajo del promedio. ¡Buen trabajo!"
        else:
            result += "\n📈 Vas en línea con tu promedio habitual."
        
        return result
    except Exception as e:
        return f"❌ Error: {e}"


def get_financial_insights() -> str:
    """Genera insights y análisis financieros automáticos."""
    try:
        now = datetime.now()
        client = get_supabase_client()
        
        # Datos del mes actual
        _, last_day = calendar.monthrange(now.year, now.month)
        start = f"{now.year}-{now.month:02d}-01T00:00:00"
        end = f"{now.year}-{now.month:02d}-{last_day}T23:59:59"
        
        expenses = client.table("gastos").select("amount, category").gte("created_at", start).lte("created_at", end).execute().data
        
        if not expenses:
            return "📭 No hay datos suficientes para generar insights este mes."
        
        # Análisis por categoría
        cats = {}
        total = 0
        for e in expenses:
            c = e['category']
            cats[c] = cats.get(c, 0) + e['amount']
            total += e['amount']
        
        top_cat = max(cats, key=cats.get)
        top_amount = cats[top_cat]
        top_pct = (top_amount / total * 100) if total > 0 else 0
        
        # Mes anterior para comparación
        prev_m = now.month - 1
        prev_y = now.year
        if prev_m <= 0:
            prev_m = 12
            prev_y -= 1
        _, prev_last_day = calendar.monthrange(prev_y, prev_m)
        prev_start = f"{prev_y}-{prev_m:02d}-01T00:00:00"
        prev_end = f"{prev_y}-{prev_m:02d}-{prev_last_day}T23:59:59"
        prev_expenses = client.table("gastos").select("amount").gte("created_at", prev_start).lte("created_at", prev_end).execute().data
        prev_total = sum(e['amount'] for e in prev_expenses) if prev_expenses else 0
        
        # Facturas pendientes
        recurring = client.table("gastos_fijos").select("id, amount").eq("active", True).execute().data or []
        paid = client.table("pagos_realizados").select("gasto_fijo_id").eq("month", now.month).eq("year", now.year).execute().data or []
        paid_ids = {p['gasto_fijo_id'] for p in paid}
        pending_bills = [r for r in recurring if r['id'] not in paid_ids]
        pending_amount = sum(r['amount'] for r in pending_bills)
        
        # Ingresos
        incomes = client.table("ingresos").select("amount").eq("month", now.month).eq("year", now.year).execute().data or []
        total_income = sum(i['amount'] for i in incomes)
        
        result = f"💡 **Insights Financieros - {now.month}/{now.year}:**\n\n"
        result += f"📊 **Gastos totales:** ${total:,.0f} ({len(expenses)} transacciones)\n"
        result += f"🏆 **Mayor gasto:** {top_cat.title()} con ${top_amount:,.0f} ({top_pct:.0f}%)\n"
        
        if prev_total > 0:
            diff = total - prev_total
            pct_diff = (diff / prev_total * 100)
            emoji = "📈" if diff > 0 else "📉"
            result += f"{emoji} **vs. mes anterior:** {'+'if diff > 0 else ''}${diff:,.0f} ({pct_diff:+.1f}%)\n"
        
        if total_income > 0:
            savings_rate = ((total_income - total - pending_amount) / total_income * 100)
            result += f"\n💰 **Ingresos:** ${total_income:,.0f}\n"
            result += f"💸 **Gasto total + pendientes:** ${total + pending_amount:,.0f}\n"
            result += f"📊 **Tasa de ahorro estimada:** {savings_rate:.1f}%\n"
        
        if pending_bills:
            result += f"\n⚠️ **{len(pending_bills)} facturas pendientes** por ${pending_amount:,.0f}"
        else:
            result += "\n🎉 ¡Todas las facturas del mes están pagadas!"
        
        return result
    except Exception as e:
        return f"❌ Error: {e}"


def compare_monthly_expenses(m1: int, y1: int, m2: int, y2: int) -> str:
    """Compara gastos entre dos meses por total y por categoría."""
    try:
        client = get_supabase_client()
        
        def get_month_data(month, year):
            _, last_day = calendar.monthrange(year, month)
            start = f"{year}-{month:02d}-01T00:00:00"
            end = f"{year}-{month:02d}-{last_day}T23:59:59"
            data = client.table("gastos").select("amount, category").gte("created_at", start).lte("created_at", end).execute().data or []
            total = sum(e['amount'] for e in data)
            cats = {}
            for e in data:
                c = e['category']
                cats[c] = cats.get(c, 0) + e['amount']
            return total, cats, len(data)
        
        t1, c1, n1 = get_month_data(int(m1), int(y1))
        t2, c2, n2 = get_month_data(int(m2), int(y2))
        
        diff = t2 - t1
        pct = (diff / t1 * 100) if t1 > 0 else 0
        emoji = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
        
        result = f"⚖️ **Comparación {m1}/{y1} vs {m2}/{y2}:**\n\n"
        result += f"📅 {m1}/{y1}: ${t1:,.0f} ({n1} gastos)\n"
        result += f"📅 {m2}/{y2}: ${t2:,.0f} ({n2} gastos)\n"
        result += f"{emoji} Diferencia: {'+'if diff > 0 else ''}${diff:,.0f} ({pct:+.1f}%)\n\n"
        
        # Comparar por categoría
        all_cats = set(list(c1.keys()) + list(c2.keys()))
        if all_cats:
            result += "📊 **Por categoría:**\n"
            for cat in sorted(all_cats):
                v1 = c1.get(cat, 0)
                v2 = c2.get(cat, 0)
                cat_diff = v2 - v1
                cat_emoji = "🔺" if cat_diff > 0 else "🔻" if cat_diff < 0 else "➡️"
                result += f"{cat_emoji} {cat.title()}: ${v1:,.0f} → ${v2:,.0f} ({'+'if cat_diff > 0 else ''}${cat_diff:,.0f})\n"
        
        return result
    except Exception as e:
        return f"❌ Error: {e}"


# ============================================
# RECORDATORIOS
# ============================================

def check_upcoming_bills(days_ahead: int = 1) -> list:
    """
    Verifica qué facturas vencen en los próximos X días.
    Retorna lista de bills para enviar recordatorios.
    """
    try:
        now = datetime.now()
        target_day = (now + timedelta(days=days_ahead)).day
        
        client = get_supabase_client()
        
        # Gastos fijos que vencen ese día
        recurring = client.table("gastos_fijos").select("*").eq("active", True).eq("day_of_month", target_day).execute().data
        if not recurring:
            return []
        
        # Verificar cuáles NO están pagados este mes
        paid = client.table("pagos_realizados").select("gasto_fijo_id")\
            .eq("month", now.month).eq("year", now.year).execute().data
        paid_ids = {p['gasto_fijo_id'] for p in paid} if paid else set()
        
        unpaid = [r for r in recurring if r['id'] not in paid_ids]
        return unpaid
    except Exception as e:
        logger.error(f"❌ Error checking upcoming bills: {e}")
        return []
