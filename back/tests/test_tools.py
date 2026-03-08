# -*- coding: utf-8 -*-
"""
Tests para ai/tools.py - Verifica que todas las funciones están
registradas y que execute_function maneja errores correctamente.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture(autouse=True)
def setup_env():
    os.environ.setdefault("GEMINI_API_KEY", "test-key")
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test-key")


class TestToolDeclarations:
    """Verifica que las herramientas están declaradas correctamente."""

    def test_all_tools_exists(self):
        from ai.tools import all_tools
        assert all_tools is not None

    def test_all_tools_has_function_declarations(self):
        from ai.tools import all_tools
        assert hasattr(all_tools, 'function_declarations')
        assert len(all_tools.function_declarations) > 0

    def test_expense_tools_exist(self):
        """Las herramientas de gastos deben existir."""
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "add_expense" in names
        assert "get_recent_expenses" in names
        assert "update_expense" in names
        assert "delete_expense" in names

    def test_query_tools_exist(self):
        """Las herramientas de consulta deben existir."""
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "get_expenses_by_day" in names
        assert "get_expenses_by_week" in names
        assert "get_expenses_by_category" in names
        assert "get_expenses_by_month" in names

    def test_recurring_tools_exist(self):
        """Las herramientas de gastos fijos deben existir."""
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "add_recurring_expense" in names
        assert "get_recurring_expenses" in names
        assert "get_pending_payments" in names
        assert "mark_bill_paid" in names
        assert "find_recurring_by_name" in names

    def test_financial_summary_exists(self):
        """get_financial_summary debe existir (clave para gastos del mes)."""
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "get_financial_summary" in names

    def test_income_tools_exist(self):
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "set_fixed_salary" in names
        assert "add_extra_income" in names
        assert "get_income_summary" in names

    def test_savings_tools_exist(self):
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "add_savings_goal" in names
        assert "get_savings_goals" in names
        assert "add_contribution_to_savings" in names

    def test_reminder_tool_exists(self):
        from ai.tools import all_tools
        names = [fd.name for fd in all_tools.function_declarations]
        assert "add_reminder" in names

    def test_add_expense_has_required_params(self):
        """add_expense debe requerir amount, description, category."""
        from ai.tools import all_tools
        for fd in all_tools.function_declarations:
            if fd.name == "add_expense":
                required = fd.parameters.required
                assert "amount" in required
                assert "description" in required
                assert "category" in required
                break

    def test_add_expense_category_has_enum(self):
        """add_expense category debe tener enum con las categorías válidas."""
        from ai.tools import all_tools
        for fd in all_tools.function_declarations:
            if fd.name == "add_expense":
                cat_schema = fd.parameters.properties["category"]
                assert cat_schema.enum is not None
                enums = list(cat_schema.enum)
                assert "comida" in enums
                assert "transporte" in enums
                assert "mercado" in enums
                break


class TestExecuteFunction:
    """Tests para la función execute_function."""

    @pytest.mark.asyncio
    async def test_unknown_function_returns_warning(self):
        """Función desconocida debe retornar aviso, no crash."""
        from ai.tools import execute_function
        result = await execute_function("funcion_inexistente", {}, "123")
        assert "⚠️" in result or "desconocida" in result.lower()

    @pytest.mark.asyncio
    async def test_add_expense_with_mock(self):
        """add_expense debe ejecutarse sin error con mock de DB."""
        from ai.tools import execute_function
        
        mock_result = {"success": True, "message": "✅ Gasto registrado: $32,000 en transporte", "data": []}
        
        with patch('ai.tools.add_expense', return_value=mock_result):
            result = await execute_function(
                "add_expense",
                {"amount": 32000, "description": "Uber", "category": "transporte"},
                "123"
            )
        assert "✅" in result
        assert "32,000" in result or "32000" in result

    @pytest.mark.asyncio
    async def test_get_recent_expenses_with_mock(self):
        """get_recent_expenses debe ejecutarse sin error."""
        from ai.tools import execute_function
        
        with patch('ai.tools.get_recent_expenses', return_value="📊 No tienes gastos"):
            result = await execute_function("get_recent_expenses", {}, "123")
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_financial_summary_with_mock(self):
        """get_financial_summary es la función clave para 'gastos del mes'."""
        from ai.tools import execute_function
        
        summary = "📊 **BALANCE GENERAL**\n\nTotal gastos: $500,000\nFacturas pagadas: $200,000"
        with patch('ai.tools.get_financial_summary', return_value=summary):
            result = await execute_function("get_financial_summary", {}, "123")
        assert "BALANCE GENERAL" in result

    @pytest.mark.asyncio
    async def test_execute_function_handles_db_error(self):
        """Si la DB falla, debe retornar error formateado, no crash."""
        from ai.tools import execute_function
        
        with patch('ai.tools.add_expense', side_effect=Exception("Connection refused")):
            result = await execute_function(
                "add_expense",
                {"amount": 1000, "description": "test", "category": "general"},
                "123"
            )
        assert "Error" in result or "❌" in result
