import os
import httpx
from config import logger

API_URL = os.getenv("API_URL", "http://localhost:8000")

async def send_chat_message(user_id: int, message: str) -> str:
    """Envía un mensaje de texto al backend y devuelve la respuesta."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_URL}/api/chat",
                json={"user_id": user_id, "message": message}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("reply", "No recibí una respuesta válida del backend.")
    except Exception as e:
        logger.error(f"Error comunicando con backend (chat): {e}")
        return f"🚨 Error de conexión con el servidor interno: {e}"

async def send_voice_message(user_id: int, audio_bytes: bytes) -> str:
    """Envía un mensaje de voz al backend y devuelve la respuesta."""
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            files = {'file': ('audio.ogg', audio_bytes, 'audio/ogg')}
            data = {'user_id': str(user_id)}
            
            response = await client.post(
                f"{API_URL}/api/chat/voice",
                data=data,
                files=files
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("reply", "No recibí una respuesta válida del backend.")
    except Exception as e:
        logger.error(f"Error comunicando con backend (voice): {e}")
        return f"🚨 Error de conexión con el servidor interno: {e}"

async def get_due_bills(days_ahead: int = 1) -> list:
    """Obtiene las facturas por vencer desde el backend."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{API_URL}/api/reminders/bills/due",
                params={"days_ahead": days_ahead}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("bills", [])
    except Exception as e:
        logger.error(f"Error obteniendo facturas: {e}")
        return []

async def get_custom_reminders() -> list:
    """Obtiene los recordatorios personalizados desde el backend."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_URL}/api/reminders/custom/due")
            response.raise_for_status()
            data = response.json()
            return data.get("reminders", [])
    except Exception as e:
        logger.error(f"Error obteniendo recordatorios: {e}")
        return []

async def delete_custom_reminder(reminder_id: int) -> bool:
    """Elimina un recordatorio ya enviado en el backend."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(f"{API_URL}/api/reminders/custom/{reminder_id}")
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Error eliminando recordatorio {reminder_id}: {e}")
        return False
