"""
Handler de mensajes de usuario (Cliente)
Delega todo su contenido y archivos al Backend API
"""

import traceback
from telegram import Update
from telegram.ext import ContextTypes
from config import logger
from api_client import send_chat_message, send_voice_message

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, user_text: str = None) -> None:
    """Maneja los mensajes de texto mandándolos al Backend API."""
    user_id = update.effective_user.id
    message_text = user_text or update.message.text
    
    # Enviar acción de 'escribiendo...'
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    logger.info(f"👤 Procesando mensaje de usuario {user_id}: {message_text[:50]}...")
    
    # Comunicarse con el Backend
    reply = await send_chat_message(user_id=user_id, message=message_text)
    
    from utils import split_message
    messages = split_message(reply)
    for msg in messages:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            parse_mode='Markdown'
        )

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Maneja mensajes de voz enviándolos al Backend para transcripción y respuesta."""
    user_id = update.effective_user.id
    
    # Enviar acción de 'grabando nota de voz...' o 'escribiendo...'
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    voice_file = await context.bot.get_file(update.message.voice.file_id)
    file_bytes = await voice_file.download_as_bytearray()
    
    logger.info(f"🎙️ Procesando mensaje de voz de usuario {user_id}")
    reply = await send_voice_message(user_id=user_id, audio_bytes=bytes(file_bytes))
    
    from utils import split_message
    messages = split_message(reply)
    for msg in messages:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            parse_mode='Markdown'
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manejo de errores del bot cliente."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    traceback.print_exc()
    pass
