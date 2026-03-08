# -*- coding: utf-8 -*-
"""
Tests para el módulo de prompts - verifica que el system instruction
contiene las reglas clave para entender mensajes correctamente.
"""

import sys
import os
import pytest

# Add parent dir to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ai.prompts import get_system_instruction


class TestSystemInstruction:
    """Verifica que el prompt del sistema tiene las reglas correctas."""

    def setup_method(self):
        self.prompt = get_system_instruction()

    # --- Regla #1: Entender antes de actuar ---
    def test_has_understand_before_act_rule(self):
        """El prompt debe indicar que primero entienda el mensaje."""
        assert "ENTENDER ANTES DE ACTUAR" in self.prompt

    def test_has_step_order(self):
        """El prompt debe tener una secuencia: leer → interpretar → ejecutar."""
        assert "LEE" in self.prompt
        assert "INTERPRETA" in self.prompt
        assert "EJECUTA" in self.prompt

    # --- Mensajes cortos = gastos ---
    def test_short_messages_are_expenses(self):
        """El prompt debe instruir que 'monto + palabra' = gasto."""
        assert "MENSAJES CORTOS SIN CONTEXTO" in self.prompt
        assert "SON GASTOS" in self.prompt

    def test_example_32mil_uber(self):
        """Ejemplo clave: '32 mil uber' debe estar en el prompt."""
        assert "32 mil uber" in self.prompt.lower() or "32000" in self.prompt

    def test_example_15k_cafe(self):
        """Ejemplo clave: '15k café' debe estar."""
        assert "15k" in self.prompt.lower()

    # --- Conversiones de montos ---
    def test_has_k_conversion(self):
        """Debe explicar que 'k' o 'mil' = x1,000."""
        assert "1,000" in self.prompt or "1000" in self.prompt

    def test_has_million_conversion(self):
        """Debe explicar que 'M' o 'millón' = x1,000,000."""
        assert "1,000,000" in self.prompt or "1000000" in self.prompt

    # --- Auto-categorización ---
    def test_has_transport_keywords(self):
        """Debe tener palabras clave de transporte."""
        lower = self.prompt.lower()
        assert "uber" in lower
        assert "taxi" in lower

    def test_has_food_keywords(self):
        """Debe tener palabras clave de comida."""
        lower = self.prompt.lower()
        assert "restaurante" in lower
        assert "café" in lower

    def test_has_market_keywords(self):
        """Debe tener tiendas de mercado."""
        assert "D1" in self.prompt
        assert "ARA" in self.prompt

    # --- Reglas de decisión ---
    def test_decision_rules_exist(self):
        """Debe tener reglas claras de decisión."""
        assert "REGLAS DE DECISIÓN" in self.prompt

    def test_ambiguous_message_asks(self):
        """Si el mensaje es ambiguo, debe PREGUNTAR."""
        assert "PREGUNTAR" in self.prompt

    def test_never_guess(self):
        """Si no entiende, nunca adivines."""
        assert "nunca adivines" in self.prompt

    # --- Consulta de gastos mensuales ---
    def test_monthly_expenses_uses_financial_summary(self):
        """'Mis gastos de este mes' debe usar get_financial_summary."""
        assert "get_financial_summary" in self.prompt

    def test_monthly_total_includes_fixed_expenses(self):
        """El prompt debe aclarar que el total incluye fijos + variables."""
        lower = self.prompt.lower()
        assert "gastos fijos" in lower or "facturas fijas" in lower

    # --- Fecha actual ---
    def test_has_current_date(self):
        """El prompt debe incluir la fecha actual."""
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone(timedelta(hours=-5)))
        assert str(now.year) in self.prompt

    def test_has_current_time(self):
        """El prompt debe incluir la hora."""
        assert "Hora:" in self.prompt

    # --- Categorías ---
    def test_has_all_categories(self):
        """Debe listar todas las categorías válidas."""
        lower = self.prompt.lower()
        for cat in ["comida", "transporte", "entretenimiento", "servicios", "salud", "mercado", "general"]:
            assert cat in lower, f"Categoría '{cat}' no encontrada en prompt"

    # --- Capacidades clave ---
    def test_has_recurring_expenses(self):
        """Debe documentar gastos fijos/mensualidades."""
        assert "MENSUALIDADES" in self.prompt

    def test_has_income_features(self):
        """Debe documentar ingresos."""
        assert "INGRESOS" in self.prompt

    def test_has_savings_goals(self):
        """Debe documentar metas de ahorro."""
        assert "METAS DE AHORRO" in self.prompt

    def test_has_reminders(self):
        """Debe documentar recordatorios."""
        assert "RECORDATORIOS" in self.prompt


class TestPromptEdgeCases:
    """Verifica que el prompt maneje casos borde correctamente."""

    def setup_method(self):
        self.prompt = get_system_instruction()

    def test_prompt_is_not_empty(self):
        assert len(self.prompt) > 100

    def test_prompt_has_no_unformatted_placeholders(self):
        """No debe tener {} sin formatear."""
        # After .format(), there should be no bare {}
        assert "{}" not in self.prompt

    def test_colombia_timezone_mentioned(self):
        """Debe mencionar zona horaria Colombia."""
        assert "-05:00" in self.prompt
