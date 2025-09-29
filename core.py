"""
Core v3.0 - Soporte multi-proveedor
OpenAI, Groq y Whisper Local
VERSIÓN CORREGIDA
"""

from __future__ import annotations
from pathlib import Path
import shutil
import tempfile
from typing import Optional, Union, List, Dict, Any
import subprocess
import json
import os
import datetime

# Extensiones de audio soportadas
AUDIO_EXT = {'.mp3', '.wav', '.m4a', '.flac', '.opus', '.ogg', '.aac', '.wma'}

# Directorio temporal para chunks y VAD
TEMP_DIR = Path(tempfile.gettempdir()) / "whisper_temp"
TEMP_DIR.mkdir(exist_ok=True)

# Costes por minuto (USD)
MODEL_COSTS = {
    # OpenAI
    'whisper-1': 0.006,
    # Groq (mucho más barato!)
    'groq-whisper-large-v3': 0.00011,
    'groq-distil-whisper-large-v3-en': 0.00002,
    # Local (gratis)
    'local-tiny': 0.0,
    'local-base': 0.0,
    'local-small': 0.0,
    'local-medium': 0.0,
    'local-large': 0.0,
}

# Mapeo de modelos a proveedores
PROVIDER_MAP = {
    'whisper-1': 'openai',
    'groq-whisper-large-v3': 'groq',
    'groq-distil-whisper-large-v3-en': 'groq',
    'local-tiny': 'local',
    'local-base': 'local',
    'local-small': 'local',
    'local-medium': 'local',
    'local-large': 'local',
}

# ============================================================================
# PRESUPUESTO
# ============================================================================

_budget_file = Path.home() / ".whisper4" / "budget.json"
_budget_file.parent.mkdir(parents=True, exist_ok=True)

def budget_get_data() -> dict:
    """Obtener datos de presupuesto"""
    try:
        if not _budget_file.exists():
            return {'limit': 2.0, 'consumed': 0.0, 'date': None}
        with open(_budget_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {'limit': 2.0, 'consumed': 0.0, 'date': None}

def budget_set_limit(limit: float):
    """Establecer límite de presupuesto"""
    try:
        data = budget_get_data()
        data['limit'] = limit
        with open(_budget_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error guardando límite de presupuesto: {e}")

def budget_allow(cost: float) -> bool:
    """Verificar si hay presupuesto disponible"""
    try:
        data = budget_get_data()
        today = datetime.date.today().isoformat()
        if data.get('date') != today:
            data['consumed'] = 0.0
            data['date'] = today
            with open(_budget_file, 'w') as f:
                json.dump(data, f)
        
        return (data['consumed'] + cost) <= data['limit']
    except Exception:
        return True  # En caso de error, permitir

def budget_consume(cost: float):
    """Consumir presupuesto"""
    try:
        data = budget_get_data()
        today = datetime.date.today().isoformat()
        if data.get('date') != today:
            data['consumed'] = 0.0
            data['date'] = today
        data['consumed'] += cost
        with open(_budget_file, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error consumiendo presupuesto: {e}")

def budget_get_remaining() -> float:
    """Obtener presupuesto restante"""
    try:
        data = budget_get_data()
        return max(0, data['limit'] - data['consumed'])
    except Exception:
        return 2.0

# ============================================================================
# UTILIDADES DE AUDIO
# ============================================================================

def probe_duration(audio_path: Path) -> int:
    """Obtener duración del audio en segundos"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding='utf-8', errors='replace',
                              check=True, timeout=30, startupinfo=startupinfo)
        duration_str = result.stdout.strip()
        
        if not duration_str:
            # Intentar método alternativo
            cmd2 = ['ffprobe', '-i', str(audio_path), '-show_entries', 
                   'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
            result2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding='utf-8', errors='replace',
                                   timeout=30, startupinfo=startupinfo)
            duration_str = result2.stdout.strip()
            
        if duration_str:
            return int(float(duration_str))
        else:
            # Asumir 60 segundos como fallback
            return 60
            
    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg no está instalado.\n"
            "Descarga desde: https://ffmpeg.org/download.html\n"
            "Windows: choco install ffmpeg\n"
            "Mac: brew install ffmpeg\n"
            "Linux: sudo apt install ffmpeg"
        )
    except Exception as e:
        print(f"Advertencia: No se pudo obtener duración exacta: {e}")
        return 60  # Asumir 1 minuto como fallback

def estimate_cost(duration_seconds: int, model: str) -> float:
    """Estimar coste de transcripción"""
    minutes = max(1, duration_seconds / 60.0)  # Mínimo 1 minuto
    price_per_min = MODEL_COSTS.get(model, 0.006)
    return minutes * price_per_min

def preprocess_vad_ffmpeg(audio_path: Path) -> Path:
    """Preprocesar audio con VAD para eliminar silencios"""
    output = TEMP_DIR / f"{audio_path.stem}_vad{audio_path.suffix}"
    
    # Limpiar archivos temporales viejos
    for f in TEMP_DIR.glob("*_vad.*"):
        if (datetime.datetime.now() - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days > 1:
            try:
                f.unlink()
            except:
                pass
    
    # Si ya existe y es reciente, devolverla
    if output.exists() and (datetime.datetime.now() - datetime.datetime.fromtimestamp(output.stat().st_mtime)).seconds < 3600:
        return output
    
    try:
        cmd = [
            'ffmpeg', '-i', str(audio_path),
            '-af', 'silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:'
                   'detection=peak,aformat=dblp,areverse,'
                   'silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:'
                   'detection=peak,aformat=dblp,areverse',
            '-y', str(output)
        ]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              encoding='utf-8', errors='replace',
                              check=True, timeout=300, startupinfo=startupinfo)
        return output
    except Exception as e:
        print(f"Advertencia: No se pudo aplicar VAD, usando archivo original: {e}")
        return audio_path  # Devolver original si falla

from concurrent.futures import ThreadPoolExecutor
import threading

def split_for_api(audio_path: Path, bitrate_kbps: int = 64) -> List[Path]:
    """Dividir audio en chunks si es necesario usando procesamiento paralelo"""
    # Limpiar chunks viejos
    for f in TEMP_DIR.glob("*_chunk_*.mp3"):
        if (datetime.datetime.now() - datetime.datetime.fromtimestamp(f.stat().st_mtime)).days > 1:
            try:
                f.unlink()
            except:
                pass
    
    try:
        duration = probe_duration(audio_path)
        if duration <= 0:
            print(f"Advertencia: No se pudo detectar duración válida para {audio_path}")
            return [audio_path]
    except Exception as e:
        print(f"Error detectando duración: {e}")
        return [audio_path]
    
    # Verificar tamaño del archivo
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    # Si es menor a 25MB y 25 minutos, no dividir
    if file_size_mb <= 25 and duration < 1500:
        return [audio_path]
    
    # Directorio para chunks en temp
    chunk_dir = TEMP_DIR / f"chunks_{audio_path.stem}"
    chunk_dir.mkdir(exist_ok=True)
    
    # Ajustar duración del chunk basado en el tamaño y bitrate objetivo
    target_chunk_size = 20  # MB (dejamos margen)
    mb_per_minute = file_size_mb / (duration / 60)
    chunk_duration = min(900, int((target_chunk_size / (bitrate_kbps/64) / mb_per_minute) * 60))
    chunk_duration = max(240, chunk_duration)  # Entre 4 y 15 minutos
    
    overlap = 5  # 5 segundos de solapamiento
    
    # Calcular chunks con solapamiento
    starts = []
    i = 0
    while i * (chunk_duration - overlap) < duration:
        starts.append(i * (chunk_duration - overlap))
        i += 1
    
    def process_chunk(start_idx_pair):
        """Procesar un chunk de audio en paralelo"""
        idx, start = start_idx_pair
        output = chunk_dir / f"chunk_{idx:03d}.mp3"
        
        # Si el chunk ya existe y es válido, usarlo
        if output.exists() and output.stat().st_size > 0:
            chunk_size_mb = output.stat().st_size / (1024 * 1024)
            if chunk_size_mb <= 25:
                with chunks_lock:
                    chunks.append(output)
                return True
            else:
                output.unlink()
        
        # Ajustar duración para el último chunk
        current_duration = min(chunk_duration, duration - start + overlap)
        
        # Configuración optimizada para velocidad
        cmd = [
            'ffmpeg', '-i', str(audio_path),
            '-ss', str(start),
            '-t', str(current_duration),
            '-c:a', 'libmp3lame',  # Usar LAME para mejor compresión
            '-q:a', '7',           # Calidad VBR más baja pero aceptable
            '-ac', '1',            # Mono
            '-ar', '16000',        # 16kHz es suficiente para voz
            '-threads', '0',       # Usar todos los núcleos disponibles
            '-y', str(output)
        ]
        
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 encoding='utf-8', errors='replace',
                                 check=True, timeout=120, startupinfo=startupinfo)
            
            # Verificar el chunk
            if output.exists() and output.stat().st_size > 0:
                chunk_size_mb = output.stat().st_size / (1024 * 1024)
                if chunk_size_mb <= 25:
                    with chunks_lock:
                        chunks.append(output)
                    return True
                else:
                    output.unlink()
        except Exception as e:
            print(f"Error en chunk {idx}: {e}")
            if output.exists():
                output.unlink()
        return False
        
    # Procesar chunks en paralelo
    max_workers = min(os.cpu_count() or 2, 4)  # Limitar a 4 workers máximo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_chunk, enumerate(starts)))
        
    # Si no se pudo crear ningún chunk, intentar comprimir el archivo completo
    if not chunks:
        print("Advertencia: División en chunks falló, intentando comprimir archivo completo...")
        compressed = TEMP_DIR / f"{audio_path.stem}_compressed.mp3"
        try:
            cmd = [
                'ffmpeg', '-i', str(audio_path),
                '-c:a', 'libmp3lame',
                '-q:a', '7',
                '-ac', '1',
                '-ar', '16000',
                '-threads', '0',
                '-y', str(compressed)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         encoding='utf-8', errors='replace',
                         check=True, timeout=300, startupinfo=startupinfo)
            
            if compressed.exists() and compressed.stat().st_size / (1024 * 1024) <= 25:
                return [compressed]
        except Exception as e:
            print(f"Error comprimiendo archivo: {e}")
            if compressed.exists():
                compressed.unlink()
        
        return [audio_path]
    
    # Ordenar chunks por número
    chunks.sort()
    
    return chunks

# ============================================================================
# RESULTADO DE TRANSCRIPCIÓN
# ============================================================================

class TranscriptionResult:
    """Resultado unificado de transcripción"""
    def __init__(self, text: str, segments: list = None, language: str = None):
        self.text = text.strip() if text else ""
        self.segments = segments or []
        self.language = language or 'es'

def write_srt(result: TranscriptionResult) -> str:
    """Convertir resultado a formato SRT"""
    if not result.segments:
        # Si no hay segmentos, crear uno con todo el texto
        return "1\n00:00:00,000 --> 00:00:10,000\n" + result.text + "\n"
    
    lines = []
    for i, seg in enumerate(result.segments, 1):
        start = seg.get('start', 0)
        end = seg.get('end', start + 1)
        text = seg.get('text', '').strip()
        
        if not text:
            continue
        
        start_time = _format_srt_time(start)
        end_time = _format_srt_time(end)
        
        lines.append(str(i))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")
    
    return "\n".join(lines) if lines else ""

def _format_srt_time(seconds: float) -> str:
    """Formatear tiempo para SRT"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ============================================================================
# TRANSCRIPCIÓN - WHISPER LOCAL
# ============================================================================

def transcribe_file_local(audio_path: Path, model_size: str = "base") -> TranscriptionResult:
    """Transcribir usando Whisper local (GRATIS pero lento en CPU)"""
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "Whisper no está instalado.\n"
            "Instala con: pip install openai-whisper\n"
            "Nota: Requiere varios GB de RAM"
        )
    
    # Extraer solo el tamaño del modelo
    if model_size.startswith('local-'):
        model_size = model_size.replace('local-', '')
    
    try:
        print(f"Cargando modelo Whisper {model_size}...")
        model = whisper.load_model(model_size)
        
        print(f"Transcribiendo {audio_path.name}...")
        result = model.transcribe(
            str(audio_path),
            language="es",
            word_timestamps=False,  # Más rápido sin timestamps
            fp16=False,  # Más compatible
            verbose=False
        )
        
        return TranscriptionResult(
            text=result.get('text', '').strip(),
            segments=result.get('segments', []),
            language=result.get('language', 'es')
        )
    except Exception as e:
        raise RuntimeError(f"Error en transcripción local: {e}")

# ============================================================================
# TRANSCRIPCIÓN - GROQ API
# ============================================================================

def transcribe_file_groq(audio_path: Path, model: str = "whisper-large-v3", 
                        api_key: str = None) -> TranscriptionResult:
    """Transcribir usando Groq API (50x más barato que OpenAI)"""
    # Intentar importar groq al inicio
    try:
        import groq
        from groq import Groq
    except ImportError:
        # Intentar instalar el paquete automáticamente
        try:
            import subprocess
            subprocess.check_call(["pip", "install", "groq"])
            import groq
            from groq import Groq
        except Exception as e:
            raise ImportError(
                "Error al instalar/importar el cliente de Groq.\n"
                "Por favor, ejecuta manualmente:\n"
                "1. Activa el entorno virtual: .venv\\Scripts\\activate\n"
                "2. Instala groq: pip install groq --upgrade\n"
                f"Error detallado: {str(e)}"
            )
    
    if api_key is None:
        api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        raise ValueError(
            "API key de Groq no encontrada.\n"
            "1. Obtén una gratis en: https://console.groq.com/keys\n"
            "2. Configúrala en Settings o como variable GROQ_API_KEY"
        )
    
    # Extraer nombre del modelo
    if model.startswith('groq-'):
        model = model.replace('groq-', '')
    
    try:
        client = Groq(api_key=api_key)
        
        # Verificar tamaño del archivo (límite de Groq es 25MB)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(f"Archivo muy grande ({file_size_mb:.1f}MB). Máximo: 25MB")
        
        with open(audio_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                language="es"
            )
        
        # Convertir a nuestro formato
        segments = []
        if hasattr(transcription, 'segments') and transcription.segments:
            for seg in transcription.segments:
                segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })
        
        return TranscriptionResult(
            text=transcription.text if hasattr(transcription, 'text') else str(transcription),
            segments=segments,
            language=getattr(transcription, 'language', 'es')
        )
        
    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower():
            raise ValueError("API key de Groq inválida. Verifica tu configuración.")
        elif 'rate' in error_msg.lower():
            raise ValueError("Límite de rate excedido. Espera un momento e intenta de nuevo.")
        else:
            raise RuntimeError(f"Error con Groq API: {error_msg}")

# ============================================================================
# TRANSCRIPCIÓN - OPENAI API
# ============================================================================

def transcribe_file_openai(audio_path: Path, model: str = "whisper-1",
                          api_key: str = None) -> TranscriptionResult:
    """Transcribir usando OpenAI API"""
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
        client = OpenAI(api_key=api_key)
        
        # Verificar tamaño del archivo (límite de OpenAI es 25MB)
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(f"Archivo muy grande ({file_size_mb:.1f}MB). Máximo: 25MB")
        
        with open(audio_path, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="verbose_json",
                language="es"
            )
            
            # Convertir la respuesta a un diccionario
            if hasattr(transcription, 'model_dump'):
                # Nueva API de OpenAI
                result_dict = transcription.model_dump()
            else:
                # API anterior
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
                        # Si el segmento es un objeto
                        segments.append({
                            'start': getattr(seg, 'start', 0),
                            'end': getattr(seg, 'end', 0),
                            'text': getattr(seg, 'text', '')
                        })
            
            # Extraer el texto principal
            text = result_dict.get('text', '') if isinstance(result_dict, dict) else getattr(transcription, 'text', str(transcription))
            
            return TranscriptionResult(
                text=text,
                segments=segments,
                language='es'
            )
            
            # Convertir la respuesta a un diccionario
            if hasattr(transcription, 'model_dump'):
                # Nueva API de OpenAI
                result_dict = transcription.model_dump()
            else:
                # API anterior
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
                        # Si el segmento es un objeto
                        segments.append({
                            'start': getattr(seg, 'start', 0),
                            'end': getattr(seg, 'end', 0),
                            'text': getattr(seg, 'text', '')
                        })
        
        # Convertir a nuestro formato
        segments = []
        if hasattr(transcription, 'segments') and transcription.segments:
            for seg in transcription.segments:
                segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })
        
        return TranscriptionResult(
            text=transcription.text if hasattr(transcription, 'text') else str(transcription),
            segments=segments,
            language=getattr(transcription, 'language', 'es')
        )
        
    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            raise ValueError("API key de OpenAI inválida. Verifica tu configuración.")
        elif 'rate' in error_msg.lower() or 'quota' in error_msg.lower():
            raise ValueError("Límite de cuota o rate excedido.")
        else:
            raise RuntimeError(f"Error con OpenAI API: {error_msg}")

# ============================================================================
# FUNCIÓN UNIFICADA DE TRANSCRIPCIÓN
# ============================================================================

def transcribe_file(audio_path: Path, model: str = "groq-whisper-large-v3", 
                   api_key: str = None) -> TranscriptionResult:
    """
    Transcribir archivo usando el proveedor apropiado según el modelo
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {audio_path}")
    
    provider = PROVIDER_MAP.get(model, 'groq')
    
    # Verificar tamaño y pre-procesar si es necesario
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25 and provider != 'local':
        print(f"Archivo de {file_size_mb:.1f}MB - Dividiendo en chunks...")
        # Comprimir el audio si es muy grande
        compressed_path = audio_path.parent / f"{audio_path.stem}_compressed{audio_path.suffix}"
        if not compressed_path.exists():
            try:
                subprocess.run([
                    'ffmpeg', '-i', str(audio_path),
                    '-ab', '64k',  # Reducir bitrate
                    '-y', str(compressed_path)
                ], check=True, capture_output=True)
                audio_path = compressed_path
            except Exception as e:
                print(f"No se pudo comprimir: {e}")
    
    chunk_duration = 1200  # 20 minutos
    overlap = 5  # 5 segundos de solapamiento
    
    try:
        if provider == 'local':
            return transcribe_file_local(audio_path, model)
        
        # Dividir en chunks si es necesario
        chunks = split_for_api(audio_path)
        
        # Si después de dividir solo hay un chunk y es muy grande, intentar comprimir más
        if len(chunks) == 1 and chunks[0].stat().st_size / (1024 * 1024) > 25:
            try:
                compressed_chunk = chunks[0].parent / f"{chunks[0].stem}_compressed{chunks[0].suffix}"
                subprocess.run([
                    'ffmpeg', '-i', str(chunks[0]),
                    '-ab', '32k',  # Bitrate más bajo para forzar tamaño menor
                    '-ac', '1',    # Convertir a mono
                    '-y', str(compressed_chunk)
                ], check=True, capture_output=True)
                chunks = [compressed_chunk]
            except Exception as e:
                print(f"Error comprimiendo chunk: {e}")
                raise ValueError(f"No se pudo reducir el tamaño del archivo a menos de 25MB")
        
        if len(chunks) == 1:
            if provider == 'groq':
                return transcribe_file_groq(chunks[0], model, api_key)
            else:
                return transcribe_file_openai(chunks[0], model, api_key)
        
        # Procesar múltiples chunks
        all_text = []
        all_segments = []
        overlap_threshold = 2.0  # Umbral para detectar duplicados en solapamiento
        
        for i, chunk in enumerate(chunks):
            print(f"Procesando chunk {i+1} de {len(chunks)}...")
            # Transcribir chunk
            if provider == 'groq':
                result = transcribe_file_groq(chunk, model, api_key)
            else:
                result = transcribe_file_openai(chunk, model, api_key)
            
            # Ajustar tiempos para segmentos
            offset = i * (chunk_duration - overlap)
            
            # Filtrar segmentos duplicados en zona de solapamiento
            if i > 0 and result.segments:
                # Ignorar segmentos en primeros 2 segundos si no es primer chunk
                result.segments = [s for s in result.segments if s['start'] >= overlap_threshold]
            
            # Ajustar tiempos
            for seg in result.segments:
                seg['start'] += offset
                seg['end'] += offset
            
            # Agregar al resultado
            text = result.text.strip()
            if text:  # Solo agregar si hay texto
                if all_text and not text.startswith('.') and not text.startswith('!') and not text.startswith('?'):
                    all_text.append(' ' + text)
                else:
                    all_text.append(text)
            
            all_segments.extend(result.segments)
        
        # Ordenar segmentos por tiempo
        all_segments.sort(key=lambda x: x['start'])
        
        return TranscriptionResult(
            text=''.join(all_text),
            segments=all_segments,
            language='es'
        )
            
    except Exception as e:
        # Re-lanzar con contexto adicional
        raise RuntimeError(f"Error transcribiendo con {provider}: {str(e)}")

# ============================================================================
# INFORMACIÓN DE PROVEEDORES
# ============================================================================

def get_provider_info(model: str) -> Dict[str, Any]:
    """Obtener información sobre un proveedor/modelo"""
    provider = PROVIDER_MAP.get(model, 'unknown')
    cost_per_min = MODEL_COSTS.get(model, 0)
    
    info = {
        'provider': provider,
        'model': model,
        'cost_per_min': cost_per_min,
        'cost_per_hour': cost_per_min * 60,
        'requires_api_key': provider in ['openai', 'groq'],
        'is_free': cost_per_min == 0,
    }
    
    # Calcular ahorro vs OpenAI
    openai_cost = MODEL_COSTS['whisper-1']
    if cost_per_min > 0 and cost_per_min < openai_cost:
        savings_pct = ((openai_cost - cost_per_min) / openai_cost) * 100
        info['savings_vs_openai'] = savings_pct
    else:
        info['savings_vs_openai'] = 0
    
    return info

def get_all_models_info() -> List[Dict[str, Any]]:
    """Obtener información de todos los modelos disponibles"""
    models_info = []
    
    for model in MODEL_COSTS.keys():
        info = get_provider_info(model)
        models_info.append(info)
    
    # Ordenar por coste (más barato primero, gratis al final)
    models_info.sort(key=lambda x: (x['cost_per_min'] if x['cost_per_min'] > 0 else float('inf')))
    
    return models_info
