"""
Tests para el módulo de gestión de presupuesto
"""

import pytest
from datetime import datetime, timedelta
from src.budget import BudgetManager


class TestBudgetManager:
    """Tests para BudgetManager"""

    def test_budget_manager_creation(self, temp_dir):
        """Test creación de gestor de presupuesto"""
        budget_file = temp_dir / "budget.json"
        manager = BudgetManager(daily_limit=2.0, budget_file=budget_file)
        assert manager.daily_limit == 2.0
        assert manager.spent_today == 0.0

    def test_add_expense(self, temp_dir):
        """Test agregar gasto"""
        budget_file = temp_dir / "budget.json"
        manager = BudgetManager(daily_limit=2.0, budget_file=budget_file)

        manager.add_expense(0.5, "test_model", 60)
        assert manager.spent_today == 0.5

    def test_can_spend_within_budget(self, temp_dir):
        """Test verificar si se puede gastar dentro del presupuesto"""
        budget_file = temp_dir / "budget.json"
        manager = BudgetManager(daily_limit=2.0, budget_file=budget_file)

        assert manager.can_spend(0.5) is True
        manager.add_expense(1.5, "test_model", 60)
        assert manager.can_spend(0.6) is False
        assert manager.can_spend(0.4) is True

    def test_budget_reset_on_new_day(self, temp_dir):
        """Test reset de presupuesto en nuevo día"""
        budget_file = temp_dir / "budget.json"
        manager = BudgetManager(daily_limit=2.0, budget_file=budget_file)

        # Gastar algo
        manager.add_expense(1.0, "test_model", 60)
        assert manager.spent_today == 1.0

        # Simular nuevo día
        manager.last_reset = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        manager._check_reset()

        assert manager.spent_today == 0.0

    def test_get_remaining_budget(self, temp_dir):
        """Test obtener presupuesto restante"""
        budget_file = temp_dir / "budget.json"
        manager = BudgetManager(daily_limit=2.0, budget_file=budget_file)

        assert manager.get_remaining() == 2.0
        manager.add_expense(0.75, "test_model", 60)
        assert manager.get_remaining() == 1.25

    def test_save_and_load_budget(self, temp_dir):
        """Test guardar y cargar presupuesto"""
        budget_file = temp_dir / "budget.json"

        # Crear y guardar
        manager1 = BudgetManager(daily_limit=2.0, budget_file=budget_file)
        manager1.add_expense(1.5, "test_model", 60)
        manager1.save()

        # Cargar en nueva instancia
        manager2 = BudgetManager(daily_limit=2.0, budget_file=budget_file)
        manager2.load()

        assert manager2.spent_today == 1.5
