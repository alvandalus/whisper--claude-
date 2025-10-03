"""
Tests para el módulo de configuración
"""

import pytest
from pathlib import Path
import json
import tempfile
from src.config import AppConfig, CONFIG_FILE


class TestAppConfig:
    """Tests para la clase AppConfig"""

    def test_config_creation_with_defaults(self):
        """Test creación de configuración con valores por defecto"""
        config = AppConfig()
        assert config.model == "groq-whisper-large-v3"
        assert config.bitrate == 192
        assert config.daily_budget == 2.0
        assert config.export_srt is True

    def test_config_with_env_vars(self, mock_env_vars):
        """Test carga de configuración desde variables de entorno"""
        config = AppConfig()
        assert config.groq_api_key == "test_groq_key"
        assert config.openai_api_key == "test_openai_key"

    def test_config_validation_success(self):
        """Test validación exitosa de configuración"""
        config = AppConfig(groq_api_key="test_key")
        is_valid, error = config.validate()
        assert is_valid is True
        assert error is None

    def test_config_validation_no_api_keys(self):
        """Test validación falla sin API keys"""
        config = AppConfig(openai_api_key="", groq_api_key="")
        is_valid, error = config.validate()
        assert is_valid is False
        assert "API key" in error

    def test_config_validation_invalid_budget(self):
        """Test validación falla con presupuesto inválido"""
        config = AppConfig(daily_budget=-1.0, groq_api_key="test")
        is_valid, error = config.validate()
        assert is_valid is False
        assert "presupuesto" in error.lower()

    def test_config_validation_invalid_bitrate(self):
        """Test validación falla con bitrate inválido"""
        config = AppConfig(bitrate=500, groq_api_key="test")
        is_valid, error = config.validate()
        assert is_valid is False
        assert "bitrate" in error.lower()

    def test_config_save_and_load(self, temp_dir, monkeypatch):
        """Test guardado y carga de configuración"""
        # Crear config temporal
        config_file = temp_dir / "config.json"
        monkeypatch.setattr("src.config.CONFIG_FILE", config_file)

        # Crear y guardar configuración
        config = AppConfig(
            model="groq-whisper-large-v3",
            groq_api_key="test_key",
            daily_budget=5.0
        )
        config.save()

        # Verificar que se guardó
        assert config_file.exists()

        # Cargar y verificar
        with open(config_file) as f:
            data = json.load(f)
        assert data["model"] == "groq-whisper-large-v3"
        assert data["groq_api_key"] == "test_key"
        assert data["daily_budget"] == 5.0

    def test_setup_environment(self, monkeypatch):
        """Test configuración de variables de entorno"""
        import os
        config = AppConfig(
            openai_api_key="openai_test",
            groq_api_key="groq_test"
        )
        config.setup_environment()

        assert os.environ.get("OPENAI_API_KEY") == "openai_test"
        assert os.environ.get("GROQ_API_KEY") == "groq_test"
