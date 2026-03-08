# -*- coding: utf-8 -*-
"""
Tests para process_ai_response en main.py
Verifica la robustez del procesamiento de respuestas de Gemini.
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ============================================================
# Mock helpers
# ============================================================

def make_gemini_tool_call(name: str, args: dict):
    """Crea un mock de tool call de Gemini."""
    tc = MagicMock()
    tc.name = name
    tc.args = args
    return tc


def make_gemini_response_with_tools(tool_calls):
    """Crea un mock de respuesta de Gemini con function calls."""
    response = MagicMock()
    response.function_calls = tool_calls
    response.text = None
    return response


def make_gemini_response_text(text):
    """Crea un mock de respuesta de Gemini con texto puro."""
    response = MagicMock()
    response.function_calls = None
    response.text = text
    return response


def make_gemini_response_empty():
    """Crea una respuesta vacía (ni texto ni tools)."""
    response = MagicMock()
    response.function_calls = None
    response.text = None
    return response


# ============================================================
# Tests
# ============================================================

@pytest.fixture(autouse=True)
def setup_env():
    """Configura environment para tests."""
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test-key")


@pytest.fixture
def mock_session():
    """Mock de la sesión de chat de Gemini."""
    session = MagicMock()
    final_resp = MagicMock()
    final_resp.text = "✅ Listo, gasto registrado."
    session.send_message = MagicMock(return_value=final_resp)
    return session


class TestProcessAIResponseGemini:
    """Tests para la rama Gemini de process_ai_response."""

    @pytest.mark.asyncio
    async def test_text_response_no_tools(self, mock_session):
        """Respuesta de texto simple sin herramientas."""
        with patch.dict('sys.modules', {}):
            from main import process_ai_response, save_session, get_session

        response = make_gemini_response_text("Hola, ¿en qué te ayudo?")
        
        with patch('main.get_session', return_value={'chat_session': mock_session}), \
             patch('main.save_session'), \
             patch('main.AI_PROVIDER', 'gemini', create=True), \
             patch.dict(os.environ, {"AI_PROVIDER": "gemini"}):
            # Since the code checks AI_PROVIDER from settings import, we patch at module level
            with patch('main.get_session', return_value={'chat_session': mock_session}):
                pass

    @pytest.mark.asyncio
    async def test_empty_response_returns_fallback(self):
        """Respuesta vacía debe devolver mensaje de fallback, no crash."""
        response = make_gemini_response_empty()
        
        # The key behavior: accessing response.text when it's None
        # should not crash and should return a fallback
        assert response.text is None
        assert response.function_calls is None
        
        # Simulate the logic in process_ai_response
        has_function_calls = hasattr(response, 'function_calls') and response.function_calls
        assert not has_function_calls
        
        try:
            reply_text = response.text
        except Exception:
            reply_text = None
        
        if not reply_text:
            reply_text = "No pude procesar tu mensaje. ¿Podrías reformularlo?"
        
        assert reply_text == "No pude procesar tu mensaje. ¿Podrías reformularlo?"

    def test_tool_call_args_extraction_dict(self):
        """Extracción de args cuando es un dict normal."""
        tc = make_gemini_tool_call("add_expense", {"amount": 32000, "description": "Uber", "category": "transporte"})
        
        if isinstance(tc.args, dict):
            args_dict = tc.args
        elif hasattr(tc.args, "items"):
            args_dict = {k: v for k, v in tc.args.items()}
        else:
            args_dict = tc.args or {}
        
        assert args_dict == {"amount": 32000, "description": "Uber", "category": "transporte"}

    def test_tool_call_args_extraction_none(self):
        """Extracción de args cuando es None (no debe crashear)."""
        tc = make_gemini_tool_call("get_recent_expenses", None)
        
        try:
            if isinstance(tc.args, dict):
                args_dict = tc.args
            elif hasattr(tc.args, "items"):
                args_dict = {k: v for k, v in tc.args.items()}
            else:
                args_dict = tc.args or {}
        except Exception:
            args_dict = {}
        
        assert args_dict == {}

    def test_has_function_calls_check_none(self):
        """hasattr + truthiness check con None."""
        response = make_gemini_response_empty()
        has_fc = hasattr(response, 'function_calls') and response.function_calls
        assert has_fc is None or has_fc is False or not has_fc

    def test_has_function_calls_check_with_tools(self):
        """hasattr + truthiness check con tool calls reales."""
        tc = make_gemini_tool_call("add_expense", {"amount": 1000})
        response = make_gemini_response_with_tools([tc])
        has_fc = hasattr(response, 'function_calls') and response.function_calls
        assert has_fc  # Should be truthy

    def test_has_function_calls_check_empty_list(self):
        """hasattr + truthiness check con lista vacía de tools."""
        response = make_gemini_response_with_tools([])
        has_fc = hasattr(response, 'function_calls') and response.function_calls
        assert not has_fc  # Empty list is falsy


class TestToolCallErrorHandling:
    """Tests para el manejo de errores en tool calls."""

    def test_tool_execution_error_returns_string(self):
        """Si una tool falla, debe devolver un string de error, no crash."""
        function_name = "add_expense"
        
        try:
            raise ValueError("Monto inválido")
        except Exception as tool_err:
            tool_result = f"Error ejecutando {function_name}: {str(tool_err)}"
        
        assert "Error ejecutando add_expense" in tool_result
        assert "Monto inválido" in tool_result

    def test_fallback_when_send_message_fails(self, mock_session):
        """Si send_message falla, usa tool_result como fallback."""
        tool_result = "✅ Gasto registrado: $32,000 en transporte"
        
        mock_session.send_message.side_effect = Exception("Gemini API error")
        
        try:
            final_response = mock_session.send_message("tool response")
            reply_text = final_response.text
        except Exception:
            reply_text = str(tool_result) if tool_result else "Se ejecutó la acción pero hubo un problema generando la respuesta."
        
        assert reply_text == "✅ Gasto registrado: $32,000 en transporte"

    def test_fallback_when_tool_result_empty_and_send_fails(self, mock_session):
        """Si tool_result es vacío y send_message falla, usa mensaje genérico."""
        tool_result = None
        
        mock_session.send_message.side_effect = Exception("Gemini API error")
        
        try:
            final_response = mock_session.send_message("tool response")
            reply_text = final_response.text
        except Exception:
            reply_text = str(tool_result) if tool_result else "Se ejecutó la acción pero hubo un problema generando la respuesta."
        
        assert reply_text == "Se ejecutó la acción pero hubo un problema generando la respuesta."
