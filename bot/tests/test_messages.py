# -*- coding: utf-8 -*-
"""
Tests para handlers/messages.py del bot
Verifica el fallback de Markdown y manejo de errores.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def make_mock_update(user_id=12345, chat_id=12345, text="test"):
    """Crea un mock de Update de Telegram."""
    update = MagicMock()
    update.effective_user.id = user_id
    update.effective_chat.id = chat_id
    update.message.text = text
    return update


def make_mock_context():
    """Crea un mock de Context de Telegram."""
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    context.bot.send_message = AsyncMock()
    return context


class TestHandleMessage:
    """Tests para handle_message."""

    @pytest.mark.asyncio
    async def test_sends_typing_action(self):
        """Debe enviar acción de 'typing' antes de procesar."""
        update = make_mock_update(text="32 mil uber")
        context = make_mock_context()
        
        with patch('handlers.messages.send_chat_message', new_callable=AsyncMock, return_value="✅ Gasto registrado"):
            from handlers.messages import handle_message
            await handle_message(update, context)
        
        context.bot.send_chat_action.assert_called_once_with(
            chat_id=12345, action='typing'
        )

    @pytest.mark.asyncio
    async def test_sends_reply_to_user(self):
        """Debe enviar la respuesta al usuario."""
        update = make_mock_update(text="mis gastos")
        context = make_mock_context()
        
        with patch('handlers.messages.send_chat_message', new_callable=AsyncMock, return_value="📊 Tus gastos..."):
            from handlers.messages import handle_message
            await handle_message(update, context)
        
        context.bot.send_message.assert_called()

    @pytest.mark.asyncio
    async def test_markdown_fallback_on_error(self):
        """Si Markdown falla, debe reintentar sin parse_mode."""
        update = make_mock_update(text="test")
        context = make_mock_context()
        
        # First call (with Markdown) raises, second call (without) succeeds
        call_count = [0]
        async def side_effect(**kwargs):
            call_count[0] += 1
            if call_count[0] == 1 and kwargs.get('parse_mode') == 'Markdown':
                raise Exception("Can't parse entities: Bad Request")
            return None
        
        context.bot.send_message = AsyncMock(side_effect=side_effect)
        
        with patch('handlers.messages.send_chat_message', new_callable=AsyncMock, return_value="texto con *markdown* roto"):
            from handlers.messages import handle_message
            await handle_message(update, context)
        
        # Should have been called twice: once with Markdown (failed), once without
        assert context.bot.send_message.call_count == 2

    @pytest.mark.asyncio
    async def test_passes_user_text_override(self):
        """Si se pasa user_text, debe usar ese en lugar de update.message.text."""
        update = make_mock_update(text="texto original")
        context = make_mock_context()
        
        with patch('handlers.messages.send_chat_message', new_callable=AsyncMock, return_value="ok") as mock_send:
            from handlers.messages import handle_message
            await handle_message(update, context, user_text="texto override")
        
        # Verify the API was called with the override text
        mock_send.assert_called_once_with(user_id=12345, message="texto override")


class TestSplitMessage:
    """Tests para la función split_message en utils."""

    def test_short_message_not_split(self):
        from utils import split_message
        result = split_message("Hola mundo")
        assert result == ["Hola mundo"]

    def test_long_message_is_split(self):
        from utils import split_message
        # Create a message longer than 100 chars to test splitting
        long_text = "A" * 200
        result = split_message(long_text, max_length=100)
        assert len(result) > 1
        # All parts combined should equal original
        assert "".join(result) == long_text

    def test_split_at_newline(self):
        from utils import split_message
        text = "Línea 1\n" * 50
        result = split_message(text, max_length=100)
        assert len(result) > 1
        # Each part should end cleanly (no mid-word splits)

    def test_empty_message(self):
        from utils import split_message
        result = split_message("")
        assert result == [""]
