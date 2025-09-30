"""
Módulo de utilidades de audio
Manejo de FFmpeg, VAD, división de chunks y procesamiento de audio
"""

import os
import subprocess
import datetime as dt
import tempfile
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor
import threading
import logging

logger = logging.getLogger(__name__)

# Extensiones de audio soportadas
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.opus', '.ogg', '.aac', '.wma'}

# Directorio temporal
TEMP_DIR = Path(tempfile.gettempdir()) / "transcriptor_temp"
TEMP_DIR.mkdir(exist_ok=True)


def get_audio_duration(audio_path: Path) -> int:
    """
    Obtener duración del audio en segundos usando FFprobe

    Args:
        audio_path: Ruta al archivo de audio

    Returns:
        int: Duración en segundos

    Raises:
        RuntimeError: Si FFmpeg no está instalado
    """
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

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=30,
            startupinfo=startupinfo
        )

        duration_str = result.stdout.strip()

        if not duration_str:
            # Método alternativo
            cmd2 = [
                'ffprobe', '-i', str(audio_path),
                '-show_entries', 'format=duration',
                '-v', 'quiet', '-of', 'csv=p=0'
            ]
            result2 = subprocess.run(
                cmd2,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                timeout=30,
                startupinfo=startupinfo
            )
            duration_str = result2.stdout.strip()

        if duration_str:
            duration = int(float(duration_str))
            logger.debug(f"Duración de {audio_path.name}: {duration}s")
            return duration
        else:
            logger.warning(f"No se pudo obtener duración, usando 60s por defecto")
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
        logger.warning(f"Error obteniendo duración: {e}, usando 60s por defecto")
        return 60


def apply_vad_preprocessing(audio_path: Path) -> Path:
    """
    Aplicar Voice Activity Detection para eliminar silencios

    Args:
        audio_path: Ruta al archivo de audio original

    Returns:
        Path: Ruta al archivo procesado con VAD

    Note:
        Si el procesamiento falla, retorna el archivo original
    """
    output = TEMP_DIR / f"{audio_path.stem}_vad{audio_path.suffix}"

    # Limpiar archivos VAD antiguos (más de 1 día)
    _cleanup_old_files(TEMP_DIR, "*_vad.*", days=1)

    # Si ya existe y es reciente (menos de 1 hora), reutilizar
    if output.exists():
        age = dt.datetime.now() - dt.datetime.fromtimestamp(output.stat().st_mtime)
        if age.seconds < 3600:
            logger.debug(f"Reutilizando archivo VAD existente: {output.name}")
            return output

    try:
        logger.info(f"Aplicando VAD a: {audio_path.name}")

        cmd = [
            'ffmpeg', '-i', str(audio_path),
            '-af',
            'silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:'
            'detection=peak,aformat=dblp,areverse,'
            'silenceremove=start_periods=1:start_duration=1:start_threshold=-50dB:'
            'detection=peak,aformat=dblp,areverse',
            '-y', str(output)
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=300,
            startupinfo=startupinfo
        )

        logger.info(f"VAD aplicado exitosamente: {output.name}")
        return output

    except Exception as e:
        logger.warning(f"No se pudo aplicar VAD: {e}, usando archivo original")
        return audio_path


def split_audio_for_api(audio_path: Path, bitrate_kbps: int = 64,
                        max_size_mb: int = 25) -> List[Path]:
    """
    Dividir audio en chunks si excede el tamaño máximo

    Args:
        audio_path: Ruta al archivo de audio
        bitrate_kbps: Bitrate objetivo en kbps
        max_size_mb: Tamaño máximo por chunk en MB

    Returns:
        List[Path]: Lista de rutas a los chunks (o archivo original si no necesita división)
    """
    # Limpiar chunks antiguos
    _cleanup_old_files(TEMP_DIR, "*_chunk_*.mp3", days=1)

    try:
        duration = get_audio_duration(audio_path)
        if duration <= 0:
            logger.warning("Duración inválida, retornando archivo original")
            return [audio_path]
    except Exception as e:
        logger.error(f"Error detectando duración: {e}")
        return [audio_path]

    file_size_mb = audio_path.stat().st_size / (1024 * 1024)

    # Si es menor al límite y menor a 25 minutos, no dividir
    if file_size_mb <= max_size_mb and duration < 1500:
        logger.debug(f"Archivo no requiere división: {file_size_mb:.1f}MB, {duration}s")
        return [audio_path]

    logger.info(f"Dividiendo archivo: {file_size_mb:.1f}MB, {duration}s")

    # Crear directorio para chunks
    chunk_dir = TEMP_DIR / f"chunks_{audio_path.stem}"
    chunk_dir.mkdir(exist_ok=True)

    # Calcular duración óptima del chunk
    target_chunk_size = 20  # MB (con margen)
    mb_per_minute = file_size_mb / (duration / 60)
    chunk_duration = min(900, int((target_chunk_size / (bitrate_kbps/64) / mb_per_minute) * 60))
    chunk_duration = max(240, chunk_duration)  # Entre 4 y 15 minutos

    overlap = 5  # Segundos de solapamiento

    # Calcular puntos de inicio de chunks
    starts = []
    i = 0
    while i * (chunk_duration - overlap) < duration:
        starts.append(i * (chunk_duration - overlap))
        i += 1

    logger.info(f"Dividiendo en {len(starts)} chunks de ~{chunk_duration}s")

    # Lista thread-safe para chunks
    chunks = []
    chunks_lock = threading.Lock()

    def process_chunk(start_idx_pair):
        """Procesar un chunk individual"""
        idx, start = start_idx_pair
        output = chunk_dir / f"chunk_{idx:03d}.mp3"

        # Verificar si el chunk ya existe y es válido
        if output.exists() and output.stat().st_size > 0:
            chunk_size_mb = output.stat().st_size / (1024 * 1024)
            if chunk_size_mb <= max_size_mb:
                with chunks_lock:
                    chunks.append(output)
                logger.debug(f"Reutilizando chunk {idx}: {output.name}")
                return True
            else:
                output.unlink()

        # Calcular duración del chunk
        current_duration = min(chunk_duration, duration - start + overlap)

        cmd = [
            'ffmpeg', '-i', str(audio_path),
            '-ss', str(start),
            '-t', str(current_duration),
            '-c:a', 'libmp3lame',
            '-q:a', '7',  # Calidad VBR
            '-ac', '1',   # Mono
            '-ar', '16000',  # 16kHz
            '-threads', '0',
            '-y', str(output)
        ]

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',
                errors='replace',
                check=True,
                timeout=120,
                startupinfo=startupinfo
            )

            if output.exists() and output.stat().st_size > 0:
                chunk_size_mb = output.stat().st_size / (1024 * 1024)
                if chunk_size_mb <= max_size_mb:
                    with chunks_lock:
                        chunks.append(output)
                    logger.debug(f"Chunk {idx} creado: {chunk_size_mb:.1f}MB")
                    return True
                else:
                    logger.warning(f"Chunk {idx} muy grande: {chunk_size_mb:.1f}MB")
                    output.unlink()
        except Exception as e:
            logger.error(f"Error en chunk {idx}: {e}")
            if output.exists():
                output.unlink()
        return False

    # Procesar chunks en paralelo
    max_workers = min(os.cpu_count() or 2, 4)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_chunk, enumerate(starts)))

    # Si no se pudo crear ningún chunk, intentar comprimir el archivo completo
    if not chunks:
        logger.warning("División falló, intentando comprimir archivo completo...")
        compressed = _compress_audio_file(audio_path, max_size_mb)
        if compressed:
            return [compressed]
        return [audio_path]

    # Ordenar chunks
    chunks.sort()
    logger.info(f"División completada: {len(chunks)} chunks")
    return chunks


def _compress_audio_file(audio_path: Path, max_size_mb: int = 25) -> Path:
    """
    Comprimir archivo de audio para reducir tamaño

    Args:
        audio_path: Ruta al archivo original
        max_size_mb: Tamaño máximo objetivo

    Returns:
        Path: Ruta al archivo comprimido, o None si falló
    """
    compressed = TEMP_DIR / f"{audio_path.stem}_compressed.mp3"

    try:
        logger.info(f"Comprimiendo {audio_path.name}...")

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

        subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace',
            check=True,
            timeout=300,
            startupinfo=startupinfo
        )

        if compressed.exists():
            size_mb = compressed.stat().st_size / (1024 * 1024)
            if size_mb <= max_size_mb:
                logger.info(f"Compresión exitosa: {size_mb:.1f}MB")
                return compressed
            else:
                logger.warning(f"Compresión insuficiente: {size_mb:.1f}MB")
                compressed.unlink()

    except Exception as e:
        logger.error(f"Error comprimiendo archivo: {e}")
        if compressed.exists():
            compressed.unlink()

    return None


def _cleanup_old_files(directory: Path, pattern: str, days: int = 1) -> None:
    """
    Limpiar archivos antiguos del directorio temporal

    Args:
        directory: Directorio a limpiar
        pattern: Patrón glob de archivos
        days: Antigüedad en días
    """
    try:
        for file in directory.glob(pattern):
            age = dt.datetime.now() - dt.datetime.fromtimestamp(file.stat().st_mtime)
            if age.days >= days:
                try:
                    file.unlink()
                    logger.debug(f"Archivo temporal eliminado: {file.name}")
                except Exception:
                    pass
    except Exception as e:
        logger.debug(f"Error limpiando archivos temporales: {e}")


def cleanup_temp_directory() -> None:
    """Limpiar todo el directorio temporal"""
    try:
        for file in TEMP_DIR.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    import shutil
                    shutil.rmtree(file)
            except Exception:
                pass
        logger.info("Directorio temporal limpiado")
    except Exception as e:
        logger.error(f"Error limpiando directorio temporal: {e}")


def validate_audio_file(audio_path: Path) -> tuple[bool, str]:
    """
    Validar que un archivo de audio es válido

    Args:
        audio_path: Ruta al archivo

    Returns:
        tuple: (es_válido, mensaje_error)
    """
    # Verificar existencia
    if not audio_path.exists():
        return False, "El archivo no existe"

    # Verificar extensión
    if audio_path.suffix.lower() not in AUDIO_EXTENSIONS:
        return False, f"Formato no soportado: {audio_path.suffix}"

    # Verificar tamaño
    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb == 0:
        return False, "El archivo está vacío"

    # Verificar duración con FFprobe
    try:
        duration = get_audio_duration(audio_path)
        if duration <= 0:
            return False, "No se pudo determinar la duración del audio"
    except Exception as e:
        return False, f"Error validando audio: {str(e)}"

    return True, ""
