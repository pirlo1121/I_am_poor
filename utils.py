"""
utils.py - Utilidades para mejorar la estabilidad del bot
Incluye: Circuit Breaker, Rate Limiter, Error Categorization
"""

import logging
from time import time
from collections import defaultdict
from typing import Callable, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Categorías de errores para manejo diferenciado"""
    CRITICAL = "critical"           # Reiniciar sesión
    TRANSIENT = "transient"         # Retry automático
    USER_INPUT = "user_input"       # Mantener sesión, informar usuario
    RECOVERABLE = "recoverable"     # Mantener sesión, continuar


def categorize_error(exception: Exception) -> ErrorCategory:
    """
    Categoriza un error para determinar la estrategia de manejo apropiada.
    
    Args:
        exception: La excepción a categorizar
        
    Returns:
        ErrorCategory: Categoría del error
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()
    
    # Errores críticos que requieren reinicio de sesión
    critical_keywords = [
        'invalid api key',
        'api key not valid',
        'quota exceeded',
        'rate limit exceeded',
        'authentication failed',
        'unauthorized',
        'invalid_api_key',
        'permission denied'
    ]
    
    if any(keyword in error_str for keyword in critical_keywords):
        return ErrorCategory.CRITICAL
    
    # Errores transitorios que se pueden reintentar
    transient_keywords = [
        'timeout',
        'timed out',
        'connection',
        'network',
        'temporary',
        'unavailable',
        'service unavailable',
        'gateway',
        '503',
        '502',
        '504'
    ]
    
    if any(keyword in error_str for keyword in transient_keywords):
        return ErrorCategory.TRANSIENT
    
    if 'timeout' in error_type or 'connection' in error_type:
        return ErrorCategory.TRANSIENT
    
    # Errores de entrada de usuario
    user_input_keywords = [
        'invalid parameter',
        'validation',
        'invalid input',
        'bad request',
        '400'
    ]
    
    if any(keyword in error_str for keyword in user_input_keywords):
        return ErrorCategory.USER_INPUT
    
    # Por defecto, considerar recuperable
    return ErrorCategory.RECOVERABLE


class CircuitBreaker:
    """
    Patrón Circuit Breaker para prevenir fallos en cascada.
    
    Estados:
    - CLOSED: Funcionamiento normal
    - OPEN: Demasiados fallos, bloquear llamadas
    - HALF_OPEN: Modo de prueba después de timeout
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Args:
            failure_threshold: Número de fallos antes de abrir el circuito
            timeout: Segundos antes de intentar cerrar el circuito
        """
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función con protección de circuit breaker.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si el circuito está abierto o la función falla
        """
        if self.state == "OPEN":
            # Verificar si es momento de intentar cerrar
            if self.last_failure_time and (time() - self.last_failure_time > self.timeout):
                logger.info("🔄 Circuit breaker: Intentando cerrar circuito (HALF_OPEN)")
                self.state = "HALF_OPEN"
            else:
                raise Exception("⚠️ Circuit breaker is OPEN - demasiados errores recientes")
        
        try:
            result = func(*args, **kwargs)
            
            # Éxito - resetear si estábamos en HALF_OPEN
            if self.state == "HALF_OPEN":
                logger.info("✅ Circuit breaker: Circuito cerrado exitosamente")
                self.state = "CLOSED"
                self.failure_count = 0
                
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time()
            
            logger.warning(f"⚠️ Circuit breaker: Fallo {self.failure_count}/{self.failure_threshold}")
            
            # Abrir circuito si se alcanza el threshold
            if self.failure_count >= self.failure_threshold:
                logger.error(f"🔴 Circuit breaker: ABIERTO - demasiados fallos")
                self.state = "OPEN"
            
            raise
    
    def reset(self):
        """Resetea el circuit breaker manualmente"""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("🔄 Circuit breaker reseteado manualmente")


class RateLimiter:
    """
    Rate limiter simple basado en ventana deslizante.
    Previene saturación de APIs limitando mensajes por usuario.
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Args:
            max_requests: Máximo de requests permitidas
            window_seconds: Tamaño de la ventana en segundos
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(list)
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Verifica si un usuario puede hacer una request.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            bool: True si está permitido, False si está rate limited
        """
        now = time()
        
        # Limpiar requests antiguas fuera de la ventana
        self.user_requests[user_id] = [
            timestamp for timestamp in self.user_requests[user_id]
            if now - timestamp < self.window_seconds
        ]
        
        # Verificar si está dentro del límite
        if len(self.user_requests[user_id]) >= self.max_requests:
            logger.warning(f"⚠️ Rate limit alcanzado para usuario {user_id}")
            return False
        
        # Agregar timestamp actual
        self.user_requests[user_id].append(now)
        return True
    
    def get_wait_time(self, user_id: int) -> float:
        """
        Obtiene el tiempo de espera antes de que el usuario pueda hacer otra request.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            float: Segundos a esperar (0 si puede hacer request ahora)
        """
        if not self.user_requests[user_id]:
            return 0.0
        
        now = time()
        oldest_timestamp = min(self.user_requests[user_id])
        wait_time = self.window_seconds - (now - oldest_timestamp)
        
        return max(0.0, wait_time)
    
    def cleanup_old_users(self, max_age: int = 3600):
        """
        Limpia usuarios inactivos para liberar memoria.
        
        Args:
            max_age: Segundos de inactividad antes de limpiar
        """
        now = time()
        inactive_users = []
        
        for user_id, timestamps in self.user_requests.items():
            if timestamps and (now - max(timestamps) > max_age):
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            del self.user_requests[user_id]
        
        if inactive_users:
            logger.info(f"🧹 Limpiados {len(inactive_users)} usuarios inactivos del rate limiter")


class SessionManager:
    """
    Gestor de sesiones con limpieza automática de sesiones inactivas.
    Previene memory leaks en bots de larga duración.
    """
    
    def __init__(self, max_inactive_seconds: int = 3600):
        """
        Args:
            max_inactive_seconds: Segundos de inactividad antes de limpiar sesión
        """
        self.sessions = {}
        self.last_activity = {}
        self.max_inactive_seconds = max_inactive_seconds
    
    def update_activity(self, user_id: int):
        """Actualiza el timestamp de última actividad de un usuario"""
        self.last_activity[user_id] = time()
    
    def cleanup_inactive(self) -> int:
        """
        Limpia sesiones inactivas.
        
        Returns:
            int: Número de sesiones eliminadas
        """
        now = time()
        inactive_users = []
        
        for user_id, last_time in self.last_activity.items():
            if now - last_time > self.max_inactive_seconds:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            if user_id in self.sessions:
                del self.sessions[user_id]
            del self.last_activity[user_id]
        
        if inactive_users:
            logger.info(f"🧹 Limpiadas {len(inactive_users)} sesiones inactivas")
        
        return len(inactive_users)


# ============================================
# NUEVA FUNCIÓN - TRANSCRIPCIÓN DE VOZ
# ============================================

async def transcribe_voice_message(file_path: str) -> str:
    """
    Transcribe un archivo de audio a texto usando OpenAI Whisper API.
    
    Args:
        file_path: Ruta al archivo de audio (.ogg, .mp3, .wav, etc.)
    
    Returns:
        str: Texto transcrito del audio
    
    Raises:
        Exception: Si falla la transcripción
    """
    try:
        import os
        from openai import OpenAI
        
        logger.info(f"🎤 Transcribiendo audio: {file_path}")
        
        # Obtener API key de variable de entorno
        api_key = os.getenv("CHATGPT_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise Exception("No se encontró CHATGPT_API_KEY o OPENAI_API_KEY en variables de entorno")
        
        # Crear cliente de OpenAI
        client = OpenAI(api_key=api_key)
        
        # Abrir y transcribir el archivo
        with open(file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es"  # Forzar español para mejor precisión
            )
        
        transcribed_text = transcript.text
        
        logger.info(f"✅ Transcripción exitosa: {transcribed_text[:50]}...")
        
        return transcribed_text
        
    except Exception as e:
        logger.error(f"❌ Error transcribiendo audio: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"No pude transcribir el audio: {str(e)}")

