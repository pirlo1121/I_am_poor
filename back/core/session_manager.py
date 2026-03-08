"""
Gestión de sesiones de usuario para mantener contexto conversacional.
"""

from google.genai import types
from settings import AI_PROVIDER, gemini_client, logger
from ai.prompts import get_system_instruction
from ai.tools import all_tools

# Diccionario para guardar el historial de chat de cada usuario
user_sessions = {}

# Límite de mensajes en el historial (para evitar que crezca infinitamente)
# Se mantienen los últimos N mensajes para tener contexto útil sin sobrecargar la API
MAX_HISTORY_MESSAGES = 40  # 20 intercambios (usuario + asistente) - mínimo 15 requerido



def get_or_create_session(user_id: int):
    """
    Obtiene o crea una sesión de chat para un usuario específico.
    
    Args:
        user_id: ID del usuario de Telegram
        
    Returns:
        La sesión de chat del usuario (formato depende del AI provider)
    """
    # Verificar si el usuario ya tiene una sesión
    if user_id not in user_sessions:
        # Si NO existe: Crear una nueva sesión de chat
        if AI_PROVIDER == "gemini":
            logger.info(f"🆕 Creando nueva sesión Gemini para usuario {user_id}")
            # Obtener system instruction con fecha actual
            system_prompt = get_system_instruction()
            
            # Crear sesión de chat con historial vacío
            model = gemini_client.models.get_generative_model(
                model='models/gemini-2.5-flash',
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
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
    
    return user_sessions.get(user_id)


def clear_session(user_id: int):
    """
    Elimina la sesión de un usuario.
    
    Args:
        user_id: ID del usuario de Telegram
    """
    if user_id in user_sessions:
        del user_sessions[user_id]
        logger.info(f"🗑️ Sesión eliminada para usuario {user_id}")
