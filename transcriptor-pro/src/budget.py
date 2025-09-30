"""
Módulo de gestión de presupuesto
Control de gastos diario para transcripciones
"""

import json
import datetime as dt
from pathlib import Path
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Archivo de presupuesto
APP_ROOT = Path(os.getenv("APPDATA", Path.home())) / ".transcriptor_pro"
BUDGET_FILE = APP_ROOT / "budget.json"


class BudgetManager:
    """Gestor de presupuesto diario"""

    def __init__(self):
        """Inicializar gestor de presupuesto"""
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Asegurar que el archivo de presupuesto existe"""
        if not BUDGET_FILE.exists():
            BUDGET_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._save_data({'limit': 2.0, 'consumed': 0.0, 'date': None})

    def _load_data(self) -> Dict:
        """
        Cargar datos de presupuesto desde disco

        Returns:
            dict: Datos de presupuesto
        """
        try:
            with open(BUDGET_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error cargando presupuesto: {e}")
            return {'limit': 2.0, 'consumed': 0.0, 'date': None}

    def _save_data(self, data: Dict) -> None:
        """
        Guardar datos de presupuesto a disco

        Args:
            data: Datos a guardar
        """
        try:
            with open(BUDGET_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Presupuesto guardado")
        except Exception as e:
            logger.error(f"Error guardando presupuesto: {e}")

    def _reset_if_new_day(self) -> Dict:
        """
        Resetear presupuesto consumido si es un nuevo día

        Returns:
            dict: Datos de presupuesto actualizados
        """
        data = self._load_data()
        today = dt.date.today().isoformat()

        if data.get('date') != today:
            logger.info(f"Nuevo día detectado, reseteando presupuesto consumido")
            data['consumed'] = 0.0
            data['date'] = today
            self._save_data(data)

        return data

    def set_limit(self, limit: float) -> None:
        """
        Establecer límite de presupuesto diario

        Args:
            limit: Límite en USD
        """
        if limit <= 0:
            raise ValueError("El límite debe ser mayor que 0")

        data = self._load_data()
        data['limit'] = limit
        self._save_data(data)
        logger.info(f"Límite de presupuesto establecido: ${limit:.2f}")

    def get_limit(self) -> float:
        """
        Obtener límite de presupuesto diario

        Returns:
            float: Límite en USD
        """
        data = self._load_data()
        return data.get('limit', 2.0)

    def check_available(self, cost: float) -> bool:
        """
        Verificar si hay presupuesto disponible para un gasto

        Args:
            cost: Coste a verificar

        Returns:
            bool: True si hay presupuesto suficiente
        """
        data = self._reset_if_new_day()
        remaining = data['limit'] - data['consumed']
        is_available = cost <= remaining

        logger.debug(
            f"Verificación presupuesto: ${cost:.4f} "
            f"(disponible: ${remaining:.4f}) -> {is_available}"
        )

        return is_available

    def consume(self, cost: float) -> None:
        """
        Consumir presupuesto

        Args:
            cost: Cantidad a consumir en USD
        """
        data = self._reset_if_new_day()
        data['consumed'] += cost
        self._save_data(data)

        logger.info(
            f"Presupuesto consumido: ${cost:.4f} "
            f"(total hoy: ${data['consumed']:.4f})"
        )

    def get_consumed(self) -> float:
        """
        Obtener presupuesto consumido hoy

        Returns:
            float: Cantidad consumida en USD
        """
        data = self._reset_if_new_day()
        return data.get('consumed', 0.0)

    def get_remaining(self) -> float:
        """
        Obtener presupuesto restante

        Returns:
            float: Cantidad restante en USD
        """
        data = self._reset_if_new_day()
        limit = data.get('limit', 2.0)
        consumed = data.get('consumed', 0.0)
        return max(0, limit - consumed)

    def get_stats(self) -> Dict:
        """
        Obtener estadísticas de presupuesto

        Returns:
            dict: Estadísticas (limit, consumed, remaining, percentage)
        """
        data = self._reset_if_new_day()
        limit = data.get('limit', 2.0)
        consumed = data.get('consumed', 0.0)
        remaining = max(0, limit - consumed)
        percentage = (consumed / limit * 100) if limit > 0 else 0

        return {
            'limit': limit,
            'consumed': consumed,
            'remaining': remaining,
            'percentage': percentage,
            'date': data.get('date')
        }

    def reset_today(self) -> None:
        """Resetear presupuesto consumido hoy (para testing)"""
        data = self._load_data()
        data['consumed'] = 0.0
        data['date'] = dt.date.today().isoformat()
        self._save_data(data)
        logger.info("Presupuesto del día reseteado")


# Instancia global (singleton pattern)
_budget_manager: Optional[BudgetManager] = None


def get_budget_manager() -> BudgetManager:
    """
    Obtener instancia del gestor de presupuesto (singleton)

    Returns:
        BudgetManager: Instancia del gestor
    """
    global _budget_manager
    if _budget_manager is None:
        _budget_manager = BudgetManager()
    return _budget_manager


# Funciones de conveniencia para mantener compatibilidad
def set_budget_limit(limit: float) -> None:
    """Establecer límite de presupuesto"""
    get_budget_manager().set_limit(limit)


def check_budget_available(cost: float) -> bool:
    """Verificar si hay presupuesto disponible"""
    return get_budget_manager().check_available(cost)


def consume_budget(cost: float) -> None:
    """Consumir presupuesto"""
    get_budget_manager().consume(cost)


def get_remaining_budget() -> float:
    """Obtener presupuesto restante"""
    return get_budget_manager().get_remaining()


def get_budget_stats() -> Dict:
    """Obtener estadísticas de presupuesto"""
    return get_budget_manager().get_stats()
