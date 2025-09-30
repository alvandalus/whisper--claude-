"""
Módulo de gestión de historial de transcripciones
Sistema completo para guardar, cargar y gestionar transcripciones anteriores
"""

import json
import datetime as dt
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Archivo de historial
HISTORY_FILE = Path.home() / ".transcriptor_pro" / "history.json"
HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


class TranscriptionHistory:
    """Gestor de historial de transcripciones"""

    def __init__(self):
        """Inicializar gestor de historial"""
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Asegurar que el archivo de historial existe"""
        if not HISTORY_FILE.exists():
            self._save_data([])

    def _load_data(self) -> List[Dict]:
        """
        Cargar historial desde disco

        Returns:
            list: Lista de registros de transcripciones
        """
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Historial cargado: {len(data)} registros")
                return data
        except Exception as e:
            logger.error(f"Error cargando historial: {e}")
            return []

    def _save_data(self, data: List[Dict]) -> None:
        """
        Guardar historial a disco

        Args:
            data: Lista de registros a guardar
        """
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Historial guardado: {len(data)} registros")
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")

    def add_transcription(self, record: Dict) -> str:
        """
        Agregar una transcripción al historial

        Args:
            record: Diccionario con datos de la transcripción
                - original_file: Ruta al archivo original
                - model: Modelo usado
                - duration: Duración en segundos
                - cost: Coste de la transcripción
                - language: Idioma detectado
                - output_path: Ruta al archivo de salida
                - text_preview: Vista previa del texto (opcional)
                - has_srt: Si tiene archivo SRT

        Returns:
            str: ID único de la transcripción
        """
        import uuid

        data = self._load_data()

        # Crear registro
        new_record = {
            'id': str(uuid.uuid4()),
            'timestamp': dt.datetime.now().timestamp(),
            'date': dt.datetime.now().isoformat(),
            **record
        }

        # Agregar vista previa si no existe
        if 'text_preview' not in new_record and 'text' in record:
            text = record['text']
            new_record['text_preview'] = text[:200] + '...' if len(text) > 200 else text

        data.append(new_record)
        self._save_data(data)

        logger.info(f"Transcripción agregada al historial: {new_record['id']}")
        return new_record['id']

    def get_all(self, sort_by: str = 'date', reverse: bool = True) -> List[Dict]:
        """
        Obtener todas las transcripciones

        Args:
            sort_by: Campo por el cual ordenar ('date', 'cost', 'duration')
            reverse: Orden descendente (más reciente primero)

        Returns:
            list: Lista de transcripciones ordenadas
        """
        data = self._load_data()

        # Ordenar
        if sort_by == 'date':
            data.sort(key=lambda x: x.get('timestamp', 0), reverse=reverse)
        elif sort_by == 'cost':
            data.sort(key=lambda x: x.get('cost', 0), reverse=reverse)
        elif sort_by == 'duration':
            data.sort(key=lambda x: x.get('duration', 0), reverse=reverse)

        return data

    def get_by_id(self, transcription_id: str) -> Optional[Dict]:
        """
        Obtener transcripción por ID

        Args:
            transcription_id: ID de la transcripción

        Returns:
            dict: Registro de transcripción o None
        """
        data = self._load_data()
        for record in data:
            if record.get('id') == transcription_id:
                return record
        return None

    def search(self, query: str, fields: List[str] = None) -> List[Dict]:
        """
        Buscar transcripciones

        Args:
            query: Texto a buscar
            fields: Campos donde buscar (default: ['original_file', 'text_preview', 'model'])

        Returns:
            list: Transcripciones que coinciden con la búsqueda
        """
        if fields is None:
            fields = ['original_file', 'text_preview', 'model', 'language']

        data = self._load_data()
        query_lower = query.lower()

        results = []
        for record in data:
            for field in fields:
                value = str(record.get(field, '')).lower()
                if query_lower in value:
                    results.append(record)
                    break

        logger.debug(f"Búsqueda '{query}': {len(results)} resultados")
        return results

    def filter_by_date(self, start_date: dt.datetime = None,
                      end_date: dt.datetime = None) -> List[Dict]:
        """
        Filtrar transcripciones por rango de fechas

        Args:
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)

        Returns:
            list: Transcripciones en el rango
        """
        data = self._load_data()
        results = []

        for record in data:
            timestamp = record.get('timestamp', 0)
            record_date = dt.datetime.fromtimestamp(timestamp)

            if start_date and record_date < start_date:
                continue
            if end_date and record_date > end_date:
                continue

            results.append(record)

        return results

    def filter_by_model(self, model: str) -> List[Dict]:
        """
        Filtrar transcripciones por modelo

        Args:
            model: Nombre del modelo

        Returns:
            list: Transcripciones con ese modelo
        """
        data = self._load_data()
        return [r for r in data if r.get('model') == model]

    def delete(self, transcription_id: str) -> bool:
        """
        Eliminar transcripción del historial

        Args:
            transcription_id: ID de la transcripción

        Returns:
            bool: True si se eliminó correctamente
        """
        data = self._load_data()
        original_len = len(data)

        data = [r for r in data if r.get('id') != transcription_id]

        if len(data) < original_len:
            self._save_data(data)
            logger.info(f"Transcripción eliminada: {transcription_id}")
            return True

        return False

    def clear_all(self) -> int:
        """
        Limpiar todo el historial

        Returns:
            int: Cantidad de registros eliminados
        """
        data = self._load_data()
        count = len(data)
        self._save_data([])
        logger.info(f"Historial limpiado: {count} registros eliminados")
        return count

    def get_statistics(self) -> Dict:
        """
        Obtener estadísticas del historial

        Returns:
            dict: Estadísticas generales
        """
        data = self._load_data()

        if not data:
            return {
                'total_transcriptions': 0,
                'total_duration': 0,
                'total_cost': 0,
                'average_cost': 0,
                'models_used': {},
                'languages_detected': {},
                'first_transcription': None,
                'last_transcription': None
            }

        # Calcular estadísticas
        total_duration = sum(r.get('duration', 0) for r in data)
        total_cost = sum(r.get('cost', 0) for r in data)

        # Contar modelos
        models = {}
        for r in data:
            model = r.get('model', 'unknown')
            models[model] = models.get(model, 0) + 1

        # Contar idiomas
        languages = {}
        for r in data:
            lang = r.get('language', 'unknown')
            languages[lang] = languages.get(lang, 0) + 1

        # Fechas
        timestamps = [r.get('timestamp', 0) for r in data if r.get('timestamp')]
        first_date = dt.datetime.fromtimestamp(min(timestamps)).isoformat() if timestamps else None
        last_date = dt.datetime.fromtimestamp(max(timestamps)).isoformat() if timestamps else None

        return {
            'total_transcriptions': len(data),
            'total_duration': total_duration,
            'total_duration_hours': total_duration / 3600,
            'total_cost': total_cost,
            'average_cost': total_cost / len(data),
            'models_used': models,
            'languages_detected': languages,
            'first_transcription': first_date,
            'last_transcription': last_date
        }

    def export_to_csv(self, output_path: Path) -> bool:
        """
        Exportar historial a CSV

        Args:
            output_path: Ruta del archivo CSV de salida

        Returns:
            bool: True si se exportó correctamente
        """
        import csv

        try:
            data = self._load_data()

            if not data:
                return False

            # Obtener todas las claves únicas
            all_keys = set()
            for record in data:
                all_keys.update(record.keys())

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(data)

            logger.info(f"Historial exportado a: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exportando historial: {e}")
            return False


# Instancia global (singleton)
_history_manager: Optional[TranscriptionHistory] = None


def get_history_manager() -> TranscriptionHistory:
    """
    Obtener instancia del gestor de historial (singleton)

    Returns:
        TranscriptionHistory: Instancia del gestor
    """
    global _history_manager
    if _history_manager is None:
        _history_manager = TranscriptionHistory()
    return _history_manager
