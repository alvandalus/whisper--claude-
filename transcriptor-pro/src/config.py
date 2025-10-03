"""
Módulo de configuración persistente
Gestiona la carga y guardado de configuración de la aplicación
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional
import logging

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger = logging.getLogger(__name__)
    logger.debug(".env cargado exitosamente")
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv no instalado. Variables de entorno .env no disponibles.")

# Directorio de configuración
APP_ROOT = Path(os.getenv("APPDATA", Path.home())) / ".transcriptor_pro"
TRANSCRIPTS_DIR = APP_ROOT / "transcripts"
CONFIG_FILE = APP_ROOT / "config.json"
LOGS_DIR = APP_ROOT / "logs"

# Crear directorios necesarios
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class AppConfig:
    """Configuración de la aplicación"""
    # Modelo y proveedor
    model: str = field(default_factory=lambda: os.getenv("DEFAULT_MODEL", "groq-whisper-large-v3"))

    # API Keys (primero desde .env, luego desde config guardado)
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))

    # Opciones de procesamiento
    bitrate: int = field(default_factory=lambda: int(os.getenv("AUDIO_BITRATE", "192")))
    use_vad: bool = field(default_factory=lambda: os.getenv("USE_VAD", "false").lower() == "true")
    export_srt: bool = field(default_factory=lambda: os.getenv("EXPORT_SRT", "true").lower() == "true")

    # Directorios
    output_dir: str = field(default_factory=lambda: os.getenv("OUTPUT_DIR", str(TRANSCRIPTS_DIR)))
    inbox_dir: str = field(default_factory=lambda: os.getenv("INBOX_DIR", str(Path.home() / "TranscriptorPro" / "INBOX")))

    # Presupuesto
    daily_budget: float = field(default_factory=lambda: float(os.getenv("DAILY_BUDGET", "2.0")))

    # Historial
    history: list = field(default_factory=list)

    def save(self) -> None:
        """Guardar configuración en disco"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            config_data = asdict(self)

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuración guardada: {CONFIG_FILE}")

        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            raise

    @classmethod
    def load(cls) -> 'AppConfig':
        """Cargar configuración desde disco"""
        try:
            if CONFIG_FILE.exists():
                logger.info(f"Cargando configuración: {CONFIG_FILE}")

                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Filtrar solo campos válidos
                valid_fields = {k: v for k, v in data.items()
                              if k in cls.__dataclass_fields__}

                logger.info(f"Configuración cargada: {len(valid_fields)} campos")
                return cls(**valid_fields)
            else:
                logger.info("Configuración no existe, usando valores por defecto")

        except Exception as e:
            logger.warning(f"Error cargando configuración: {e}")

        return cls()

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validar configuración

        Returns:
            tuple: (es_válida, mensaje_error)
        """
        # Validar que al menos una API key esté configurada
        if not self.model.startswith('local'):
            if not self.openai_api_key and not self.groq_api_key:
                return False, "Se requiere al menos una API key (OpenAI o Groq)"

        # Validar presupuesto
        if self.daily_budget <= 0:
            return False, "El presupuesto diario debe ser mayor que 0"

        # Validar bitrate
        if self.bitrate < 64 or self.bitrate > 320:
            return False, "El bitrate debe estar entre 64 y 320 kbps"

        return True, None

    def setup_environment(self) -> None:
        """Configurar variables de entorno para APIs"""
        if self.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            logger.debug("OpenAI API key configurada")

        if self.groq_api_key:
            os.environ['GROQ_API_KEY'] = self.groq_api_key
            logger.debug("Groq API key configurada")


def get_config() -> AppConfig:
    """
    Obtener configuración (singleton helper)

    Returns:
        AppConfig: Configuración cargada
    """
    return AppConfig.load()
