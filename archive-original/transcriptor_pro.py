"""
Transcriptor Pro v1.0 - Multi-Provider Audio Transcription Tool
Sistema profesional de transcripción con soporte para OpenAI, Groq y Whisper Local
"""

from __future__ import annotations
import os
import sys
import tkinter as tk
import uuid
import time
import json
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import datetime as dt
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Dict, Any, Union
import subprocess
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# CONSTANTES Y CONFIGURACIÓN GLOBAL
# ============================================================================

AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.opus', '.ogg', '.aac', '.wma'}
TEMP_DIRECTORY = Path(tempfile.gettempdir()) / "transcriptor_temp"
TEMP_DIRECTORY.mkdir(exist_ok=True)

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

# Directorio de configuración
APP_ROOT = Path(os.getenv("APPDATA", Path.home())) / ".transcriptor_pro"
TRANSCRIPTS_DIR = APP_ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = APP_ROOT / "config.json"
BUDGET_PATH = APP_ROOT / "budget.json"
HISTORY_PATH = APP_ROOT / "history.json"

# ============================================================================
# GESTIÓN DE PRESUPUESTO
# ============================================================================

def load_budget_data() -> dict:
    """Cargar datos de presupuesto"""
    try:
        if not BUDGET_PATH.exists():
            return {'limit': 2.0, 'consumed': 0.0, 'date': None}
        with open(BUDGET_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return {'limit': 2.0, 'consumed': 0.0, 'date': None}

def save_budget_limit(limit: float):
    """Establecer límite de presupuesto"""
    try:
        data = load_budget_data()
        data['limit'] = limit
        with open(BUDGET_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error guardando límite de presupuesto: {e}")

def check_budget_available(cost: float) -> bool:
    """Verificar si hay presupuesto disponible"""
    try:
        data = load_budget_data()
        today = dt.date.today().isoformat()
        if data.get('date') != today:
            data['consumed'] = 0.0
            data['date'] = today
            with open(BUDGET_PATH, 'w') as f:
                json.dump(data, f)

        return (data['consumed'] + cost) <= data['limit']
    except Exception:
        return True

def consume_budget(cost: float):
    """Consumir presupuesto"""
    try:
        data = load_budget_data()
        today = dt.date.today().isoformat()
        if data.get('date') != today:
            data['consumed'] = 0.0
            data['date'] = today
        data['consumed'] += cost
        with open(BUDGET_PATH, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error consumiendo presupuesto: {e}")

def get_remaining_budget() -> float:
    """Obtener presupuesto restante"""
    try:
        data = load_budget_data()
        return max(0, data['limit'] - data['consumed'])
    except Exception:
        return 2.0

# ============================================================================
# UTILIDADES DE AUDIO
# ============================================================================

def get_audio_duration(audio_path: Path) -> int:
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
            cmd2 = ['ffprobe', '-i', str(audio_path), '-show_entries',
                   'format=duration', '-v', 'quiet', '-of', 'csv=p=0']
            result2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding='utf-8', errors='replace',
                                   timeout=30, startupinfo=startupinfo)
            duration_str = result2.stdout.strip()

        if duration_str:
            return int(float(duration_str))
        else:
            return 60

    except FileNotFoundError:
        raise RuntimeError(
            "FFmpeg no está instalado.\n"
            "Descarga desde: https://ffmpeg.org/download.html"
        )
    except Exception as e:
        print(f"Advertencia: No se pudo obtener duración exacta: {e}")
        return 60

def calculate_cost(duration_seconds: int, model: str) -> float:
    """Calcular coste de transcripción"""
    minutes = max(1, duration_seconds / 60.0)
    price_per_min = MODEL_PRICING.get(model, 0.006)
    return minutes * price_per_min

def apply_vad_preprocessing(audio_path: Path) -> Path:
    """Preprocesar audio con VAD para eliminar silencios"""
    output = TEMP_DIRECTORY / f"{audio_path.stem}_vad{audio_path.suffix}"

    # Limpiar archivos VAD viejos
    for f in TEMP_DIRECTORY.glob("*_vad.*"):
        age = dt.datetime.now() - dt.datetime.fromtimestamp(f.stat().st_mtime)
        if age.days > 1:
            try:
                f.unlink()
            except:
                pass

    # Si ya existe y es reciente, devolverla
    if output.exists():
        age = dt.datetime.now() - dt.datetime.fromtimestamp(output.stat().st_mtime)
        if age.seconds < 3600:
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

        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      encoding='utf-8', errors='replace',
                      check=True, timeout=300, startupinfo=startupinfo)
        return output
    except Exception as e:
        print(f"Advertencia: No se pudo aplicar VAD: {e}")
        return audio_path

def split_audio_for_api(audio_path: Path, bitrate_kbps: int = 64) -> List[Path]:
    """Dividir audio en chunks si es necesario"""
    # Limpiar chunks viejos
    for f in TEMP_DIRECTORY.glob("*_chunk_*.mp3"):
        age = dt.datetime.now() - dt.datetime.fromtimestamp(f.stat().st_mtime)
        if age.days > 1:
            try:
                f.unlink()
            except:
                pass

    try:
        duration = get_audio_duration(audio_path)
        if duration <= 0:
            return [audio_path]
    except Exception:
        return [audio_path]

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    # Si es menor a 25MB y 25 minutos, no dividir
    if file_size_mb <= 25 and duration < 1500:
        return [audio_path]

    # Directorio para chunks
    chunk_dir = TEMP_DIRECTORY / f"chunks_{audio_path.stem}"
    chunk_dir.mkdir(exist_ok=True)

    # Calcular duración del chunk
    target_chunk_size = 20
    mb_per_minute = file_size_mb / (duration / 60)
    chunk_duration = min(900, int((target_chunk_size / (bitrate_kbps/64) / mb_per_minute) * 60))
    chunk_duration = max(240, chunk_duration)

    overlap = 5

    # Calcular chunks con solapamiento
    starts = []
    i = 0
    while i * (chunk_duration - overlap) < duration:
        starts.append(i * (chunk_duration - overlap))
        i += 1

    chunks = []
    chunks_lock = threading.Lock()

    def process_chunk(start_idx_pair):
        idx, start = start_idx_pair
        output = chunk_dir / f"chunk_{idx:03d}.mp3"

        if output.exists() and output.stat().st_size > 0:
            chunk_size_mb = output.stat().st_size / (1024 * 1024)
            if chunk_size_mb <= 25:
                with chunks_lock:
                    chunks.append(output)
                return True
            else:
                output.unlink()

        current_duration = min(chunk_duration, duration - start + overlap)

        cmd = [
            'ffmpeg', '-i', str(audio_path),
            '-ss', str(start),
            '-t', str(current_duration),
            '-c:a', 'libmp3lame',
            '-q:a', '7',
            '-ac', '1',
            '-ar', '16000',
            '-threads', '0',
            '-y', str(output)
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         encoding='utf-8', errors='replace',
                         check=True, timeout=120, startupinfo=startupinfo)

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
    max_workers = min(os.cpu_count() or 2, 4)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_chunk, enumerate(starts)))

    if not chunks:
        compressed = TEMP_DIRECTORY / f"{audio_path.stem}_compressed.mp3"
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
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
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

    chunks.sort()
    return chunks

# ============================================================================
# RESULTADO DE TRANSCRIPCIÓN
# ============================================================================

class TranscriptionOutput:
    """Resultado de transcripción"""
    def __init__(self, text: str, segments: list = None, language: str = None):
        self.text = text.strip() if text else ""
        self.segments = segments or []
        self.language = language or 'es'

def generate_srt(result: TranscriptionOutput) -> str:
    """Convertir resultado a formato SRT"""
    if not result.segments:
        return "1\n00:00:00,000 --> 00:00:10,000\n" + result.text + "\n"

    lines = []
    for i, seg in enumerate(result.segments, 1):
        start = seg.get('start', 0)
        end = seg.get('end', start + 1)
        text = seg.get('text', '').strip()

        if not text:
            continue

        start_time = format_timestamp(start)
        end_time = format_timestamp(end)

        lines.append(str(i))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")

    return "\n".join(lines) if lines else ""

def format_timestamp(seconds: float) -> str:
    """Formatear tiempo para SRT"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# ============================================================================
# TRANSCRIPCIÓN - GROQ API
# ============================================================================

def transcribe_with_groq(audio_path: Path, model: str = "whisper-large-v3",
                        api_key: str = None) -> TranscriptionOutput:
    """Transcribir usando Groq API"""
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
            "Configúrala en Settings"
        )

    if model.startswith('groq-'):
        model = model.replace('groq-', '')

    try:
        client = Groq(api_key=api_key)

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

        segments = []
        if hasattr(transcription, 'segments') and transcription.segments:
            for seg in transcription.segments:
                segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'text': seg.get('text', '')
                })

        return TranscriptionOutput(
            text=transcription.text if hasattr(transcription, 'text') else str(transcription),
            segments=segments,
            language=getattr(transcription, 'language', 'es')
        )

    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower():
            raise ValueError("API key de Groq inválida")
        elif 'rate' in error_msg.lower():
            raise ValueError("Límite de rate excedido")
        else:
            raise RuntimeError(f"Error con Groq API: {error_msg}")

# ============================================================================
# TRANSCRIPCIÓN - OPENAI API
# ============================================================================

def transcribe_with_openai(audio_path: Path, model: str = "whisper-1",
                          api_key: str = None) -> TranscriptionOutput:
    """Transcribir usando OpenAI API"""
    if api_key is None:
        api_key = os.getenv('OPENAI_API_KEY')

    if not api_key:
        raise ValueError(
            "API key de OpenAI no encontrada.\n"
            "Configúrala en Settings"
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

            if hasattr(transcription, 'model_dump'):
                result_dict = transcription.model_dump()
            else:
                result_dict = transcription if isinstance(transcription, dict) else transcription.__dict__

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

            return TranscriptionOutput(
                text=text,
                segments=segments,
                language='es'
            )

    except Exception as e:
        error_msg = str(e)
        if 'api_key' in error_msg.lower() or 'unauthorized' in error_msg.lower():
            raise ValueError("API key de OpenAI inválida")
        elif 'rate' in error_msg.lower() or 'quota' in error_msg.lower():
            raise ValueError("Límite de cuota excedido")
        else:
            raise RuntimeError(f"Error con OpenAI API: {error_msg}")

# ============================================================================
# TRANSCRIPCIÓN - WHISPER LOCAL
# ============================================================================

def transcribe_with_local(audio_path: Path, model_size: str = "base") -> TranscriptionOutput:
    """Transcribir usando Whisper local"""
    try:
        import whisper
    except ImportError:
        raise ImportError(
            "Whisper no está instalado.\n"
            "Instala con: pip install openai-whisper"
        )

    if model_size.startswith('local-'):
        model_size = model_size.replace('local-', '')

    try:
        print(f"Cargando modelo Whisper {model_size}...")
        model = whisper.load_model(model_size)

        print(f"Transcribiendo {audio_path.name}...")
        result = model.transcribe(
            str(audio_path),
            language="es",
            word_timestamps=False,
            fp16=False,
            verbose=False
        )

        return TranscriptionOutput(
            text=result.get('text', '').strip(),
            segments=result.get('segments', []),
            language=result.get('language', 'es')
        )
    except Exception as e:
        raise RuntimeError(f"Error en transcripción local: {e}")

# ============================================================================
# FUNCIÓN UNIFICADA DE TRANSCRIPCIÓN
# ============================================================================

def transcribe_audio(audio_path: Path, model: str = "groq-whisper-large-v3",
                   api_key: str = None) -> TranscriptionOutput:
    """Transcribir archivo usando el proveedor apropiado"""
    if not audio_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {audio_path}")

    provider = PROVIDER_MAPPING.get(model, 'groq')

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 25 and provider != 'local':
        print(f"Archivo de {file_size_mb:.1f}MB - Dividiendo en chunks...")

    try:
        if provider == 'local':
            return transcribe_with_local(audio_path, model)

        chunks = split_audio_for_api(audio_path)

        if len(chunks) == 1:
            if provider == 'groq':
                return transcribe_with_groq(chunks[0], model, api_key)
            else:
                return transcribe_with_openai(chunks[0], model, api_key)

        # Procesar múltiples chunks
        all_text = []
        all_segments = []
        chunk_duration = 1200
        overlap = 5
        overlap_threshold = 2.0

        for i, chunk in enumerate(chunks):
            print(f"Procesando chunk {i+1} de {len(chunks)}...")

            if provider == 'groq':
                result = transcribe_with_groq(chunk, model, api_key)
            else:
                result = transcribe_with_openai(chunk, model, api_key)

            offset = i * (chunk_duration - overlap)

            if i > 0 and result.segments:
                result.segments = [s for s in result.segments if s['start'] >= overlap_threshold]

            for seg in result.segments:
                seg['start'] += offset
                seg['end'] += offset

            text = result.text.strip()
            if text:
                if all_text and not text.startswith('.') and not text.startswith('!') and not text.startswith('?'):
                    all_text.append(' ' + text)
                else:
                    all_text.append(text)

            all_segments.extend(result.segments)

        all_segments.sort(key=lambda x: x['start'])

        return TranscriptionOutput(
            text=''.join(all_text),
            segments=all_segments,
            language='es'
        )

    except Exception as e:
        raise RuntimeError(f"Error transcribiendo con {provider}: {str(e)}")

# ============================================================================
# INFORMACIÓN DE PROVEEDORES
# ============================================================================

def get_model_info(model: str) -> Dict[str, Any]:
    """Obtener información sobre un modelo"""
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

    openai_cost = MODEL_PRICING['whisper-1']
    if cost_per_min > 0 and cost_per_min < openai_cost:
        savings_pct = ((openai_cost - cost_per_min) / openai_cost) * 100
        info['savings_vs_openai'] = savings_pct
    else:
        info['savings_vs_openai'] = 0

    return info

def get_all_models() -> List[Dict[str, Any]]:
    """Obtener información de todos los modelos"""
    models_info = []

    for model in MODEL_PRICING.keys():
        info = get_model_info(model)
        models_info.append(info)

    models_info.sort(key=lambda x: (x['cost_per_min'] if x['cost_per_min'] > 0 else float('inf')))

    return models_info

# ============================================================================
# CONFIGURACIÓN DE APLICACIÓN
# ============================================================================

@dataclass
class ApplicationConfig:
    """Configuración de la aplicación"""
    model: str = "groq-whisper-large-v3"
    openai_api_key: str = ""
    groq_api_key: str = ""
    bitrate: int = 192
    use_vad: bool = False
    export_srt: bool = True
    output_dir: str = str(TRANSCRIPTS_DIR)
    history: list[dict] = field(default_factory=list)
    daily_budget: float = 2.0
    inbox_dir: str = str(Path.home() / "TranscriptorPro" / "INBOX")

    def save(self):
        """Guardar configuración"""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            config_data = asdict(self)

            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            print(f"✓ Configuración guardada en: {CONFIG_PATH}")

        except Exception as e:
            print(f"✗ Error guardando configuración: {e}")
            raise

    @classmethod
    def load(cls) -> ApplicationConfig:
        """Cargar configuración"""
        try:
            if CONFIG_PATH.exists():
                print(f"✓ Cargando configuración desde: {CONFIG_PATH}")
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    valid_fields = {k: v for k, v in data.items()
                                  if k in cls.__dataclass_fields__}

                    print(f"✓ Configuración cargada: {len(valid_fields)} campos")
                    return cls(**valid_fields)
            else:
                print(f"⚠ No existe config, usando valores por defecto")
        except Exception as e:
            print(f"⚠ Error cargando configuración: {e}")

        print("✓ Usando configuración por defecto")
        return cls()

# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

class TranscriptorProApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transcriptor Pro v1.0 – Multi-Provider Edition 🎙️")
        self.geometry("1100x750")
        self.minsize(900, 600)

        self.config = ApplicationConfig.load()
        self.audio: Optional[Path] = None

        self._build_interface()
        self.after(100, self._apply_configuration)
        self.after(1000, self._show_welcome_tip)

    def _build_interface(self):
        """Construir interfaz de usuario"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Pestañas
        self.single_tab = ttk.Frame(notebook)
        notebook.add(self.single_tab, text="📄 Archivo único")

        self.batch_tab = ttk.Frame(notebook)
        notebook.add(self.batch_tab, text="📁 Procesamiento por lotes")

        self.history_tab = ttk.Frame(notebook)
        notebook.add(self.history_tab, text="📋 Historial")

        self.config_tab = ttk.Frame(notebook)
        notebook.add(self.config_tab, text="⚙️ Configuración")

        self.comparison_tab = ttk.Frame(notebook)
        notebook.add(self.comparison_tab, text="💰 Comparador")

        self._build_single_file_tab()
        self._build_batch_processing_tab()
        self._build_history_tab()
        self._build_configuration_tab()
        self._build_comparison_tab()

        # Barra de estado
        status_text = "Listo"
        if self.config.groq_api_key:
            status_text += " · Groq configurado"
        elif self.config.openai_api_key:
            status_text += " · OpenAI configurado"

        self.status_bar = ttk.Label(self, text=status_text,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_single_file_tab(self):
        """Construir pestaña de archivo único"""
        top = ttk.Frame(self.single_tab, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="📂 Abrir archivo",
                  command=self._select_file).pack(side="left", padx=2)

        self.filename_label = ttk.Label(top, text="(sin archivo)",
                                     font=("Segoe UI", 9, "italic"))
        self.filename_label.pack(side="left", padx=10)

        self.file_info_label = ttk.Label(top, text="", foreground="blue")
        self.file_info_label.pack(side="left", padx=10)

        self.transcribe_button = ttk.Button(top, text="▶️ Transcribir",
                  command=self._execute_single_transcription,
                  style="Accent.TButton")
        self.transcribe_button.pack(side="right", padx=2)

        # Área de resultado
        body = ttk.Frame(self.single_tab, padding=10)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text="Transcripción:",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")

        text_frame = ttk.Frame(body)
        text_frame.pack(fill="both", expand=True, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.result_text = tk.Text(text_frame, wrap="word",
                                 font=("Segoe UI", 10),
                                 yscrollcommand=scrollbar.set)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.result_text.yview)

        # Botones de acción
        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill="x", pady=5)

        ttk.Button(btn_frame, text="💾 Guardar",
                  command=self._save_transcription).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Copiar",
                  command=self._copy_to_clipboard).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Limpiar",
                  command=lambda: self.result_text.delete("1.0", tk.END)).pack(side="left", padx=2)

    def _build_batch_processing_tab(self):
        """Construir pestaña de procesamiento por lotes"""
        top = ttk.Frame(self.batch_tab, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="📥 INBOX:",
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=2)
        self.inbox_var = tk.StringVar(value=self.config.inbox_dir)
        ttk.Entry(top, textvariable=self.inbox_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="...", width=3,
                  command=lambda: self._select_directory(self.inbox_var)).grid(row=0, column=2)

        ttk.Label(top, text="📤 OUT:",
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=2)
        self.output_var = tk.StringVar(value=self.config.output_dir)
        ttk.Entry(top, textvariable=self.output_var, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(top, text="...", width=3,
                  command=lambda: self._select_directory(self.output_var)).grid(row=1, column=2)

        btn_frame = ttk.Frame(self.batch_tab, padding=10)
        btn_frame.pack(fill="x")

        self.batch_button = ttk.Button(btn_frame, text="▶️ Procesar carpeta",
                  command=self._execute_batch_processing)
        self.batch_button.pack(side="left", padx=2)

        # Progreso
        self.batch_progress = ttk.Progressbar(self.batch_tab, mode='determinate')
        self.batch_progress.pack(fill="x", padx=10, pady=5)

        # Log
        log_frame = ttk.Frame(self.batch_tab, padding=10)
        log_frame.pack(fill="both", expand=True)

        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")

        self.batch_log = tk.Text(log_frame, wrap="word",
                               font=("Consolas", 9),
                               yscrollcommand=log_scroll.set)
        self.batch_log.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.batch_log.yview)

    def _build_history_tab(self):
        """Construir pestaña de historial"""
        frame = ttk.Frame(self.history_tab, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="📋 Historial de Transcripciones",
                 font=("Segoe UI", 14, "bold")).pack(pady=10)

        ttk.Label(frame, text="Funcionalidad de historial disponible próximamente",
                 font=("Segoe UI", 10)).pack(pady=20)

    def _build_configuration_tab(self):
        """Construir pestaña de configuración"""
        canvas = tk.Canvas(self.config_tab)
        scrollbar = ttk.Scrollbar(self.config_tab, orient="vertical", command=canvas.yview)

        frame = ttk.Frame(canvas, padding=20)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Proveedor y modelo
        section1 = ttk.LabelFrame(frame, text="🤖 Proveedor y Modelo", padding=15)
        section1.pack(fill="x", pady=10)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(section1, text="Modelo:").grid(row=0, column=0, sticky="w", pady=5)

        self.model_var = tk.StringVar(value=self.config.model)

        model_options = list(MODEL_PRICING.keys())
        self.model_combo = ttk.Combobox(section1, textvariable=self.model_var,
                                       values=model_options, width=35, state="readonly")
        self.model_combo.grid(row=0, column=1, sticky="w", pady=5)
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_selected)

        self.model_info_label = ttk.Label(section1, text="", foreground="blue")
        self.model_info_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        # API Keys
        section2 = ttk.LabelFrame(frame, text="🔑 API Keys", padding=15)
        section2.pack(fill="x", pady=10)

        ttk.Label(section2, text="OpenAI API Key:").grid(row=0, column=0, sticky="w", pady=5)
        self.openai_key_var = tk.StringVar(value=self.config.openai_api_key)
        openai_entry = ttk.Entry(section2, textvariable=self.openai_key_var, width=50, show="*")
        openai_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        ttk.Button(section2, text="👁️", width=3,
                  command=lambda: self._toggle_visibility(openai_entry)).grid(row=0, column=2)

        ttk.Label(section2, text="Groq API Key:").grid(row=1, column=0, sticky="w", pady=5)
        self.groq_key_var = tk.StringVar(value=self.config.groq_api_key)
        groq_entry = ttk.Entry(section2, textvariable=self.groq_key_var, width=50, show="*")
        groq_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        ttk.Button(section2, text="👁️", width=3,
                  command=lambda: self._toggle_visibility(groq_entry)).grid(row=1, column=2)

        ttk.Button(section2, text="💾 GUARDAR CONFIGURACIÓN",
                  command=self._save_configuration,
                  style="Accent.TButton").grid(row=2, column=0, columnspan=3, pady=15, sticky="ew")

        # Opciones
        section3 = ttk.LabelFrame(frame, text="🎛️ Opciones de Procesamiento", padding=15)
        section3.pack(fill="x", pady=10)

        ttk.Label(section3, text="Bitrate (kbps):").grid(row=0, column=0, sticky="w", pady=5)
        self.bitrate_var = tk.IntVar(value=self.config.bitrate)
        ttk.Spinbox(section3, from_=64, to=320, increment=16,
                   textvariable=self.bitrate_var, width=10).grid(row=0, column=1, sticky="w", pady=5)

        self.vad_var = tk.BooleanVar(value=self.config.use_vad)
        ttk.Checkbutton(section3, text="VAD (recortar silencios) ⚠️ Consume CPU",
                       variable=self.vad_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        self.srt_var = tk.BooleanVar(value=self.config.export_srt)
        ttk.Checkbutton(section3, text="Exportar subtítulos (SRT)",
                       variable=self.srt_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        # Presupuesto
        section4 = ttk.LabelFrame(frame, text="💰 Control de Presupuesto", padding=15)
        section4.pack(fill="x", pady=10)

        ttk.Label(section4, text="Límite diario (USD):").grid(row=0, column=0, sticky="w", pady=5)
        self.budget_var = tk.DoubleVar(value=self.config.daily_budget)
        ttk.Entry(section4, textvariable=self.budget_var, width=15).grid(row=0, column=1,
                                                                         sticky="w", pady=5)

        self.budget_status_label = ttk.Label(section4, text="")
        self.budget_status_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        self._update_model_info()
        self._update_budget_display()

    def _build_comparison_tab(self):
        """Construir pestaña de comparación"""
        frame = ttk.Frame(self.comparison_tab, padding=20)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="💰 Comparador de Costes entre Proveedores",
                         font=("Segoe UI", 14, "bold"))
        title.pack(pady=10)

        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=10)

        ttk.Label(input_frame, text="Duración del audio (minutos):").pack(side="left", padx=5)
        self.duration_var = tk.IntVar(value=60)
        ttk.Spinbox(input_frame, from_=1, to=600, textvariable=self.duration_var,
                   width=10).pack(side="left", padx=5)
        ttk.Button(input_frame, text="🔄 Calcular",
                  command=self._update_cost_comparison).pack(side="left", padx=5)

        columns = ("Modelo", "Proveedor", "Coste", "Ahorro vs OpenAI", "API Key")
        self.comparison_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)

        for col in columns:
            self.comparison_tree.heading(col, text=col)

        self.comparison_tree.column("Modelo", width=250)
        self.comparison_tree.column("Proveedor", width=100)
        self.comparison_tree.column("Coste", width=100)
        self.comparison_tree.column("Ahorro vs OpenAI", width=150)
        self.comparison_tree.column("API Key", width=100)

        scrollbar = ttk.Scrollbar(frame, orient="vertical",
                                 command=self.comparison_tree.yview)
        self.comparison_tree.configure(yscrollcommand=scrollbar.set)

        self.comparison_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        summary_frame = ttk.LabelFrame(frame, text="📊 Resumen", padding=15)
        summary_frame.pack(fill="x", pady=10)

        self.cheapest_label = ttk.Label(summary_frame, text="", font=("Segoe UI", 10))
        self.cheapest_label.pack(anchor="w", pady=2)

        self.savings_label = ttk.Label(summary_frame, text="", font=("Segoe UI", 10))
        self.savings_label.pack(anchor="w", pady=2)

        self._update_cost_comparison()

    # ========================================================================
    # MÉTODOS DE LÓGICA
    # ========================================================================

    def _apply_configuration(self):
        """Aplicar configuración cargada"""
        if hasattr(self, 'model_var'):
            self.model_var.set(self.config.model)
        if hasattr(self, 'openai_key_var'):
            self.openai_key_var.set(self.config.openai_api_key)
        if hasattr(self, 'groq_key_var'):
            self.groq_key_var.set(self.config.groq_api_key)
        if hasattr(self, 'bitrate_var'):
            self.bitrate_var.set(self.config.bitrate)
        if hasattr(self, 'vad_var'):
            self.vad_var.set(self.config.use_vad)
        if hasattr(self, 'srt_var'):
            self.srt_var.set(self.config.export_srt)
        if hasattr(self, 'budget_var'):
            self.budget_var.set(self.config.daily_budget)
        if hasattr(self, 'inbox_var'):
            self.inbox_var.set(self.config.inbox_dir)
        if hasattr(self, 'output_var'):
            self.output_var.set(self.config.output_dir)

        if self.config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.groq_api_key:
            os.environ['GROQ_API_KEY'] = self.config.groq_api_key

    def _sync_config_from_ui(self):
        """Sincronizar configuración desde UI"""
        self.config.model = self.model_var.get()
        self.config.openai_api_key = self.openai_key_var.get()
        self.config.groq_api_key = self.groq_key_var.get()
        self.config.bitrate = int(self.bitrate_var.get())
        self.config.use_vad = self.vad_var.get()
        self.config.export_srt = self.srt_var.get()
        self.config.daily_budget = float(self.budget_var.get())
        self.config.inbox_dir = self.inbox_var.get()
        self.config.output_dir = self.output_var.get()

        if self.config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.groq_api_key:
            os.environ['GROQ_API_KEY'] = self.config.groq_api_key

    def _save_configuration(self):
        """Guardar configuración"""
        try:
            self._sync_config_from_ui()

            if not self.config.model.startswith('local'):
                if not self.config.openai_api_key and not self.config.groq_api_key:
                    messagebox.showwarning(
                        "Advertencia",
                        "No has configurado ninguna API key.\n"
                        "Necesitas al menos una para transcribir."
                    )

            self.config.save()
            save_budget_limit(self.config.daily_budget)

            status_text = "Configuración guardada"
            if self.config.groq_api_key:
                status_text += " · Groq configurado ✓"
            if self.config.openai_api_key:
                status_text += " · OpenAI configurado ✓"
            self.status_bar.config(text=status_text)

            details = "✅ Configuración guardada correctamente\n\n"
            details += f"Modelo: {self.config.model}\n"
            if self.config.groq_api_key:
                details += f"Groq API: Configurada\n"
            if self.config.openai_api_key:
                details += f"OpenAI API: Configurada\n"
            details += f"Presupuesto: ${self.config.daily_budget}/día\n"

            messagebox.showinfo("Éxito", details)
            self._update_budget_display()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _on_model_selected(self, event=None):
        """Cuando cambia el modelo"""
        self._update_model_info()

    def _update_model_info(self):
        """Actualizar información del modelo"""
        model = self.model_var.get()
        info = get_model_info(model)

        cost_hour = info['cost_per_hour']
        provider = info['provider'].upper()

        text = f"💰 ${cost_hour:.4f}/hora"

        if info['is_free']:
            text += " · 🎉 GRATIS"
        elif info['savings_vs_openai'] > 0:
            text += f" · 📉 {info['savings_vs_openai']:.1f}% ahorro"

        text += f" · 🔧 {provider}"

        if info['requires_api_key']:
            text += " (requiere API key)"

        self.model_info_label.config(text=text)

    def _update_budget_display(self):
        """Actualizar visualización de presupuesto"""
        remaining = get_remaining_budget()
        limit = self.config.daily_budget
        consumed = limit - remaining

        pct = (consumed / limit * 100) if limit > 0 else 0

        text = f"Gastado hoy: ${consumed:.2f} de ${limit:.2f} ({pct:.1f}%)"

        if remaining <= 0:
            text += " ⚠️ LÍMITE ALCANZADO"
            color = "red"
        elif pct > 75:
            text += " ⚠️"
            color = "orange"
        else:
            text += " ✓"
            color = "green"

        self.budget_status_label.config(text=text, foreground=color)

    def _toggle_visibility(self, entry: ttk.Entry):
        """Mostrar/ocultar contraseña"""
        if entry.cget('show') == '*':
            entry.config(show='')
        else:
            entry.config(show='*')

    def _show_welcome_tip(self):
        """Mostrar tip de bienvenida"""
        if self.config.groq_api_key:
            return

        if self.config.model.startswith('groq'):
            return

        if self.config.model.startswith('openai') or self.config.model == 'whisper-1':
            messagebox.showinfo(
                "💡 Bienvenido a Transcriptor Pro",
                "Transcriptor Pro es una herramienta profesional de transcripción.\n\n"
                "Soporta múltiples proveedores:\n"
                "• Groq (recomendado, 98% más barato)\n"
                "• OpenAI (calidad premium)\n"
                "• Whisper Local (gratis, lento)\n\n"
                "Configura tu API key en la pestaña Configuración."
            )

    def _update_cost_comparison(self):
        """Actualizar comparación de costes"""
        duration_min = self.duration_var.get()

        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)

        models_info = get_all_models()

        cheapest_cost = float('inf')
        cheapest_model = ""
        openai_cost = 0

        for info in models_info:
            cost = info['cost_per_min'] * duration_min
            savings = info['savings_vs_openai']

            if info['model'] == 'whisper-1':
                openai_cost = cost

            if cost < cheapest_cost and cost > 0:
                cheapest_cost = cost
                cheapest_model = info['model']

            needs_key = "✓ Sí" if info['requires_api_key'] else "No (local)"

            if info['is_free']:
                savings_text = "GRATIS 🎉"
            elif savings > 0:
                savings_text = f"{savings:.1f}% 📉"
            else:
                savings_text = "Referencia"

            self.comparison_tree.insert("", "end", values=(
                info['model'],
                info['provider'].upper(),
                f"${cost:.4f}",
                savings_text,
                needs_key
            ))

        if openai_cost > 0 and cheapest_cost < float('inf'):
            savings_amount = openai_cost - cheapest_cost
            savings_pct = (savings_amount / openai_cost * 100)

            self.cheapest_label.config(
                text=f"🏆 Más barato: {cheapest_model} (${cheapest_cost:.4f})"
            )
            self.savings_label.config(
                text=f"💰 Ahorrarías: ${savings_amount:.4f} ({savings_pct:.1f}%) vs OpenAI"
            )

    # ========================================================================
    # ARCHIVO ÚNICO
    # ========================================================================

    def _select_file(self):
        """Seleccionar archivo de audio"""
        ext_str = " ".join(f"*{ext}" for ext in AUDIO_EXTENSIONS)

        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[("Audio", ext_str), ("Todos", "*.*")]
        )

        if not file_path:
            return

        self.audio = Path(file_path)
        self.filename_label.config(text=self.audio.name)

        try:
            duration_sec = get_audio_duration(self.audio)
            cost = calculate_cost(duration_sec, self.config.model)

            minutes = duration_sec // 60
            seconds = duration_sec % 60

            provider = PROVIDER_MAPPING.get(self.config.model, '?').upper()
            info = f"⏱️ {minutes}:{seconds:02d} | 💰 ${cost:.4f} | 🤖 {provider}"
            self.file_info_label.config(text=info)
            self.status_bar.config(text=f"Archivo cargado: {self.audio.name}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")

    def _execute_single_transcription(self):
        """Ejecutar transcripción de archivo único"""
        if not self.audio:
            messagebox.showwarning("Sin archivo", "Selecciona un archivo primero")
            return

        self.transcribe_button.configure(state="disabled")
        self._sync_config_from_ui()
        threading.Thread(target=self._worker_single_transcription, daemon=True).start()

    def _worker_single_transcription(self):
        """Worker para transcripción única"""
        try:
            src = self.audio

            if self.config.use_vad:
                file_size_mb = self.audio.stat().st_size / (1024 * 1024)

                if file_size_mb > 10:
                    response = messagebox.askyesno(
                        "⚠️ Advertencia VAD",
                        f"El archivo pesa {file_size_mb:.1f} MB.\n\n"
                        "VAD puede tardar mucho y consumir CPU.\n\n"
                        "¿Continuar con VAD?",
                        icon='warning'
                    )

                    if not response:
                        self.after(0, lambda: messagebox.showinfo(
                            "Cancelado", "Transcripción cancelada"))
                        return

                self.after(0, lambda: self.status_bar.config(text="Aplicando VAD..."))
                src = apply_vad_preprocessing(self.audio)

            self.after(0, lambda: self.status_bar.config(text="Transcribiendo..."))

            duration = get_audio_duration(src)
            cost = calculate_cost(duration, self.config.model)

            if not check_budget_available(cost):
                self.after(0, lambda: messagebox.showwarning(
                    "Presupuesto", f"Sin presupuesto para ${cost:.4f}"))
                return

            result = transcribe_audio(src, model=self.config.model)

            # Guardar archivos
            timestamp = dt.datetime.now().timestamp()
            transcriptions_dir = Path(self.config.output_dir)
            transcriptions_dir.mkdir(exist_ok=True, parents=True)

            out_base = transcriptions_dir / f"{self.audio.stem}_{int(timestamp)}"
            out_txt = out_base.with_suffix(".txt")
            out_txt.write_text(result.text, encoding="utf-8")

            has_srt = False
            if self.config.export_srt:
                out_srt = out_base.with_suffix(".srt")
                out_srt.write_text(generate_srt(result), encoding="utf-8")
                has_srt = True

            self.after(0, lambda: self.result_text.delete("1.0", tk.END))
            self.after(0, lambda: self.result_text.insert("1.0", result.text))

            consume_budget(cost)

            msg = f"✅ Transcripción completada\n\n"
            msg += f"📄 {out_txt}\n"
            msg += f"💰 Coste: ${cost:.4f}\n"
            msg += f"🤖 {PROVIDER_MAPPING.get(self.config.model, '?').upper()}"

            self.after(0, lambda: messagebox.showinfo("Éxito", msg))
            self.after(0, self._update_budget_display)

        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
        finally:
            self.after(0, lambda: self.transcribe_button.configure(state="normal"))

    # ========================================================================
    # PROCESAMIENTO POR LOTES
    # ========================================================================

    def _select_directory(self, var: tk.StringVar):
        """Seleccionar directorio"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def _execute_batch_processing(self):
        """Ejecutar procesamiento por lotes"""
        self._sync_config_from_ui()
        self.batch_log.delete("1.0", tk.END)
        self.batch_button.configure(state="disabled")
        threading.Thread(target=self._worker_batch_processing, daemon=True).start()

    def _worker_batch_processing(self):
        """Worker para procesamiento por lotes"""
        inbox = Path(self.inbox_var.get())
        outdir = Path(self.output_var.get())
        outdir.mkdir(parents=True, exist_ok=True)

        files = [f for f in sorted(inbox.glob("*")) if f.suffix.lower() in AUDIO_EXTENSIONS]
        total_files = len(files)

        self._add_to_log(f"📁 Encontrados {total_files} archivos")

        successful = 0
        failed = 0
        total_cost = 0.0

        for i, p in enumerate(files, 1):
            try:
                self._add_to_log(f"[{i}/{total_files}] {p.name}...")
                self.after(0, lambda v=(i/total_files)*100: self.batch_progress.config(value=v))

                src = apply_vad_preprocessing(p) if self.config.use_vad else p

                duration = get_audio_duration(src)
                cost = calculate_cost(duration, self.config.model)

                if not check_budget_available(cost):
                    self._add_to_log(f"  ⚠️ SKIP: sin presupuesto (${cost:.4f})")
                    failed += 1
                    continue

                result = transcribe_audio(src, model=self.config.model)

                base = outdir / p.stem
                (base.with_suffix(".txt")).write_text(result.text, encoding="utf-8")
                if self.config.export_srt:
                    (base.with_suffix(".srt")).write_text(generate_srt(result), encoding="utf-8")

                consume_budget(cost)
                total_cost += cost
                successful += 1

                self._add_to_log(f"  ✅ OK (${cost:.4f})")

            except Exception as e:
                self._add_to_log(f"  ❌ ERROR: {e}")
                failed += 1

        self._add_to_log(f"\n{'='*50}")
        self._add_to_log(f"✅ Completado: {successful}/{total_files}")
        self._add_to_log(f"❌ Fallidos: {failed}")
        self._add_to_log(f"💰 Coste total: ${total_cost:.4f}")

        self.after(0, lambda: self.batch_progress.config(value=0))
        self.after(0, self._update_budget_display)
        self.after(0, lambda: self.batch_button.configure(state="normal"))

    def _add_to_log(self, msg: str):
        """Añadir mensaje al log"""
        self.after(0, lambda: self.batch_log.insert(tk.END, msg + "\n"))
        self.after(0, lambda: self.batch_log.see(tk.END))

    # ========================================================================
    # UTILIDADES
    # ========================================================================

    def _save_transcription(self):
        """Guardar transcripción"""
        text = self.result_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin contenido", "No hay texto para guardar")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Subtítulos", "*.srt"), ("Todos", "*.*")]
        )

        if file_path:
            try:
                Path(file_path).write_text(text, encoding='utf-8')
                messagebox.showinfo("Guardado", f"✅ Guardado en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def _copy_to_clipboard(self):
        """Copiar al portapapeles"""
        text = self.result_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin contenido", "No hay texto para copiar")
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_bar.config(text="✓ Copiado al portapapeles")
        self.after(2000, lambda: self.status_bar.config(text="Listo"))

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    try:
        app = TranscriptorProApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error Fatal",
            f"Error crítico:\n{e}\n\n"
            f"Revisa el log en: {APP_ROOT}")

if __name__ == "__main__":
    main()
