"""
Tests para el módulo core de transcripción
"""

import pytest
from pathlib import Path
from src.core import (
    calculate_cost,
    TranscriptionResult,
    MODEL_PRICING,
    PROVIDER_MAPPING,
    get_model_info,
    get_all_models
)


class TestCostCalculation:
    """Tests para cálculo de costes"""

    def test_calculate_cost_groq_whisper(self):
        """Test cálculo de coste con Groq Whisper"""
        duration = 60  # 1 minuto
        model = "groq-whisper-large-v3"
        cost = calculate_cost(duration, model)
        expected = MODEL_PRICING[model]
        assert cost == pytest.approx(expected, rel=0.01)

    def test_calculate_cost_openai(self):
        """Test cálculo de coste con OpenAI"""
        duration = 120  # 2 minutos
        model = "whisper-1"
        cost = calculate_cost(duration, model)
        expected = 2 * MODEL_PRICING[model]
        assert cost == pytest.approx(expected, rel=0.01)

    def test_calculate_cost_local_is_free(self):
        """Test que modelos locales son gratis"""
        duration = 3600  # 1 hora
        model = "local-base"
        cost = calculate_cost(duration, model)
        assert cost == 0.0

    def test_calculate_cost_minimum_duration(self):
        """Test que duración mínima es 1 minuto"""
        duration = 30  # 30 segundos
        model = "whisper-1"
        cost = calculate_cost(duration, model)
        # Debe cobrar como mínimo 1 minuto
        expected = MODEL_PRICING[model]
        assert cost == pytest.approx(expected, rel=0.01)


class TestTranscriptionResult:
    """Tests para TranscriptionResult"""

    def test_transcription_result_creation(self):
        """Test creación de resultado de transcripción"""
        result = TranscriptionResult(
            text="Hola mundo",
            segments=[{"start": 0, "end": 1, "text": "Hola mundo"}],
            language="es",
            duration=1.0,
            cost=0.001,
            model="groq-whisper-large-v3"
        )
        assert result.text == "Hola mundo"
        assert len(result.segments) == 1
        assert result.language == "es"

    def test_transcription_result_text_strip(self):
        """Test que el texto se limpia de espacios"""
        result = TranscriptionResult(text="  Texto con espacios  ")
        assert result.text == "Texto con espacios"

    def test_transcription_result_default_segments(self):
        """Test segmentos por defecto es lista vacía"""
        result = TranscriptionResult(text="Test")
        assert result.segments == []


class TestModelInfo:
    """Tests para información de modelos"""

    def test_get_all_models(self):
        """Test obtener todos los modelos"""
        models = get_all_models()
        assert len(models) > 0
        assert "groq-whisper-large-v3" in models
        assert "whisper-1" in models
        assert "local-base" in models

    def test_get_model_info(self):
        """Test obtener información de un modelo"""
        info = get_model_info("groq-whisper-large-v3")
        assert info["provider"] == "groq"
        assert info["cost_per_minute"] == MODEL_PRICING["groq-whisper-large-v3"]

    def test_provider_mapping(self):
        """Test mapeo de proveedores"""
        assert PROVIDER_MAPPING["whisper-1"] == "openai"
        assert PROVIDER_MAPPING["groq-whisper-large-v3"] == "groq"
        assert PROVIDER_MAPPING["local-base"] == "local"
