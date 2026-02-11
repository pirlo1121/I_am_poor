"""
database.py - Módulo de conexión y operaciones con Supabase
Este módulo maneja todas las interacciones con la base de datos PostgreSQL vía Supabase.
"""

import os
from typing import Optional, List, Dict
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
    """
    Inicializa y retorna el cliente de Supabase.
    
    Returns:
        Client: Cliente de Supabase configurado
        
    Raises:
        ValueError: Si las credenciales no están configuradas
    """
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


def add_expense(amount: float, description: str, category: str) -> Dict:
    """
    Registra un nuevo gasto en la base de datos.
    
    Args:
        amount (float): Monto del gasto
        description (str): Descripción del gasto
        category (str): Categoría del gasto (ej: comida, transporte, etc.)
        
    Returns:
        Dict: Resultado de la operación con información del registro creado
        
    Raises:
        Exception: Si hay un error al insertar el registro
    """
    try:
        # Inicializar cliente si no existe
        client = init_supabase()
        
        # Preparar datos del gasto
        expense_data = {
            "amount": float(amount),
            "description": description.strip(),
            "category": category.strip().lower()
        }
        
        # Insertar en la tabla 'gastos'
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
    """
    Obtiene los gastos más recientes de la base de datos.
    
    Args:
        limit (int): Número de gastos a recuperar (default: 5)
        
    Returns:
        str: Texto formateado con los gastos recientes
    """
    try:
        # Inicializar cliente si no existe
        client = init_supabase()
        
        # Consultar los últimos gastos ordenados por fecha de creación
        response = client.table("gastos") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        
        expenses = response.data
        
        if not expenses:
            return "📭 No hay gastos registrados aún."
        
        # Formatear gastos como texto
        result = f"📊 **Últimos {len(expenses)} gastos:**\n\n"
        
        total = 0
        for idx, expense in enumerate(expenses, 1):
            amount = expense.get("amount", 0)
            description = expense.get("description", "Sin descripción")
            category = expense.get("category", "sin categoría")
            created_at = expense.get("created_at", "")
            
            # Extraer solo la fecha (sin hora)
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


# Inicializar la conexión al importar el módulo
try:
    init_supabase()
except Exception as e:
    logger.warning(f"⚠️ No se pudo inicializar Supabase al importar: {e}")
