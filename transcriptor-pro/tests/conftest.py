"""
Configuración de pytest
"""

import pytest
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_dir():
    """Crea un directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_path(temp_dir):
    """Crea un archivo de audio de prueba"""
    audio_file = temp_dir / "test_audio.mp3"
    # Crear un archivo vacío para pruebas
    audio_file.touch()
    return audio_file


@pytest.fixture
def mock_config(temp_dir):
    """Configuración de prueba"""
    from src.config import AppConfig

    config = AppConfig(
        model="groq-whisper-large-v3",
        groq_api_key="test_api_key",
        openai_api_key="",
        bitrate=192,
        use_vad=False,
        export_srt=True,
        output_dir=str(temp_dir / "output"),
        inbox_dir=str(temp_dir / "inbox"),
        daily_budget=2.0
    )
    return config


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Variables de entorno de prueba"""
    monkeypatch.setenv("GROQ_API_KEY", "test_groq_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    monkeypatch.setenv("DEFAULT_MODEL", "groq-whisper-large-v3")
    monkeypatch.setenv("DAILY_BUDGET", "2.0")
