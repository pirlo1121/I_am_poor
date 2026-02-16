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
            "message": f"✅ Gasto registrado: ${amount:,.0f} COP en {category}",
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


def unmark_payment_done(recurring_id: int) -> Dict:
    """Desmarca un gasto fijo como pagado para el mes actual (elimina el pago)."""
    try:
        client = init_supabase()
        now = datetime.now()
        
        # Verificar que el gasto fijo existe
        recurring_response = client.table("gastos_fijos") \
            .select("description") \
            .eq("id", recurring_id) \
            .execute()
        
        if not recurring_response.data:
            return {"success": False, "message": "❌ Gasto fijo no encontrado"}
        
        description = recurring_response.data[0].get("description", "")
        
        # Buscar el pago del mes actual
        payment_response = client.table("pagos_realizados") \
            .select("id") \
            .eq("gasto_fijo_id", recurring_id) \
            .eq("month", now.month) \
            .eq("year", now.year) \
            .execute()
        
        if not payment_response.data:
            return {"success": False, "message": f"⚠️ '{description}' no está marcada como pagada este mes"}
        
        # Eliminar el pago
        payment_id = payment_response.data[0]["id"]
        client.table("pagos_realizados").delete().eq("id", payment_id).execute()
        
        logger.info(f"↩️ Pago desmarcado: {description}")
        return {"success": True, "message": f"↩️ Pago desmarcado: {description} vuelve a estar pendiente este mes"}
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "message": f"❌ Error al desmarcar pago: {str(e)}"}


def get_paid_payments() -> str:
    """Obtiene las facturas/mensualidades ya pagadas del mes actual."""
    try:
        client = init_supabase()
        
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Obtener pagos realizados este mes
        payments_response = client.table("pagos_realizados") \
            .select("*") \
            .eq("month", current_month) \
            .eq("year", current_year) \
            .execute()
        
        paid_payments = payments_response.data
        
        if not paid_payments:
            return f"📭 No has pagado ninguna factura en {now.strftime('%B %Y')} aún"
        
        # Obtener detalles de los gastos fijos
        paid_with_details = []
        for payment in paid_payments:
            recurring_id = payment.get("gasto_fijo_id")
            
            # Buscar el gasto fijo correspondiente
            recurring_response = client.table("gastos_fijos") \
                .select("*") \
                .eq("id", recurring_id) \
                .execute()
            
            if recurring_response.data:
                recurring = recurring_response.data[0]
                paid_with_details.append({
                    "description": recurring.get("description", ""),
                    "amount": payment.get("amount", 0),
                    "category": recurring.get("category", ""),
                    "day_of_month": recurring.get("day_of_month", 0)
                })
        
        if not paid_with_details:
            return f"📭 No se encontraron detalles de pagos para {now.strftime('%B %Y')}"
        
        result = f"✅ **Facturas Pagadas ({now.strftime('%B %Y')}):**\n\n"
        
        total_paid = 0
        for idx, payment in enumerate(paid_with_details, 1):
            description = payment.get("description", "")
            amount = payment.get("amount", 0)
            category = payment.get("category", "")
            day = payment.get("day_of_month", 0)
            
            result += f"{idx}. ✅ ${amount:,.0f} - {description}\n"
            result += f"   📅 Día {day} de cada mes ({category.title()})\n\n"
            total_paid += amount
        
        result += f"💵 **Total Pagado**: ${total_paid:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar facturas pagadas: {str(e)}"


def get_all_monthly_bills() -> str:
    """Obtiene todas las mensualidades del mes actual (pagadas y pendientes)."""
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
            .order("day_of_month") \
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
        
        # Separar en pagadas y pendientes
        paid_bills = []
        pending_bills = []
        
        for rec in recurring_expenses:
            rec_id = rec.get("id")
            description = rec.get("description", "")
            amount = rec.get("amount", 0)
            day = rec.get("day_of_month", 0)
            category = rec.get("category", "")
            
            bill_info = {
                "description": description,
                "amount": amount,
                "day": day,
                "category": category
            }
            
            if rec_id in paid_ids:
                paid_bills.append(bill_info)
            else:
                days_until = day - current_day
                bill_info["days_until"] = days_until
                pending_bills.append(bill_info)
        
        # Construir respuesta
        result = f"📋 **Todas las Mensualidades ({now.strftime('%B %Y')}):**\n\n"
        
        # Mostrar pagadas
        if paid_bills:
            result += "✅ **PAGADAS:**\n"
            total_paid = 0
            for idx, bill in enumerate(paid_bills, 1):
                result += f"{idx}. 💰 ${bill['amount']:,.0f} - {bill['description']}\n"
                result += f"   📅 Día {bill['day']} ({bill['category'].title()})\n"
                total_paid += bill['amount']
            result += f"   **Subtotal Pagado**: ${total_paid:,.0f}\n\n"
        else:
            result += "✅ **PAGADAS:** Ninguna aún\n\n"
        
        # Mostrar pendientes
        if pending_bills:
            result += "⏰ **PENDIENTES:**\n"
            total_pending = 0
            for idx, bill in enumerate(pending_bills, 1):
                days_until = bill.get("days_until", 0)
                
                if days_until < 0:
                    status = f"⚠️ Vencida"
                elif days_until == 0:
                    status = f"🔴 Vence HOY"
                elif days_until == 1:
                    status = f"🟡 Mañana"
                else:
                    status = f"⏰ Faltan {days_until} días"
                
                result += f"{idx}. 💰 ${bill['amount']:,.0f} - {bill['description']}\n"
                result += f"   📅 Día {bill['day']} - {status} ({bill['category'].title()})\n"
                total_pending += bill['amount']
            result += f"   **Subtotal Pendiente**: ${total_pending:,.0f}\n\n"
        else:
            result += "⏰ **PENDIENTES:** ¡Todas pagadas! 🎉\n\n"
        
        # Total general
        total_all = sum(b['amount'] for b in paid_bills) + sum(b['amount'] for b in pending_bills)
        result += f"💵 **Total Mensual**: ${total_all:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar mensualidades: {str(e)}"


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


# ============================================
# NUEVAS FUNCIONES - MEJORAS DE LENGUAJE NATURAL
# ============================================

def find_recurring_by_name(description: str) -> Optional[int]:
    """
    Busca un gasto fijo por nombre/descripción (case-insensitive).
    Retorna el ID del gasto fijo o None si no se encuentra.
    
    Args:
        description: Nombre del gasto fijo (ej: "arriendo", "luz", "internet")
    
    Returns:
        ID del gasto fijo o None
    """
    try:
        client = init_supabase()
        
        # Buscar gastos fijos que coincidan (case-insensitive)
        response = client.table("gastos_fijos") \
            .select("*") \
            .eq("active", True) \
            .execute()
        
        # Buscar coincidencia
        search_term = description.strip().lower()
        for rec in response.data:
            rec_desc = rec.get("description", "").lower()
            if search_term in rec_desc or rec_desc in search_term:
                return rec.get("id")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error buscando gasto fijo: {e}")
        return None


def get_expenses_by_month(month: Optional[int] = None, year: Optional[int] = None) -> str:
    """
    Obtiene todos los gastos de un mes específico.
    Si no se especifica mes/año, usa el mes actual.
    
    Args:
        month: Mes (1-12), None para mes actual
        year: Año (ej: 2026), None para año actual
    
    Returns:
        str: Gastos del mes formateados
    """
    try:
        client = init_supabase()
        
        now = datetime.now()
        target_month = month if month else now.month
        target_year = year if year else now.year
        
        # Calcular rango de fechas del mes
        from calendar import monthrange
        last_day = monthrange(target_year, target_month)[1]
        
        start_date = f"{target_year}-{target_month:02d}-01T00:00:00"
        end_date = f"{target_year}-{target_month:02d}-{last_day}T23:59:59"
        
        response = client.table("gastos") \
            .select("*") \
            .gte("created_at", start_date) \
            .lte("created_at", end_date) \
            .order("created_at", desc=True) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                          "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            return f"📭 No hay gastos registrados en {month_names[target_month]} {target_year}"
        
        # Agrupar por categoría
        by_category = {}
        total = 0
        
        for expense in expenses:
            category = expense.get("category", "sin categoría")
            amount = expense.get("amount", 0)
            
            if category not in by_category:
                by_category[category] = {"total": 0, "count": 0}
            
            by_category[category]["total"] += amount
            by_category[category]["count"] += 1
            total += amount
        
        month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        result = f"📅 **Gastos de {month_names[target_month]} {target_year}:**\n\n"
        
        # Ordenar categorías por total
        sorted_cats = sorted(by_category.items(), key=lambda x: x[1]["total"], reverse=True)
        
        emojis = {
            "comida": "🍔",
            "transporte": "🚕",
            "servicios": "🏠",
            "entretenimiento": "🎮",
            "salud": "💊",
            "mercado": "🛒",
            "general": "📦"
        }
        
        for category, data in sorted_cats:
            emoji = emojis.get(category, "💰")
            result += f"{emoji} **{category.title()}**: ${data['total']:,.0f} ({data['count']} gastos)\n"
        
        result += f"\n💵 **Total del Mes**: ${total:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar gastos del mes: {str(e)}"


def compare_monthly_expenses(month1: int, year1: int, month2: int, year2: int) -> str:
    """
    Compara gastos entre dos meses.
    
    Args:
        month1, year1: Primer mes a comparar
        month2, year2: Segundo mes a comparar
    
    Returns:
        str: Comparación formateada
    """
    try:
        client = init_supabase()
        
        month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        # Obtener datos de ambos meses
        from calendar import monthrange
        
        def get_month_data(month, year):
            last_day = monthrange(year, month)[1]
            start_date = f"{year}-{month:02d}-01T00:00:00"
            end_date = f"{year}-{month:02d}-{last_day}T23:59:59"
            
            response = client.table("gastos") \
                .select("*") \
                .gte("created_at", start_date) \
                .lte("created_at", end_date) \
                .execute()
            
            expenses = response.data
            total = sum(e.get("amount", 0) for e in expenses)
            
            by_category = {}
            for e in expenses:
                cat = e.get("category", "general")
                if cat not in by_category:
                    by_category[cat] = 0
                by_category[cat] += e.get("amount", 0)
            
            return total, by_category, len(expenses)
        
        total1, cats1, count1 = get_month_data(month1, year1)
        total2, cats2, count2 = get_month_data(month2, year2)
        
        result = f"📊 **Comparación de Gastos:**\n\n"
        result += f"**{month_names[month1]} {year1}** vs **{month_names[month2]} {year2}**\n\n"
        
        # Totales
        diff = total2 - total1
        diff_pct = ((total2 - total1) / total1 * 100) if total1 > 0 else 0
        
        result += f"💵 **{month_names[month1]}**: ${total1:,.0f} COP ({count1} gastos)\n"
        result += f"💵 **{month_names[month2]}**: ${total2:,.0f} COP ({count2} gastos)\n\n"
        
        if diff > 0:
            result += f"📈 **Diferencia**: +${diff:,.0f} COP (+{diff_pct:.1f}%)\n"
            result += f"⚠️ Gastaste MÁS en {month_names[month2]}\n\n"
        elif diff < 0:
            result += f"📉 **Diferencia**: -${abs(diff):,.0f} COP ({diff_pct:.1f}%)\n"
            result += f"✅ Gastaste MENOS en {month_names[month2]}\n\n"
        else:
            result += f"➡️ **Sin cambio**\n\n"
        
        # Comparar categorías principales
        all_cats = set(list(cats1.keys()) + list(cats2.keys()))
        
        if all_cats:
            result += "**Por Categorías:**\n"
            for cat in sorted(all_cats):
                amt1 = cats1.get(cat, 0)
                amt2 = cats2.get(cat, 0)
                
                if amt1 > 0 or amt2 > 0:
                    cat_diff = amt2 - amt1
                    if cat_diff > 0:
                        result += f"• {cat.title()}: ${amt1:,.0f} → ${amt2:,.0f} (+${cat_diff:,.0f})\n"
                    elif cat_diff < 0:
                        result += f"• {cat.title()}: ${amt1:,.0f} → ${amt2:,.0f} (-${abs(cat_diff):,.0f})\n"
                    else:
                        result += f"• {cat.title()}: ${amt1:,.0f} (sin cambio)\n"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al comparar meses: {str(e)}"


# ============================================
# FUNCIÓN OPTIMIZADA - RESUMEN FINANCIERO RÁPIDO
# ============================================

def get_financial_summary(budget: Optional[float] = None) -> str:
    """
    Obtiene un resumen financiero completo del mes actual en UNA SOLA CONSULTA.
    Incluye: gastos totales, mensualidades pagadas, mensualidades pendientes, 
    y si se proporciona un presupuesto, calcula el balance.
    
    Esta función es MUCHO MÁS RÁPIDA que llamar a múltiples funciones por separado.
    
    Args:
        budget: Presupuesto mensual opcional (en COP)
    
    Returns:
        str: Resumen financiero completo formateado
    """
    try:
        client = init_supabase()
        
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # 1. Obtener gastos del mes actual
        start_date = f"{current_year}-{current_month:02d}-01T00:00:00"
        if current_month == 12:
            end_date = f"{current_year + 1}-01-01T00:00:00"
        else:
            end_date = f"{current_year}-{current_month + 1:02d}-01T00:00:00"
        
        expenses_response = client.table("gastos") \
            .select("amount") \
            .gte("created_at", start_date) \
            .lt("created_at", end_date) \
            .execute()
        
        total_expenses = sum(e.get("amount", 0) for e in expenses_response.data)
        
        # 2. Obtener gastos fijos y pagos
        recurring_response = client.table("gastos_fijos") \
            .select("id,description,amount,day_of_month") \
            .eq("active", True) \
            .execute()
        
        payments_response = client.table("pagos_realizados") \
            .select("gasto_fijo_id,amount") \
            .eq("month", current_month) \
            .eq("year", current_year) \
            .execute()
        
        recurring_expenses = recurring_response.data
        paid_ids = {p["gasto_fijo_id"] for p in payments_response.data}
        
        # Calcular totales de mensualidades
        total_bills = sum(r.get("amount", 0) for r in recurring_expenses)
        paid_bills_amount = sum(p.get("amount", 0) for p in payments_response.data)
        pending_bills_amount = total_bills - paid_bills_amount
        
        paid_count = len(paid_ids)
        pending_count = len(recurring_expenses) - paid_count
        
        # Construir respuesta rápida
        result = f"💰 **Resumen Financiero - {now.strftime('%B %Y')}**\n\n"
        
        result += f"📊 **GASTOS VARIABLES:**\n"
        result += f"   ${total_expenses:,.0f} COP\n\n"
        
        result += f"🏠 **MENSUALIDADES:**\n"
        result += f"   ✅ Pagadas: {paid_count} (${paid_bills_amount:,.0f})\n"
        result += f"   ⏰ Pendientes: {pending_count} (${pending_bills_amount:,.0f})\n"
        result += f"   📋 Total: ${total_bills:,.0f}\n\n"
        
        # Total gastado hasta ahora
        total_spent = total_expenses + paid_bills_amount
        result += f"💵 **TOTAL GASTADO**: ${total_spent:,.0f} COP\n"
        
        # Si hay presupuesto, calcular balance
        if budget and budget > 0:
            total_committed = total_expenses + total_bills
            balance = budget - total_committed
            
            result += f"\n💼 **PRESUPUESTO**: ${budget:,.0f} COP\n"
            
            if balance >= 0:
                result += f"✅ **BALANCE**: ${balance:,.0f} COP disponibles 🎉\n"
                percentage = (balance / budget * 100) if budget > 0 else 0
                result += f"   ({percentage:.1f}% del presupuesto restante)"
            else:
                result += f"⚠️ **SOBREGIRO**: ${abs(balance):,.0f} COP 🔴\n"
                percentage = (abs(balance) / budget * 100) if budget > 0 else 0
                result += f"   ({percentage:.1f}% por encima del presupuesto)"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en resumen financiero: {e}")
        return f"❌ Error al generar resumen financiero: {str(e)}"


# ============================================
# NUEVAS MEJORAS CREATIVAS - METAS DE AHORRO
# ============================================

def add_savings_goal(name: str, target_amount: float, deadline: Optional[str] = None, category: str = "general") -> Dict:
    """
    Crea una nueva meta de ahorro.
    
    Args:
        name: Nombre de la meta (ej: "Vacaciones", "Laptop")
        target_amount: Monto objetivo en COP
        deadline: Fecha límite en formato YYYY-MM-DD (opcional)
        category: Categoría de la meta
    
    Returns:
        Dict con success, message
    """
    try:
        client = init_supabase()
        
        goal_data = {
            "name": name.strip(),
            "target_amount": float(target_amount),
            "current_amount": 0.0,
            "category": category.lower(),
            "active": True
        }
        
        if deadline:
            goal_data["deadline"] = deadline
        
        response = client.table("savings_goals").insert(goal_data).execute()
        
        # Calcular sugerencia mensual si hay deadline
        suggestion = ""
        if deadline:
            from datetime import datetime
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                now = datetime.now()
                months_left = max(1, ((deadline_date.year - now.year) * 12 + deadline_date.month - now.month))
                monthly_saving = target_amount / months_left
                suggestion = f"\n💰 Sugerencia: Ahorra ${monthly_saving:,.0f} COP al mes durante {months_left} meses"
            except:
                pass
        
        logger.info(f"✅ Meta creada: {name} - ${target_amount}")
        
        return {
            "success": True,
            "message": f"🎯 Meta de Ahorro Creada:\n📝 {name}\n💵 Objetivo: ${target_amount:,.0f} COP\n📅 Plazo: {deadline if deadline else 'Sin plazo definido'}{suggestion}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando meta: {e}")
        return {
            "success": False,
            "message": f"❌ Error al crear meta de ahorro: {str(e)}"
        }


def get_savings_goals() -> str:
    """Obtiene todas las metas de ahorro activas con su progreso."""
    try:
        client = init_supabase()
        
        response = client.table("savings_goals") \
            .select("*") \
            .eq("active", True) \
            .order("created_at", desc=True) \
            .execute()
        
        goals = response.data
        
        if not goals:
            return "📭 No tienes metas de ahorro configuradas aún.\n\n💡 Crea una con: 'Quiero ahorrar X para Y'"
        
        result = "🎯 **Tus Metas de Ahorro:**\n\n"
        
        for idx, goal in enumerate(goals, 1):
            name = goal.get("name", "")
            target = goal.get("target_amount", 0)
            current = goal.get("current_amount", 0)
            deadline = goal.get("deadline", "")
            
            percentage = (current / target * 100) if target > 0 else 0
            
            # Emoji según progreso
            if percentage >= 100:
                emoji = "🎉"
            elif percentage >= 75:
                emoji = "🔥"
            elif percentage >= 50:
                emoji = "💪"
            elif percentage >= 25:
                emoji = "📈"
            else:
                emoji = "🌱"
            
            result += f"{idx}. {emoji} **{name}**\n"
            result += f"   💰 ${current:,.0f} de ${target:,.0f} ({percentage:.1f}%)\n"
            
            if deadline:
                from datetime import datetime
                try:
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                    now = datetime.now()
                    days_left = (deadline_date - now).days
                    if days_left > 0:
                        result += f"   ⏰ {days_left} días restantes\n"
                    else:
                        result += f"   ⚠️ Plazo vencido\n"
                except:
                    pass
            
            # Barra de progreso visual
            bar_length = 15
            filled = int(bar_length * percentage / 100)
            bar = "█" * filled + "░" * (bar_length - filled)
            result += f"   [{bar}]\n\n"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar metas: {str(e)}"


def add_contribution_to_goal(goal_id: int, amount: float, description: str = "") -> Dict:
    """
    Agrega dinero a una meta de ahorro.
    
    Args:
        goal_id: ID de la meta
        amount: Monto a agregar
        description: Descripción opcional
    
    Returns:
        Dict con success, message
    """
    try:
        client = init_supabase()
        
        # Verificar que la meta existe
        goal_response = client.table("savings_goals") \
            .select("*") \
            .eq("id", goal_id) \
            .eq("active", True) \
            .execute()
        
        if not goal_response.data:
            return {
                "success": False,
                "message": "❌ Meta no encontrada"
            }
        
        goal = goal_response.data[0]
        goal_name = goal.get("name", "")
        target_amount = goal.get("target_amount", 0)
        current_amount = goal.get("current_amount", 0)
        
        # Registrar la contribución
        contribution_data = {
            "goal_id": goal_id,
            "amount": float(amount),
            "description": description.strip() if description else f"Contribución a {goal_name}"
        }
        
        client.table("savings_contributions").insert(contribution_data).execute()
        
        # Actualizar el monto actual de la meta
        new_amount = current_amount + amount
        client.table("savings_goals") \
            .update({"current_amount": new_amount}) \
            .eq("id", goal_id) \
            .execute()
        
        percentage = (new_amount / target_amount * 100) if target_amount > 0 else 0
        remaining = target_amount - new_amount
        
        message = f"✅ Contribución Registrada:\n"
        message += f"🎯 Meta: {goal_name}\n"
        message += f"💰 Agregaste: ${amount:,.0f} COP\n"
        message += f"📊 Progreso: ${new_amount:,.0f} de ${target_amount:,.0f} ({percentage:.1f}%)\n"
        
        if percentage >= 100:
            message += f"\n🎉 ¡FELICITACIONES! ¡Meta alcanzada! 🎉"
        else:
            message += f"💪 Faltan: ${remaining:,.0f} COP"
        
        logger.info(f"✅ Contribución: ${amount} a meta {goal_name}")
        
        return {
            "success": True,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {
            "success": False,
            "message": f"❌ Error al agregar contribución: {str(e)}"
        }


# ============================================
# ANÁLISIS PREDICTIVO E INSIGHTS
# ============================================

def get_spending_prediction(category: Optional[str] = None) -> str:
    """
    Proyecta gastos futuros basándose en el promedio de los últimos 3 meses.
    
    Args:
        category: Categoría específica a proyectar (opcional)
    
    Returns:
        str: Proyección formateada
    """
    try:
        client = init_supabase()
        
        now = datetime.now()
        
        # Calcular los últimos 3 meses
        months_data = []
        
        for i in range(3):
            month = now.month - i
            year = now.year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # Obtener gastos del mes
            from calendar import monthrange
            last_day = monthrange(year, month)[1]
            
            start_date = f"{year}-{month:02d}-01T00:00:00"
            end_date = f"{year}-{month:02d}-{last_day}T23:59:59"
            
            query = client.table("gastos") \
                .select("amount, category") \
                .gte("created_at", start_date) \
                .lte("created_at", end_date)
            
            if category:
                query = query.eq("category", category.lower())
            
            response = query.execute()
            
            total = sum(e.get("amount", 0) for e in response.data)
            months_data.append(total)
        
        if not months_data or all(m == 0 for m in months_data):
            return "📊 No hay suficientes datos históricos para hacer una proyección"
        
        # Calcular promedio
        average = sum(months_data) / len(months_data)
        
        # Calcular tendencia
        if len(months_data) >= 2:
            trend = ((months_data[0] - months_data[-1]) / months_data[-1] * 100) if months_data[-1] > 0 else 0
        else:
            trend = 0
        
        month_names = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        next_month = now.month + 1
        next_year = now.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        result = f"📊 **Proyección de Gastos para {month_names[next_month]} {next_year}:**\n\n"
        
        if category:
            result += f"🏷️ Categoría: {category.title()}\n"
        
        result += f"💰 Proyección: ~${average:,.0f} COP\n"
        result += f"📈 Basado en promedio de últimos 3 meses\n\n"
        
        result += f"**Histórico:**\n"
        for i, amount in enumerate(months_data):
            m = now.month - i
            y = now.year
            if m <= 0:
                m += 12
                y -= 1
            result += f"• {month_names[m]}: ${amount:,.0f}\n"
        
        result += f"\n**Tendencia:** "
        if trend > 10:
            result += f"📈 Incremento del {abs(trend):.1f}%"
        elif trend < -10:
            result += f"📉 Reducción del {abs(trend):.1f}%"
        else:
            result += f"➡️ Estable"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error en proyección: {str(e)}"


def get_financial_insights() -> str:
    """
    Genera insights financieros automáticos basados en patrones de gasto.
    
    Returns:
        str: Insights formateados
    """
    try:
        client = init_supabase()
        
        now = datetime.now()
        current_month = now.month
        current_year = now.year
        
        # Obtener gastos del mes actual
        from calendar import monthrange
        last_day = monthrange(current_year, current_month)[1]
        start_date = f"{current_year}-{current_month:02d}-01T00:00:00"
        end_date = f"{current_year}-{current_month:02d}-{last_day}T23:59:59"
        
        current_response = client.table("gastos") \
            .select("*") \
            .gte("created_at", start_date) \
            .lte("created_at", end_date) \
            .execute()
        
        current_expenses = current_response.data
        
        if not current_expenses:
            return "📊 No hay suficientes datos para generar insights este mes"
        
        # Analizar por categoría
        by_category = {}
        total_current = 0
        
        for expense in current_expenses:
            cat = expense.get("category", "general")
            amount = expense.get("amount", 0)
            
            if cat not in by_category:
                by_category[cat] = 0
            
            by_category[cat] += amount
            total_current += amount
        
        # Obtener gastos del mes anterior para comparación
        prev_month = current_month - 1
        prev_year = current_year
        if prev_month <= 0:
            prev_month = 12
            prev_year -= 1
        
        last_day_prev = monthrange(prev_year, prev_month)[1]
        start_date_prev = f"{prev_year}-{prev_month:02d}-01T00:00:00"
        end_date_prev = f"{prev_year}-{prev_month:02d}-{last_day_prev}T23:59:59"
        
        prev_response = client.table("gastos") \
            .select("amount") \
            .gte("created_at", start_date_prev) \
            .lte("created_at", end_date_prev) \
            .execute()
        
        total_prev = sum(e.get("amount", 0) for e in prev_response.data)
        
        # Construir insights
        result = f"💡 **Insights Financieros - {now.strftime('%B %Y')}:**\n\n"
        
        # Comparación mensual
        if total_prev > 0:
            diff = total_current - total_prev
            diff_pct = (diff / total_prev * 100)
            
            if diff_pct > 10:
                result += f"⚠️ **Alerta:** Gastas {abs(diff_pct):.1f}% MÁS que el mes pasado (+${abs(diff):,.0f})\n\n"
            elif diff_pct < -10:
                result += f"✅ **Excelente:** Gastas {abs(diff_pct):.1f}% MENOS que el mes pasado (-${abs(diff):,.0f})\n\n"
            else:
                result += f"➡️ **Estable:** Gastos similares al mes pasado\n\n"
        
        # Categoría que más gasta
        if by_category:
            sorted_cats = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
            top_cat, top_amount = sorted_cats[0]
            percentage = (top_amount / total_current * 100) if total_current > 0 else 0
            
            result += f"📊 **Categoría Dominante:**\n"
            result += f"   {top_cat.title()}: ${top_amount:,.0f} ({percentage:.1f}% del total)\n"
            
            # Sugerencias basadas en porcentajes recomendados
            recommendations = {
                "comida": 25,
                "transporte": 15,
                "entretenimiento": 10,
                "servicios": 20
            }
            
            if top_cat in recommendations:
                recommended = recommendations[top_cat]
                if percentage > recommended + 10:
                    savings_potential = top_amount * 0.15  # 15% de reducción
                    result += f"   ⚠️ Recomendado: ~{recommended}%\n"
                    result += f"   💡 Podrías ahorrar ~${savings_potential:,.0f} optimizando esta categoría\n"
            
            result += "\n"
        
        # Promedio diario
        days_in_month = last_day
        current_day = now.day
        daily_avg = total_current / current_day if current_day > 0 else 0
        projected_monthly = daily_avg * days_in_month
        
        result += f"📅 **Ritmo de Gasto:**\n"
        result += f"   Promedio diario: ${daily_avg:,.0f}\n"
        result += f"   Proyección fin de mes: ${projected_monthly:,.0f}\n\n"
        
        # Recomendaciones
        result += f"💪 **Recomendaciones:**\n"
        
        if projected_monthly > total_current * 1.2:
            result += f"   • Estás gastando más rápido de lo normal\n"
            result += f"   • Considera revisar gastos no esenciales\n"
        else:
            result += f"   • Ritmo de gasto saludable\n"
        
        if len(by_category) > 5:
            result += f"   • Muchas categorías activas, considera consolidar\n"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error generando insights: {str(e)}"


# Helper para buscar meta por nombre (para AI)
def find_savings_goal_by_name(name: str) -> Optional[int]:
    """Busca una meta de ahorro por nombre y retorna su ID."""
    try:
        client = init_supabase()
        
        response = client.table("savings_goals") \
            .select("*") \
            .eq("active", True) \
            .execute()
        
        search_term = name.strip().lower()
        for goal in response.data:
            goal_name = goal.get("name", "").lower()
            if search_term in goal_name or goal_name in search_term:
                return goal.get("id")
        
        return None
        
    except Exception as e:
        logger.error(f"❌ Error buscando meta: {e}")
        return None


# ============================================
# FUNCIONES DE INGRESOS
# ============================================

def set_fixed_salary(amount: float) -> Dict:
    """Define o actualiza el salario fijo del mes actual."""
    try:
        client = init_supabase()
        now = datetime.now()
        
        # Verificar si ya existe un salario para este mes
        existing = client.table("ingresos") \
            .select("id") \
            .eq("type", "salario") \
            .eq("month", now.month) \
            .eq("year", now.year) \
            .execute()
        
        if existing.data:
            # Actualizar
            client.table("ingresos") \
                .update({"amount": float(amount)}) \
                .eq("id", existing.data[0]["id"]) \
                .execute()
            logger.info(f"✅ Salario actualizado: ${amount}")
            return {"success": True, "message": f"💰 Salario actualizado a ${amount:,.0f} COP para este mes"}
        else:
            # Insertar
            client.table("ingresos").insert({
                "amount": float(amount),
                "type": "salario",
                "description": "Salario fijo",
                "month": now.month,
                "year": now.year
            }).execute()
            logger.info(f"✅ Salario registrado: ${amount}")
            return {"success": True, "message": f"💰 Salario fijo registrado: ${amount:,.0f} COP"}
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "message": f"❌ Error al registrar salario: {str(e)}"}


def add_extra_income(amount: float, description: str = "") -> Dict:
    """Registra un ingreso extra con fecha y descripción."""
    try:
        client = init_supabase()
        now = datetime.now()
        
        client.table("ingresos").insert({
            "amount": float(amount),
            "type": "extra",
            "description": description.strip() if description else "Ingreso extra",
            "month": now.month,
            "year": now.year
        }).execute()
        
        logger.info(f"✅ Ingreso extra: ${amount} - {description}")
        return {"success": True, "message": f"✅ Ingreso extra registrado: ${amount:,.0f} COP - {description or 'Sin descripción'}"}
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "message": f"❌ Error al registrar ingreso: {str(e)}"}


def get_extra_incomes(month: Optional[int] = None, year: Optional[int] = None) -> str:
    """Lista todos los ingresos extras del mes."""
    try:
        client = init_supabase()
        now = datetime.now()
        target_month = month if month else now.month
        target_year = year if year else now.year
        
        response = client.table("ingresos") \
            .select("*") \
            .eq("type", "extra") \
            .eq("month", target_month) \
            .eq("year", target_year) \
            .order("created_at", desc=True) \
            .execute()
        
        extras = response.data
        if not extras:
            return "📭 No hay ingresos extras registrados este mes"
        
        total = sum(e.get("amount", 0) for e in extras)
        result = f"💵 **Ingresos Extras del mes ({len(extras)}):**\n\n"
        
        for idx, inc in enumerate(extras, 1):
            amount = inc.get("amount", 0)
            desc = inc.get("description", "Sin descripción")
            date = inc.get("created_at", "")[:10]
            result += f"{idx}. ${amount:,.0f} - {desc} ({date})\n"
        
        result += f"\n💰 **Total extras**: ${total:,.0f} COP"
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar ingresos: {str(e)}"


def get_income_summary(month: Optional[int] = None, year: Optional[int] = None) -> str:
    """Resumen de ingresos del mes: salario + extras = total."""
    try:
        client = init_supabase()
        now = datetime.now()
        target_month = month if month else now.month
        target_year = year if year else now.year
        
        response = client.table("ingresos") \
            .select("*") \
            .eq("month", target_month) \
            .eq("year", target_year) \
            .execute()
        
        incomes = response.data
        if not incomes:
            return "📭 No hay ingresos registrados este mes"
        
        salary = 0
        extras_total = 0
        extras_count = 0
        
        for inc in incomes:
            if inc.get("type") == "salario":
                salary = inc.get("amount", 0)
            else:
                extras_total += inc.get("amount", 0)
                extras_count += 1
        
        total = salary + extras_total
        result = f"💵 **Ingresos del mes:**\n"
        result += f"   💼 Salario: ${salary:,.0f} COP\n"
        result += f"   ➕ Extras: ${extras_total:,.0f} COP ({extras_count} registros)\n"
        result += f"   📊 **Total**: ${total:,.0f} COP"
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return f"❌ Error al consultar ingresos: {str(e)}"


# Inicializar la conexión al importar el módulo
try:
    init_supabase()
except Exception as e:
    logger.warning(f"⚠️ No se pudo inicializar Supabase al importar: {e}")

