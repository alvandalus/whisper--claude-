"""
Módulo core de transcripción
Motor principal para transcribir audio con múltiples proveedores
"""

import os
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

from .audio_utils import get_audio_duration, split_audio_for_api

logger = logging.getLogger(__name__)

# Costes por minuto en USD
MODEL_PRICING = {
    'whisper-1': 0.006,
    'groq-whisper-large-v3': 0.00011,
    'groq-distil-whisper-large-v3-en': 0.00002,
    'local-tiny': 0.0,
    'local-base': 0.0,
    'local-small': 0.0,
    'local-medium': 0.0,
    'local-large': 0.0,
}

# Mapeo de modelos a proveedores
PROVIDER_MAPPING = {
    'whisper-1': 'openai',
    'groq-whisper-large-v3': 'groq',
    'groq-distil-whisper-large-v3-en': 'groq',
    'local-tiny': 'local',
    'local-base': 'local',
    'local-small': 'local',
    'local-medium': 'local',
    'local-large': 'local',
}


@dataclass
class TranscriptionResult:
    """Resultado de una transcripción"""
    text: str
    segments: List[Dict] = None
    language: str = 'es'
    duration: float = 0.0
    cost: float = 0.0
    model: str = ''

    def __post_init__(self):
        if self.segments is None:
            self.segments = []
        self.text = self.text.strip() if self.text else ""


def calculate_cost(duration_seconds: int, model: str) -> float:
    """
    Calcular coste de transcripción

    Args:
        duration_seconds: Duración en segundos
        model: Modelo a utilizar

    Returns:
        float: Coste en USD
    """
    minutes = max(1, duration_seconds / 60.0)
    price_per_min = MODEL_PRICING.get(model, 0.006)
    cost = minutes * price_per_min

    logger.debug(f"Coste calculado: {duration_seconds}s con {model} = ${cost:.4f}")
    return cost


def transcribe_with_groq(audio_path: Path, model: str = "whisper-large-v3",
                        api_key: str = None) -> TranscriptionResult:
    """
    Transcribir usando Groq API

    Args:
        audio_path: Ruta al archivo de audio
        model: Modelo a utilizar
        api_key: API key de Groq

    Returns:
        TranscriptionResult: Resultado de la transcripción

    Raises:
        ImportError: Si el cliente de Groq no está instalado
        ValueError: Si no hay API key o es inválida
        RuntimeError: Si hay error en la transcripción
    """
    try:
        from groq import Groq
    except ImportError:
        raise ImportError(
            "Cliente de Groq no instalado.\n"
            "Instala con: pip install groq"
        )

    if api_key is None:
        api_key = os.getenv('GROQ_API_KEY')

    if not api_key:
        raise ValueError(
            "API key de Groq no encontrada.\n"
            "Configúrala en Settings o como variable GROQ_API_KEY"
        )

    # Normalizar nombre del modelo
    if model.startswith('groq-'):
        model = model.replace('groq-', '')

    try:
        logger.info(f"Transcribiendo con Groq: {audio_path.name}")

        client = Groq(api_key=api_key)

        # Verificar tamaño
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(
                f"Archivo muy grande ({file_size_mb:.1f}MB). "
                f"Máximo: 25MB. Usa split_audio_for_api() primero."
            )

        with open(audio_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                language="es"
            )

        # Extraer segmentos
        segments = []
        if hasattr(transcription, 'segments') and transcription.segments:
            for seg in transcription.segments:
                segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })

        text = transcription.text if hasattr(transcription, 'text') else str(transcription)
        language = getattr(transcription, 'language', 'es')

        logger.info(f"Transcripción Groq exitosa: {len(text)} caracteres")

        return TranscriptionResult(
            text=text,
            segments=segments,
            language=language
        )

    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower():
            raise ValueError("API key de Groq inválida")
        elif 'rate' in error_msg.lower():
            raise ValueError("Límite de rate excedido. Espera un momento.")
        else:
            raise RuntimeError(f"Error con Groq API: {error_msg}")


def transcribe_with_openai(audio_path: Path, model: str = "whisper-1",
                          api_key: str = None) -> TranscriptionResult:
    """
    Transcribir usando OpenAI API

    Args:
        audio_path: Ruta al archivo de audio
        model: Modelo a utilizar
        api_key: API key de OpenAI

    Returns:
        TranscriptionResult: Resultado de la transcripción

    Raises:
        ImportError: Si el cliente de OpenAI no está instalado
        ValueError: Si no hay API key o es inválida
        RuntimeError: Si hay error en la transcripción
    """
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        raise ValueError(
            "API key de OpenAI no encontrada.\n"
            "Configúrala en Settings o como variable OPENAI_API_KEY"
        )

    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "Cliente de OpenAI no instalado.\n"
            "Instala con: pip install openai"
        )

    try:
        logger.info(f"Transcribiendo con OpenAI: {audio_path.name}")

        client = OpenAI(api_key=api_key)

        # Verificar tamaño
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(
                f"Archivo muy grande ({file_size_mb:.1f}MB). "
                f"Máximo: 25MB. Usa split_audio_for_api() primero."
            )

        with open(audio_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                language="es"
            )

            # Convertir respuesta a dict
            if hasattr(transcription, 'model_dump'):
                result_dict = transcription.model_dump()
            else:
                result_dict = transcription if isinstance(transcription, dict) else transcription.__dict__

            # Extraer segmentos
            segments = []
            if 'segments' in result_dict:
                for seg in result_dict['segments']:
                    if isinstance(seg, dict):
                        segments.append({
                            'start': seg.get('start', 0),
                            'end': seg.get('end', 0),
                            'text': seg.get('text', '')
                        })
                    else:
                        segments.append({
                            'start': getattr(seg, 'start', 0),
                            'end': getattr(seg, 'end', 0),
                            'text': getattr(seg, 'text', '')
                        })

            text = result_dict.get('text', '') if isinstance(result_dict, dict) else getattr(transcription, 'text', str(transcription))

            logger.info(f"Transcripción OpenAI exitosa: {len(text)} caracteres")

            return TranscriptionResult(
                text=text,
                segments=segments,
                language='es'
            )

    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            raise ValueError("API key de OpenAI inválida")
        elif 'rate' in error_msg.lower() or 'quota' in error_msg.lower():
            raise ValueError("Límite de cuota o rate excedido")
        else:
            raise RuntimeError(f"Error con OpenAI API: {error_msg}")


def transcribe_with_local(audio_path: Path, model_size: str = "base") -> TranscriptionResult:
    """
    Transcribir usando Whisper local

    Args:
        audio_path: Ruta al archivo de audio
        model_size: Tamaño del modelo (tiny, base, small, medium, large)

    Returns:
        TranscriptionResult: Resultado de la transcripción

    Raises:
        ImportError: Si Whisper no está instalado
        RuntimeError: Si hay error en la transcripción
    """
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "Whisper no está instalado.\n"
            "Instala con: pip install openai-whisper\n"
            "Nota: Requiere varios GB de RAM"
        )

    # Normalizar nombre del modelo
    if model_size.startswith('local-'):
        model_size = model_size.replace('local-', '')

    try:
        logger.info(f"Cargando modelo Whisper {model_size}...")
        model = whisper.load_model(model_size)

        logger.info(f"Transcribiendo localmente: {audio_path.name}")
        result = model.transcribe(
            str(audio_path),
            language="es",
            word_timestamps=False,
            fp16=False,
            verbose=False
        )

        text = result.get('text', '').strip()
        segments = result.get('segments', [])
        language = result.get('language', 'es')

        logger.info(f"Transcripción local exitosa: {len(text)} caracteres")

        return TranscriptionResult(
            text=text,
            segments=segments,
            language=language
        )

    except Exception as e:
        raise RuntimeError(f"Error en transcripción local: {e}")


def transcribe_audio(audio_path: Path, model: str = "groq-whisper-large-v3",
                     api_key: str = None) -> TranscriptionResult:
    """
    Transcribir archivo de audio usando el proveedor apropiado

    Args:
        audio_path: Ruta al archivo de audio
        model: Modelo a utilizar
        api_key: API key (opcional, se obtiene de variables de entorno)

    Returns:
        TranscriptionResult: Resultado de la transcripción

    Raises:
        FileNotFoundError: Si el archivo no existe
        RuntimeError: Si hay error en la transcripción
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {audio_path}")

    provider = PROVIDER_MAPPING.get(model, 'groq')
    logger.info(f"Transcribiendo con proveedor: {provider}, modelo: {model}")

    try:
        # Si es local, transcribir directamente
        if provider == 'local':
            return transcribe_with_local(audio_path, model)

        # Dividir en chunks si es necesario
        chunks = split_audio_for_api(audio_path)

        # Un solo chunk, transcribir directamente
        if len(chunks) == 1:
            if provider == 'groq':
                return transcribe_with_groq(chunks[0], model, api_key)
            else:
                return transcribe_with_openai(chunks[0], model, api_key)

        # Múltiples chunks, procesar y combinar
        logger.info(f"Procesando {len(chunks)} chunks...")
        return _transcribe_multiple_chunks(chunks, provider, model, api_key)

    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise RuntimeError(f"Error transcribiendo con {provider}: {str(e)}")


def _transcribe_multiple_chunks(chunks: List[Path], provider: str,
                                model: str, api_key: str = None) -> TranscriptionResult:
    """
    Transcribir múltiples chunks y combinar resultados

    Args:
        chunks: Lista de archivos de audio
        provider: Proveedor (groq/openai)
        model: Modelo a utilizar
        api_key: API key

    Returns:
        TranscriptionResult: Resultado combinado
    """
    all_text = []
    all_segments = []

    chunk_duration = 1200  # 20 minutos
    overlap = 5  # Segundos de solapamiento
    overlap_threshold = 2.0

    for i, chunk in enumerate(chunks):
        logger.info(f"Procesando chunk {i+1}/{len(chunks)}: {chunk.name}")

        # Transcribir chunk
        if provider == 'groq':
            result = transcribe_with_groq(chunk, model, api_key)
        else:
            result = transcribe_with_openai(chunk, model, api_key)

        # Ajustar tiempos de segmentos
        offset = i * (chunk_duration - overlap)

        # Filtrar segmentos duplicados en zona de solapamiento
        if i > 0 and result.segments:
            result.segments = [s for s in result.segments if s['start'] >= overlap_threshold]

        # Ajustar timestamps
        for seg in result.segments:
            seg['start'] += offset
            seg['end'] += offset

        # Agregar texto
        text = result.text.strip()
        if text:
            if all_text and not text.startswith(('.', '!', '?', ',')):
                all_text.append(' ' + text)
            else:
                all_text.append(text)

        all_segments.extend(result.segments)

    # Ordenar segmentos por tiempo
    all_segments.sort(key=lambda x: x['start'])

    combined_text = ''.join(all_text)
    logger.info(f"Chunks combinados: {len(combined_text)} caracteres totales")

    return TranscriptionResult(
        text=combined_text,
        segments=all_segments,
        language='es'
    )


def generate_srt(result: TranscriptionResult) -> str:
    """
    Generar archivo SRT desde resultado de transcripción

    Args:
        result: Resultado de transcripción

    Returns:
        str: Contenido del archivo SRT
    """
    if not result.segments:
        # Sin segmentos, crear uno por defecto
        return "1\n00:00:00,000 --> 00:00:10,000\n" + result.text + "\n"

    lines = []
    for i, seg in enumerate(result.segments, 1):
        start = seg.get('start', 0)
        end = seg.get('end', start + 1)
        text = seg.get('text', '').strip()

        if not text:
            continue

        start_time = _format_srt_timestamp(start)
        end_time = _format_srt_timestamp(end)

        lines.append(str(i))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines) if lines else ""


def _format_srt_timestamp(seconds: float) -> str:
    """
    Formatear timestamp para SRT

    Args:
        seconds: Tiempo en segundos

    Returns:
        str: Timestamp formateado (HH:MM:SS,mmm)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def get_model_info(model: str) -> Dict[str, Any]:
    """
    Obtener información sobre un modelo

    Args:
        model: Nombre del modelo

    Returns:
        dict: Información del modelo
    """
    provider = PROVIDER_MAPPING.get(model, 'unknown')
    cost_per_min = MODEL_PRICING.get(model, 0)

    info = {
        'provider': provider,
        'model': model,
        'cost_per_min': cost_per_min,
        'cost_per_hour': cost_per_min * 60,
        'requires_api_key': provider in ['openai', 'groq'],
        'is_free': cost_per_min == 0,
    }

    # Calcular ahorro vs OpenAI
    openai_cost = MODEL_PRICING['whisper-1']
    if cost_per_min > 0 and cost_per_min < openai_cost:
        savings_pct = ((openai_cost - cost_per_min) / openai_cost) * 100
        info['savings_vs_openai'] = savings_pct
    else:
        info['savings_vs_openai'] = 0

    return info


def get_all_models() -> List[Dict[str, Any]]:
    """
    Obtener información de todos los modelos disponibles

    Returns:
        list: Lista de información de modelos
    """
    models_info = []

    for model in MODEL_PRICING.keys():
        info = get_model_info(model)
        models_info.append(info)

    # Ordenar por coste (más barato primero, gratis al final)
    models_info.sort(key=lambda x: (x['cost_per_min'] if x['cost_per_min'] > 0 else float('inf')))

    return models_info
