"""
database.py - Módulo de conexión y operaciones con Supabase (VERSIÓN EXTENDIDA)
Maneja gastos normales, gastos fijos recurrentes, análisis y tracking de pagos.
"""

import os
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de Supabase
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# Cliente de Supabase (inicializado como None)
supabase: Optional[Client] = None


def init_supabase() -> Client:
    """Inicializa y retorna el cliente de Supabase."""
    global supabase
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "Las variables SUPABASE_URL y SUPABASE_KEY deben estar configuradas en .env"
        )
    
    if supabase is None:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("✅ Conexión a Supabase establecida exitosamente")
        except Exception as e:
            logger.error(f"❌ Error al conectar con Supabase: {e}")
            raise
    
    return supabase


# ============================================
# FUNCIONES DE GASTOS NORMALES
# ============================================

def add_expense(amount: float, description: str, category: str) -> Dict:
    """Registra un nuevo gasto en la base de datos."""
    try:
        client = init_supabase()
        
        expense_data = {
            "amount": float(amount),
            "description": description.strip(),
            "category": category.strip().lower()
        }
        
        response = client.table("gastos").insert(expense_data).execute()
        
        logger.info(f"✅ Gasto registrado: ${amount} - {description} ({category})")
        
        return {
            "success": True,
            "message": f"✅ Gasto registrado exitosamente: ${amount:,.0f} COP en {category}",
            "data": response.data
        }
        
    except Exception as e:
        logger.error(f"❌ Error al registrar gasto: {e}")
        return {
            "success": False,
            "message": f"❌ Error al registrar el gasto: {str(e)}",
            "data": None
        }


def get_recent_expenses(limit: int = 5) -> str:
    """Obtiene los gastos más recientes de la base de datos."""
    try:
        client = init_supabase()
        
        response = client.table("gastos") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            return "📭 No hay gastos registrados aún."
        
        result = f"📊 **Últimos {len(expenses)} gastos:**\n\n"
        
        total = 0
        for idx, expense in enumerate(expenses, 1):
            amount = expense.get("amount", 0)
            description = expense.get("description", "Sin descripción")
            category = expense.get("category", "sin categoría")
            created_at = expense.get("created_at", "")
            
            date_str = created_at.split("T")[0] if created_at else "N/A"
            
            result += f"{idx}. 💰 ${amount:,.0f} COP\n"
            result += f"   📝 {description}\n"
            result += f"   🏷️ Categoría: {category.title()}\n"
            result += f"   📅 {date_str}\n\n"
            
            total += amount
        
        result += f"💵 **Total**: ${total:,.0f} COP"
        
        logger.info(f"📊 Consultados {len(expenses)} gastos recientes")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error al consultar gastos: {e}")
        return f"❌ Error al consultar los gastos: {str(e)}"


# ============================================
# NUEVAS FUNCIONES - CONSULTAS POR PERÍODO
# ============================================

def get_expenses_by_day(date: str = None) -> str:
    """
    Obtiene los gastos de un día específico.
    
    Args:
        date (str): Fecha en formato YYYY-MM-DD. Si es None, usa hoy.
    
    Returns:
        str: Gastos del día formateados
    """
    try:
        client = init_supabase()
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Rango del día completo
        start_date = f"{date}T00:00:00"
        end_date = f"{date}T23:59:59"
        
        response = client.table("gastos") \
            .select("*") \
            .gte("created_at", start_date) \
            .lte("created_at", end_date) \
            .order("created_at", desc=True) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            return f"📭 No hay gastos registrados para el {date}"
        
        result = f"📅 **Gastos del {date}:**\n\n"
        
        total = 0
        for idx, expense in enumerate(expenses, 1):
            amount = expense.get("amount", 0)
            description = expense.get("description", "")
            category = expense.get("category", "")
            
            result += f"{idx}. 💰 ${amount:,.0f} - {description} ({category.title()})\n"
            total += amount
        
        result += f"\n💵 **Total del día**: ${total:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar gastos del día: {str(e)}"


def get_expenses_by_week() -> str:
    """Obtiene los gastos de la semana actual (últimos 7 días)."""
    try:
        client = init_supabase()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        response = client.table("gastos") \
            .select("*") \
            .gte("created_at", start_date.isoformat()) \
            .lte("created_at", end_date.isoformat()) \
            .order("created_at", desc=True) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            return "📭 No hay gastos registrados en los últimos 7 días"
        
        result = f"📅 **Gastos de los últimos 7 días:**\n\n"
        
        # Agrupar por día
        by_day = {}
        total_general = 0
        
        for expense in expenses:
            amount = expense.get("amount", 0)
            created_at = expense.get("created_at", "")
            date_key = created_at.split("T")[0] if created_at else "Sin fecha"
            
            if date_key not in by_day:
                by_day[date_key] = []
            
            by_day[date_key].append(expense)
            total_general += amount
        
        # Mostrar por día
        for date_key in sorted(by_day.keys(), reverse=True):
            day_expenses = by_day[date_key]
            day_total = sum(e.get("amount", 0) for e in day_expenses)
            
            result += f"**{date_key}** - ${day_total:,.0f} COP ({len(day_expenses)} gastos)\n"
        
        result += f"\n💵 **Total de la semana**: ${total_general:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar gastos de la semana: {str(e)}"


def get_expenses_by_category(category: str) -> str:
    """Obtiene todos los gastos de una categoría específica."""
    try:
        client = init_supabase()
        
        response = client.table("gastos") \
            .select("*") \
            .eq("category", category.lower()) \
            .order("created_at", desc=True) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            return f"📭 No hay gastos registrados en la categoría '{category.title()}'"
        
        result = f"🏷️ **Gastos en {category.title()}:**\n\n"
        
        total = 0
        for idx, expense in enumerate(expenses, 1):
            amount = expense.get("amount", 0)
            description = expense.get("description", "")
            created_at = expense.get("created_at", "")
            date_str = created_at.split("T")[0] if created_at else "N/A"
            
            result += f"{idx}. 💰 ${amount:,.0f} - {description} ({date_str})\n"
            total += amount
        
        result += f"\n💵 **Total en {category.title()}**: ${total:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar gastos por categoría: {str(e)}"


def get_category_summary() -> str:
    """Obtiene un resumen de gastos por categoría (más a menos gastado)."""
    try:
        client = init_supabase()
        
        response = client.table("gastos").select("*").execute()
        expenses = response.data
        
        if not expenses:
            return "📭 No hay gastos registrados para análisis"
        
        # Agrupar por categoría
        by_category = {}
        total_general = 0
        
        for expense in expenses:
            category = expense.get("category", "sin categoría")
            amount = expense.get("amount", 0)
            
            if category not in by_category:
                by_category[category] = 0
            
            by_category[category] += amount
            total_general += amount
        
        # Ordenar por monto descendente
        sorted_categories = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
        
        result = f"📊 **Análisis por Categorías:**\n\n"
        
        emojis = {
            "comida": "🍔",
            "transporte": "🚕",
            "servicios": "🏠",
            "entretenimiento": "🎮",
            "salud": "💊",
            "general": "📦"
        }
        
        for idx, (category, amount) in enumerate(sorted_categories, 1):
            percentage = (amount / total_general * 100) if total_general > 0 else 0
            emoji = emojis.get(category, "💰")
            
            result += f"{idx}. {emoji} **{category.title()}**: ${amount:,.0f} COP ({percentage:.1f}%)\n"
        
        result += f"\n💵 **Total General**: ${total_general:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al generar resumen: {str(e)}"


# ============================================
# NUEVAS FUNCIONES - GASTOS FIJOS RECURRENTES
# ============================================

def add_recurring_expense(description: str, amount: float, category: str, day_of_month: int) -> Dict:
    """Registra un gasto fijo mensual."""
    try:
        client = init_supabase()
        
        if day_of_month < 1 or day_of_month > 31:
            return {
                "success": False,
                "message": "❌ El día del mes debe estar entre 1 y 31"
            }
        
        recurring_data = {
            "description": description.strip(),
            "amount": float(amount),
            "category": category.strip().lower(),
            "day_of_month": day_of_month,
            "active": True
        }
        
        response = client.table("gastos_fijos").insert(recurring_data).execute()
        
        logger.info(f"✅ Gasto fijo registrado: {description} - ${amount} día {day_of_month}")
        
        return {
            "success": True,
            "message": f"✅ Gasto fijo registrado:\n📝 {description}\n💰 ${amount:,.0f} COP\n📅 Día {day_of_month} de cada mes\n🔔 Te recordaré 1 día antes"
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {
            "success": False,
            "message": f"❌ Error al registrar gasto fijo: {str(e)}"
        }


def get_recurring_expenses() -> str:
    """Lista todos los gastos fijos activos."""
    try:
        client = init_supabase()
        
        response = client.table("gastos_fijos") \
            .select("*") \
            .eq("active", True) \
            .order("day_of_month") \
            .execute()
        
        recurring = response.data
        
        if not recurring:
            return "📭 No tienes gastos fijos registrados"
        
        result = f"📋 **Gastos Fijos Mensuales:**\n\n"
        
        total = 0
        for idx, rec in enumerate(recurring, 1):
            description = rec.get("description", "")
            amount = rec.get("amount", 0)
            day = rec.get("day_of_month", 0)
            category = rec.get("category", "")
            
            result += f"{idx}. 💰 ${amount:,.0f} - {description}\n"
            result += f"   📅 Día {day} de cada mes ({category.title()})\n\n"
            total += amount
        
        result += f"💵 **Total Mensual**: ${total:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar gastos fijos: {str(e)}"


def get_pending_payments() -> str:
    """Obtiene las facturas pendientes del mes actual."""
    try:
        client = init_supabase()
        
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        current_day = now.day
        
        # Obtener todos los gastos fijos activos
        recurring_response = client.table("gastos_fijos") \
            .select("*") \
            .eq("active", True) \
            .execute()
        
        recurring_expenses = recurring_response.data
        
        if not recurring_expenses:
            return "📭 No tienes gastos fijos configurados"
        
        # Obtener pagos ya realizados este mes
        payments_response = client.table("pagos_realizados") \
            .select("*") \
            .eq("month", current_month) \
            .eq("year", current_year) \
            .execute()
        
        paid_ids = {p["gasto_fijo_id"] for p in payments_response.data}
        
        # Filtrar pendientes
        pending = []
        for rec in recurring_expenses:
            rec_id = rec.get("id")
            day = rec.get("day_of_month", 0)
            
            if rec_id not in paid_ids:
                days_until = day - current_day
                rec["days_until"] = days_until
                pending.append(rec)
        
        if not pending:
            return f"✅ ¡Todas las facturas de {now.strftime('%B')} están pagadas!"
        
        # Ordenar por días que faltan
        pending.sort(key=lambda x: x["days_until"])
        
        result = f"📋 **Facturas Pendientes ({now.strftime('%B %Y')}):**\n\n"
        
        total_pending = 0
        for idx, rec in enumerate(pending, 1):
            description = rec.get("description", "")
            amount = rec.get("amount", 0)
            day = rec.get("day_of_month", 0)
            days_until = rec.get("days_until", 0)
            
            if days_until < 0:
                status = f"⚠️ Vencida (hace {abs(days_until)} días)"
            elif days_until == 0:
                status = "🔴 Vence HOY"
            elif days_until == 1:
                status = "🟡 Vence MAÑANA"
            else:
                status = f"⏰ Faltan {days_until} días"
            
            result += f"{idx}. 💰 ${amount:,.0f} - {description}\n"
            result += f"   📅 Vence: {day} de {now.strftime('%B')}\n"
            result += f"   {status}\n\n"
            
            total_pending += amount
        
        result += f"💵 **Total a Pagar**: ${total_pending:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar facturas pendientes: {str(e)}"


def mark_payment_done(recurring_id: int) -> Dict:
    """Marca un gasto fijo como pagado para el mes actual."""
    try:
        client = init_supabase()
        
        now = datetime.now()
        
        # Verificar que el gasto fijo existe
        recurring_response = client.table("gastos_fijos") \
            .select("*") \
            .eq("id", recurring_id) \
            .execute()
        
        if not recurring_response.data:
            return {
                "success": False,
                "message": "❌ Gasto fijo no encontrado"
            }
        
        recurring = recurring_response.data[0]
        amount = recurring.get("amount", 0)
        description = recurring.get("description", "")
        
        # Registrar el pago
        payment_data = {
            "gasto_fijo_id": recurring_id,
            "month": now.month,
            "year": now.year,
            "amount": amount
        }
        
        client.table("pagos_realizados").insert(payment_data).execute()
        
        logger.info(f"✅ Pago marcado: {description}")
        
        return {
            "success": True,
            "message": f"✅ Pago registrado:\n📝 {description}\n💰 ${amount:,.0f} COP\n📅 {now.strftime('%B %Y')}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {
            "success": False,
            "message": f"❌ Error al marcar pago: {str(e)}"
        }


def get_upcoming_payments(days_ahead: int = 3) -> List[Dict]:
    """
    Obtiene pagos próximos a vencer (para el sistema de notificaciones).
    
    Args:
        days_ahead (int): Días de anticipación para alertar
    
    Returns:
        List[Dict]: Lista de pagos próximos a vencer
    """
    try:
        client = init_supabase()
        
        now = datetime.now()
        current_day = now.day
        current_month = now.month
        current_year = now.year
        
        # Obtener gastos fijos activos
        recurring_response = client.table("gastos_fijos") \
            .select("*") \
            .eq("active", True) \
            .execute()
        
        # Obtener pagos realizados este mes
        payments_response = client.table("pagos_realizados") \
            .select("*") \
            .eq("month", current_month) \
            .eq("year", current_year) \
            .execute()
        
        paid_ids = {p["gasto_fijo_id"] for p in payments_response.data}
        
        # Filtrar próximos a vencer
        upcoming = []
        for rec in recurring_response.data:
            rec_id = rec.get("id")
            day = rec.get("day_of_month", 0)
            
            if rec_id not in paid_ids:
                days_until = day - current_day
                
                if 0 <= days_until <= days_ahead:
                    upcoming.append({
                        "id": rec_id,
                        "description": rec.get("description", ""),
                        "amount": rec.get("amount", 0),
                        "day_of_month": day,
                        "days_until": days_until
                    })
        
        return upcoming
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return []


# Inicializar la conexión al importar el módulo
try:
    init_supabase()
except Exception as e:
    logger.warning(f"⚠️ No se pudo inicializar Supabase al importar: {e}")
