from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk
import datetime as dt
from pathlib import Path
import os
import json

@dataclass
class TranscriptionRecord:
    """Registro de una transcripción"""
    id: str
    date: float
    original_file: str
    text: str
    segments: list
    language: str

class HistoryTab:
    """Pestaña de historial"""
    def __init__(self, app):
        self.app = app
        self.history_file = Path(app.config.output_dir).parent / "history.json"
        self._build_history_tab()
    
    def _build_history_tab(self):
        """Construir pestaña de historial"""
        # Frame principal con scroll
        main_frame = ttk.Frame(self.app.tab_history)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas y scrollbar para scroll vertical
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Título
        ttk.Label(scrollable_frame, text="📋 Historial de Transcripciones", 
                 font=("Segoe UI", 12, "bold")).pack(pady=10)
        
        try:
            # Cargar historial desde archivo
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            else:
                records = []
            
            # Lista de transcripciones
            for record in sorted(records, key=lambda x: x['date'], reverse=True):
                # Frame para cada registro
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill="x", padx=5, pady=5)
                
                # Fecha y archivo original
                date_str = dt.datetime.fromtimestamp(record['date']).strftime("%Y-%m-%d %H:%M")
                filename = Path(record['original_file']).name if record['original_file'] else 'Archivo desconocido'
                
                ttk.Label(frame, text=f"🕒 {date_str}", font=("Segoe UI", 9)).pack(anchor="w")
                ttk.Label(frame, text=f"📄 {filename}", font=("Segoe UI", 9, "bold")).pack(anchor="w")
                
                # Información adicional
                info_text = f"🌐 Idioma: {record.get('language', 'Desconocido')}"
                if 'model' in record:
                    info_text += f" · 🤖 Modelo: {record['model']}"
                if 'duration' in record:
                    info_text += f" · ⏱️ Duración: {record['duration']:.1f}s"
                ttk.Label(frame, text=info_text, font=("Segoe UI", 9)).pack(anchor="w")
                
                # Botones de acción
                btn_frame = ttk.Frame(frame)
                btn_frame.pack(fill="x", pady=5)
                
                def make_view_cmd(text, segments):
                    def cmd():
                        self._show_full_transcript(text, segments)
                    return cmd
                
                ttk.Button(btn_frame, text="🔍 Ver completo",
                          command=make_view_cmd(record['text'], record['segments'])).pack(side="left", padx=2)
                
                if record['original_file'] and Path(record['original_file']).exists():
                    def make_open_cmd(path):
                        return lambda: os.startfile(path)
                    
                    ttk.Button(btn_frame, text="🎵 Abrir audio",
                             command=make_open_cmd(record['original_file'])).pack(side="left", padx=2)
                
                ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=10)
        
        except Exception as e:
            ttk.Label(scrollable_frame, 
                     text=f"Error cargando historial: {e}",
                     font=("Segoe UI", 9)).pack(pady=10)

        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Botón para actualizar
        ttk.Button(main_frame, text="🔄 Actualizar",
                  command=self._refresh_history).pack(pady=10)

    def _show_full_transcript(self, text, segments):
        """Mostrar transcripción completa en una ventana nueva"""
        window = tk.Toplevel(self.app)
        window.title("Transcripción Completa")
        window.geometry("800x600")
        
        # Frame con scroll
        frame = ttk.Frame(window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap="word", font=("Segoe UI", 10))
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Insertar texto completo
        text_widget.insert("1.0", text)
        
        # Agregar marcas de tiempo si hay segmentos
        if segments:
            text_widget.insert("1.0", "Segmentos con marcas de tiempo:\n\n")
            for seg in segments:
                timestamp = f"[{seg['start']:.1f}s - {seg['end']:.1f}s]\n"
                text_widget.insert("end", timestamp + seg['text'] + "\n\n")
        
        text_widget.configure(state="disabled")
        
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _refresh_history(self):
        """Actualizar vista del historial"""
        for widget in self.app.tab_history.winfo_children():
            widget.destroy()
        self._build_history_tab()