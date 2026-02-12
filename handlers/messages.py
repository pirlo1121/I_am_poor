"""
Handler de mensajes de usuario con integración de AI.
"""

import json
from telegram import Update
from telegram.ext import ContextTypes
from google.genai import types
from config import AI_PROVIDER, logger
from ai.providers import generate_ai_response
from ai.prompts import SYSTEM_INSTRUCTION
from ai.tools import execute_function
from core.session_manager import get_or_create_session, clear_session, MAX_HISTORY_MESSAGES, user_sessions


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja todos los mensajes del usuario usando AI (Gemini o ChatGPT) con Function Calling
    y gestión de sesiones por usuario para mantener contexto conversacional.
    """
    user_message = update.message.text
    user_id = update.effective_user.id
    
    logger.info(f"Usuario {user_id}: {user_message}")
    
    # Obtener o crear sesión de chat
    chat_session = get_or_create_session(user_id)
    
    try:
        # Generar respuesta con el AI provider configurado
        response = generate_ai_response(user_message, chat_session)
        
        # ===== PROCESAR RESPUESTA SEGÚN PROVIDER =====
        if AI_PROVIDER == "chatgpt":
            await _process_chatgpt_response(response, user_message, user_id, update)
        else:
            await _process_gemini_response(response, chat_session, update)
        
    except Exception as e:
        logger.error(f"❌ Error procesando mensaje (user_id={user_id}): {e}")
        import traceback
        error_traceback = traceback.format_exc()
        logger.error(error_traceback)
        
        await _handle_error(e, user_id, update)


async def _process_chatgpt_response(response, user_message: str, user_id: int, update: Update):
    """Procesa la respuesta de ChatGPT."""
    message = response.choices[0].message
    
    # Guardar mensaje del usuario en el historial
    user_sessions[user_id].append({"role": "user", "content": user_message})
    
    # Limitar el historial a los últimos MAX_HISTORY_MESSAGES mensajes
    if len(user_sessions[user_id]) > MAX_HISTORY_MESSAGES:
        # Mantener solo los últimos mensajes (ventana deslizante)
        user_sessions[user_id] = user_sessions[user_id][-MAX_HISTORY_MESSAGES:]
        logger.info(f"📦 Historial limitado a {MAX_HISTORY_MESSAGES} mensajes para usuario {user_id}")
    
    if message.tool_calls:
        # Hay llamadas a funciones - recopilar resultados
        function_results = []
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            logger.info(f"🤖 ChatGPT llama a función: {function_name} con args: {function_args}")
            
            # Ejecutar función y obtener resultado
            function_result = await execute_function(function_name, function_args)
            function_results.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_result
            })
        
        # Guardar mensaje del asistente con tool_calls en historial
        user_sessions[user_id].append({
            "role": "assistant",
            "content": message.content if message.content else "",
            "tool_calls": [{
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments}
            } for tc in message.tool_calls]
        })
        
        # Agregar resultados de funciones al historial
        user_sessions[user_id].extend(function_results)
        
        # Hacer segunda llamada a ChatGPT para que procese los resultados y genere respuesta natural
        logger.info("🔄 Enviando resultados a ChatGPT para generar respuesta natural")
        
        # Crear mensajes solo con historial + system instruction (sin mensaje vacío del usuario)
        from config import openai
        messages_with_results = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        messages_with_results.extend(user_sessions[user_id])
        
        second_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_with_results
        )
        final_message = second_response.choices[0].message
        
        if final_message.content and final_message.content.strip():
            await update.message.reply_text(final_message.content, parse_mode='Markdown')
            user_sessions[user_id].append({"role": "assistant", "content": final_message.content})
        else:
            # Fallback: Si la IA no generó respuesta de texto, enviar confirmación natural
            logger.warning("⚠️ ChatGPT no retornó contenido de texto después de function call")
            fallback_msg = "Listo ✅"
            await update.message.reply_text(fallback_msg)
            user_sessions[user_id].append({"role": "assistant", "content": fallback_msg})
    
    
    elif message.content:
        # Respuesta de texto normal
        await update.message.reply_text(message.content, parse_mode='Markdown')
        
        # Guardar respuesta del asistente en el historial
        user_sessions[user_id].append({"role": "assistant", "content": message.content})
    else:
        await update.message.reply_text(
            "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
        )
        user_sessions[user_id].append({
            "role": "assistant", 
            "content": "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
        })


async def _process_gemini_response(response, chat_session, update: Update):
    """Procesa la respuesta de Gemini."""
    if response.candidates and response.candidates[0].content.parts:
        # Buscar si hay function calls y recopilar resultados
        function_calls_found = []
        text_responses = []
        
        for part in response.candidates[0].content.parts:
            # Si hay una llamada a función
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                function_name = function_call.name
                function_args = dict(function_call.args)
                
                logger.info(f"🤖 Gemini llama a función: {function_name} con args: {function_args}")
                
                # Ejecutar función y guardar resultado
                function_result = await execute_function(function_name, function_args)
                function_calls_found.append({
                    "name": function_name,
                    "result": function_result
                })
            
            # Si es solo texto
            elif hasattr(part, 'text') and part.text:
                text_responses.append(part.text)
        
        # Si hubo function calls, enviar resultados de vuelta a Gemini para respuesta natural
        if function_calls_found:
            logger.info("🔄 Enviando resultados a Gemini para generar respuesta natural")
            
            # Construir mensaje con los resultados de las funciones
            has_sent_response = False
            for fc in function_calls_found:
                try:
                    # Enviar resultado de función de vuelta al chat
                    function_response_part = types.Part.from_function_response(
                        name=fc["name"],
                        response={"result": fc["result"]}
                    )
                    
                    # Obtener respuesta final de Gemini procesando el resultado
                    final_response = chat_session.send_message(function_response_part)
                    
                    # Enviar la respuesta natural al usuario
                    if final_response.candidates and final_response.candidates[0].content.parts:
                        for final_part in final_response.candidates[0].content.parts:
                            if hasattr(final_part, 'text') and final_part.text and final_part.text.strip():
                                await update.message.reply_text(final_part.text, parse_mode='Markdown')
                                has_sent_response = True
                except Exception as func_error:
                    logger.error(f"❌ Error procesando resultado de función {fc['name']}: {func_error}")
                    # Continuar con la siguiente función
            
            # Si no se envió ninguna respuesta, enviar confirmación natural
            if not has_sent_response:
                logger.warning("⚠️ Gemini no retornó contenido de texto después de function calls")
                await update.message.reply_text("Listo ✅")
        
        # Si solo hay texto (sin function calls)
        elif text_responses:
            for text in text_responses:
                await update.message.reply_text(text, parse_mode='Markdown')
    
    # Si no hay partes en la respuesta
    else:
        await update.message.reply_text(
            "🤔 No estoy seguro de cómo ayudarte con eso. ¿Puedes reformular tu pregunta?"
        )


async def _handle_error(e: Exception, user_id: int, update: Update):
    """
    Manejo de errores inteligente.
    Solo reinicia sesión si es un error crítico de API.
    Errores menores no deberían borrar el historial.
    """
    error_str = str(e).lower()
    critical_errors = [
        'invalid api key',
        'quota exceeded',
        'rate limit',
        'authentication',
        'unauthorized',
        'invalid_request_error'
    ]
    
    # Verificar si es un error crítico que requiere reinicio
    is_critical = any(err in error_str for err in critical_errors)
    
    if is_critical:
        # Error crítico: Reiniciar sesión
        logger.warning(f"🔄 Error CRÍTICO detectado. Reiniciando sesión para usuario {user_id}")
        
        clear_session(user_id)
        
        # Crear nueva sesión
        get_or_create_session(user_id)
        
        await update.message.reply_text(
            "⚠️ borrando historial de conversacion"
        )
    else:
        # Error menor: Mantener sesión pero informar al usuario
        logger.warning(f"⚠️ Error menor detectado. Manteniendo sesión para usuario {user_id}")
        await update.message.reply_text(
            "❌ Hubo un problema procesando tu mensaje. Tu historial se mantiene intacto.\n"
            "Por favor, intenta de nuevo o reformula tu pregunta."
        )
