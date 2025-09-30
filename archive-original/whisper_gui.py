"""
Whisper GUI v3.0 - Multi-Provider Edition
Soporta: OpenAI, Groq y Whisper Local
"""

from __future__ import annotations
import os
import tkinter as tk
import uuid
import time
import json
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import datetime as dt
import json
from dataclasses import dataclass, asdict, field
from typing import Optional

# Importar core
from core import (
    AUDIO_EXT, split_for_api, transcribe_file, write_srt,
    preprocess_vad_ffmpeg, estimate_cost, budget_set_limit,
    budget_allow, budget_consume, probe_duration, MODEL_COSTS,
    budget_get_remaining, get_provider_info, get_all_models_info,
    PROVIDER_MAP
)

ROOT = Path(os.getenv("APPDATA", Path.home())) / ".whisper4"
DIR_TXT = ROOT / "transcripts"
DIR_TXT.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = ROOT / "config.json"

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

@dataclass
class AppConfig:
    """Configuración de la aplicación v3"""
    # Modelo y proveedor
    model: str = "groq-whisper-large-v3"  # Por defecto el más barato
    
    # API Keys
    openai_api_key: str = ""
    groq_api_key: str = ""
    
    # Opciones de procesamiento
    bitrate: int = 192
    use_vad: bool = False  # DESACTIVADO por defecto (consume mucha CPU)
    export_srt: bool = True
    output_dir: str = str(DIR_TXT)  # Directorio de salida personalizable
    
    # Historial
    history: list[dict] = field(default_factory=list)  # Lista de registros de transcripción
    
    # Presupuesto
    daily_budget: float = 2.0
    
    # Directorios
    inbox_dir: str = str(Path.home() / "IAAudio" / "INBOX")
    output_dir: str = str(Path.home() / "IAAudio" / "OUT")
    
    def save(self):
        """Guardar configuración"""
        try:
            # Asegurar que el directorio existe
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar con formato bonito
            config_data = asdict(self)
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Configuración guardada en: {CONFIG_FILE}")
            
        except Exception as e:
            print(f"✗ Error guardando configuración: {e}")
            raise
    
    @classmethod
    def load(cls) -> AppConfig:
        """Cargar configuración"""
        try:
            if CONFIG_FILE.exists():
                print(f"✓ Cargando configuración desde: {CONFIG_FILE}")
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Filtrar solo campos válidos
                    valid_fields = {k: v for k, v in data.items() 
                                  if k in cls.__dataclass_fields__}
                    
                    print(f"✓ Configuración cargada: {len(valid_fields)} campos")
                    if 'groq_api_key' in valid_fields and valid_fields['groq_api_key']:
                        print(f"  - Groq API key: {len(valid_fields['groq_api_key'])} caracteres")
                    if 'openai_api_key' in valid_fields and valid_fields['openai_api_key']:
                        print(f"  - OpenAI API key: {len(valid_fields['openai_api_key'])} caracteres")
                    
                    # Migrar historial existente si no existe aún
                    app_path = CONFIG_FILE.parent
                    history_path = app_path / "history"
                    if not (app_path / "history.json").exists():
                        print("Migrando transcripciones existentes al historial...")
                        if history_path.exists() and history_path.is_dir():
                            history_records = []
                            try:
                                for json_file in history_path.glob("*.json"):
                                    with open(json_file, 'r', encoding='utf-8') as f:
                                        transcript = json.load(f)
                                        # Crear registro del historial
                                        record = {
                                            "id": json_file.stem,  # Usar nombre del archivo como ID
                                            "date": json_file.stat().st_mtime,  # Fecha de modificación
                                            "original_file": transcript.get("audio_file", ""),
                                            "text": transcript.get("text", ""),
                                            "segments": transcript.get("segments", []),
                                            "language": transcript.get("language", "")
                                        }
                                        history_records.append(record)
                                
                                # Guardar historial
                                if history_records:
                                    with open(app_path / "history.json", 'w', encoding='utf-8') as f:
                                        json.dump(history_records, f, ensure_ascii=False, indent=2)
                                        print(f"✓ Se migraron {len(history_records)} transcripciones al historial")
                            except Exception as e:
                                print(f"✗ Error migrando transcripciones: {e}")
                                # Continuar aunque haya error
                    
                    return cls(**valid_fields)
            else:
                print(f"⚠ No existe config en {CONFIG_FILE}, usando valores por defecto")
        except Exception as e:
            print(f"⚠ Error cargando configuración: {e}")
        
        print("✓ Usando configuración por defecto")
        return cls()

# ============================================================================
# APLICACIÓN PRINCIPAL
# ============================================================================

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IA Audio v3.0 – Multi-Provider Edition 🚀")
        self.geometry("1100x750")
        self.minsize(900, 600)
        
        self.config = AppConfig.load()
        self.audio: Optional[Path] = None
        
        self._build_ui()
        
        # Aplicar config DESPUÉS de crear todos los widgets
        self.after(100, self._apply_config_to_ui)
        
        # Mostrar info de ahorro solo si es primera vez o usa OpenAI
        self.after(1000, self._show_savings_tip)
    
    def _build_ui(self):
        """Construir interfaz"""
        # Notebook
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tabs
        self.tab_single = ttk.Frame(nb)
        nb.add(self.tab_single, text="📄 Archivo único")
        
        self.tab_batch = ttk.Frame(nb)
        nb.add(self.tab_batch, text="📁 Procesamiento por lotes")
        
        self.tab_history = ttk.Frame(nb)
        nb.add(self.tab_history, text="📋 Historial")
        
        self.tab_config = ttk.Frame(nb)
        nb.add(self.tab_config, text="⚙️ Configuración")
        
        self.tab_compare = ttk.Frame(nb)
        nb.add(self.tab_compare, text="💰 Comparador de Costes")
        
        self._build_single_tab()
        self._build_batch_tab()
        self._build_config_tab()
        self._build_compare_tab()
        
        # Crear pestaña de historial
        from history_tab import HistoryTab
        self.history_tab = HistoryTab(self)
        
        # Barra de estado
        status_text = "Listo"
        if self.config.groq_api_key:
            status_text += " · Groq configurado (98% ahorro vs OpenAI)"
        elif self.config.openai_api_key:
            status_text += " · OpenAI configurado"
        
        self.status_bar = ttk.Label(self, text=status_text, 
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _build_single_tab(self):
        """Tab de archivo único"""
        # Frame superior
        top = ttk.Frame(self.tab_single, padding=10)
        top.pack(fill="x")
        
        ttk.Button(top, text="📂 Abrir archivo", 
                  command=self._choose_file).pack(side="left", padx=2)
        
        self.lbl_filename = ttk.Label(top, text="(sin archivo)", 
                                     font=("Segoe UI", 9, "italic"))
        self.lbl_filename.pack(side="left", padx=10)
        
        self.lbl_file_info = ttk.Label(top, text="", foreground="blue")
        self.lbl_file_info.pack(side="left", padx=10)
        
        self.transcribe_btn = ttk.Button(top, text="▶️ Transcribir", 
                  command=self._run_single,
                  style="Accent.TButton")
        self.transcribe_btn.pack(side="right", padx=2)
        
        # Área de resultado
        body = ttk.Frame(self.tab_single, padding=10)
        body.pack(fill="both", expand=True)
        
        ttk.Label(body, text="Transcripción:", 
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        text_frame = ttk.Frame(body)
        text_frame.pack(fill="both", expand=True, pady=5)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.txt_result = tk.Text(text_frame, wrap="word", 
                                 font=("Segoe UI", 10),
                                 yscrollcommand=scrollbar.set)
        self.txt_result.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.txt_result.yview)
        
        # Botones de acción
        btn_frame = ttk.Frame(body)
        btn_frame.pack(fill="x", pady=5)
        
        ttk.Button(btn_frame, text="💾 Guardar", 
                  command=self._save_transcript).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Copiar", 
                  command=self._copy_to_clipboard).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ Limpiar", 
                  command=lambda: self.txt_result.delete("1.0", tk.END)).pack(side="left", padx=2)
    
    def _build_batch_tab(self):
        """Tab de procesamiento por lotes"""
        top = ttk.Frame(self.tab_batch, padding=10)
        top.pack(fill="x")
        
        ttk.Label(top, text="📥 INBOX:", 
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", pady=2)
        self.inbox_var = tk.StringVar(value=self.config.inbox_dir)
        ttk.Entry(top, textvariable=self.inbox_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(top, text="...", width=3,
                  command=lambda: self._pick_dir(self.inbox_var)).grid(row=0, column=2)
        
        ttk.Label(top, text="📤 OUT:", 
                 font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky="w", pady=2)
        self.out_var = tk.StringVar(value=self.config.output_dir)
        ttk.Entry(top, textvariable=self.out_var, width=60).grid(row=1, column=1, padx=5)
        ttk.Button(top, text="...", width=3,
                  command=lambda: self._pick_dir(self.out_var)).grid(row=1, column=2)
        
        btn_frame = ttk.Frame(self.tab_batch, padding=10)
        btn_frame.pack(fill="x")
        
        self.batch_btn = ttk.Button(btn_frame, text="▶️ Procesar carpeta", 
                  command=self._run_batch)
        self.batch_btn.pack(side="left", padx=2)
        
        # Progreso
        self.batch_progress = ttk.Progressbar(self.tab_batch, mode='determinate')
        self.batch_progress.pack(fill="x", padx=10, pady=5)
        
        # Log
        log_frame = ttk.Frame(self.tab_batch, padding=10)
        log_frame.pack(fill="both", expand=True)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(log_frame, wrap="word", 
                               font=("Consolas", 9),
                               yscrollcommand=log_scroll.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
    
    def _build_config_tab(self):
        """Tab de configuración"""
        # Canvas con scroll para contenido largo
        canvas = tk.Canvas(self.tab_config)
        scrollbar = ttk.Scrollbar(self.tab_config, orient="vertical", command=canvas.yview)
        
        # Frame principal dentro del canvas
        frame = ttk.Frame(canvas, padding=20)
        
        # Configurar scroll
        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # === PROVEEDOR Y MODELO ===
        section1 = ttk.LabelFrame(frame, text="🤖 Proveedor y Modelo", padding=15)
        section1.pack(fill="x", pady=10)
        
        # Empaquetar canvas y scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        ttk.Label(section1, text="Modelo:").grid(row=0, column=0, sticky="w", pady=5)
        
        self.model_var = tk.StringVar(value=self.config.model)
        
        # Crear combobox con info de cada modelo
        model_options = list(MODEL_COSTS.keys())
        self.model_combo = ttk.Combobox(section1, textvariable=self.model_var, 
                                       values=model_options, width=35, state="readonly")
        self.model_combo.grid(row=0, column=1, sticky="w", pady=5)
        self.model_combo.bind("<<ComboboxSelected>>", self._on_model_change)
        
        # Label con info del modelo seleccionado
        self.lbl_model_info = ttk.Label(section1, text="", foreground="blue")
        self.lbl_model_info.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # === API KEYS ===
        section2 = ttk.LabelFrame(frame, text="🔑 API Keys", padding=15)
        section2.pack(fill="x", pady=10)
        
        ttk.Label(section2, text="OpenAI API Key:").grid(row=0, column=0, sticky="w", pady=5)
        self.openai_key_var = tk.StringVar(value=self.config.openai_api_key)
        openai_entry = ttk.Entry(section2, textvariable=self.openai_key_var, width=50, show="*")
        openai_entry.grid(row=0, column=1, sticky="w", pady=5, padx=5)
        ttk.Button(section2, text="👁️", width=3,
                  command=lambda: self._toggle_password(openai_entry)).grid(row=0, column=2)
        
        ttk.Label(section2, text="Groq API Key:").grid(row=1, column=0, sticky="w", pady=5)
        self.groq_key_var = tk.StringVar(value=self.config.groq_api_key)
        groq_entry = ttk.Entry(section2, textvariable=self.groq_key_var, width=50, show="*")
        groq_entry.grid(row=1, column=1, sticky="w", pady=5, padx=5)
        ttk.Button(section2, text="👁️", width=3,
                  command=lambda: self._toggle_password(groq_entry)).grid(row=1, column=2)
        
        # Botón GUARDAR junto a las API keys (más visible)
        ttk.Button(section2, text="💾 GUARDAR CONFIGURACIÓN", 
                  command=self._save_config,
                  style="Accent.TButton").grid(row=2, column=0, columnspan=3, pady=15, sticky="ew")
        
        # Link para obtener Groq API gratis
        link = ttk.Label(section2, text="🎁 Obtener Groq API gratis (clic aquí)", 
                        foreground="blue", cursor="hand2")
        link.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        link.bind("<Button-1>", lambda e: self._open_groq_website())
        
        # === OPCIONES ===
        section3 = ttk.LabelFrame(frame, text="🎛️ Opciones de Procesamiento", padding=15)
        section3.pack(fill="x", pady=10)
        
        ttk.Label(section3, text="Bitrate (kbps):").grid(row=0, column=0, sticky="w", pady=5)
        self.br_var = tk.IntVar(value=self.config.bitrate)
        ttk.Spinbox(section3, from_=64, to=320, increment=16, 
                   textvariable=self.br_var, width=10).grid(row=0, column=1, sticky="w", pady=5)
        
        self.vad_var = tk.BooleanVar(value=self.config.use_vad)
        vad_check = ttk.Checkbutton(section3, text="VAD (recortar silencios) ⚠️ Consume mucha CPU", 
                       variable=self.vad_var)
        vad_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        self.srt_var = tk.BooleanVar(value=self.config.export_srt)
        ttk.Checkbutton(section3, text="Exportar subtítulos (SRT)", 
                       variable=self.srt_var).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        # === PRESUPUESTO ===
        section4 = ttk.LabelFrame(frame, text="💰 Control de Presupuesto", padding=15)
        section4.pack(fill="x", pady=10)
        
        ttk.Label(section4, text="Límite diario (USD):").grid(row=0, column=0, sticky="w", pady=5)
        self.budget_var = tk.DoubleVar(value=self.config.daily_budget)
        ttk.Entry(section4, textvariable=self.budget_var, width=15).grid(row=0, column=1, 
                                                                         sticky="w", pady=5)
        
        self.lbl_budget_status = ttk.Label(section4, text="")
        self.lbl_budget_status.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Botones adicionales
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=20)
        
        ttk.Button(btn_frame, text="🔄 Restaurar valores por defecto", 
                  command=self._reset_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🧪 Probar conexión API", 
                  command=self._test_api_connection).pack(side="left", padx=5)
        
        # Actualizar info inicial
        self._update_model_info()
        self._update_budget_status()
    
    def _build_compare_tab(self):
        """Tab de comparación de costes"""
        frame = ttk.Frame(self.tab_compare, padding=20)
        frame.pack(fill="both", expand=True)
        
        # Título
        title = ttk.Label(frame, text="💰 Comparador de Costes entre Proveedores", 
                         font=("Segoe UI", 14, "bold"))
        title.pack(pady=10)
        
        # Input de duración
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=10)
        
        ttk.Label(input_frame, text="Duración del audio (minutos):").pack(side="left", padx=5)
        self.compare_duration_var = tk.IntVar(value=60)
        ttk.Spinbox(input_frame, from_=1, to=600, textvariable=self.compare_duration_var, 
                   width=10).pack(side="left", padx=5)
        ttk.Button(input_frame, text="🔄 Calcular", 
                  command=self._update_comparison).pack(side="left", padx=5)
        
        # Tabla de comparación
        columns = ("Modelo", "Proveedor", "Coste", "Ahorro vs OpenAI", "API Key")
        self.compare_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.compare_tree.heading(col, text=col)
        
        self.compare_tree.column("Modelo", width=250)
        self.compare_tree.column("Proveedor", width=100)
        self.compare_tree.column("Coste", width=100)
        self.compare_tree.column("Ahorro vs OpenAI", width=150)
        self.compare_tree.column("API Key", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", 
                                 command=self.compare_tree.yview)
        self.compare_tree.configure(yscrollcommand=scrollbar.set)
        
        self.compare_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Resumen
        summary_frame = ttk.LabelFrame(frame, text="📊 Resumen", padding=15)
        summary_frame.pack(fill="x", pady=10)
        
        self.lbl_cheapest = ttk.Label(summary_frame, text="", font=("Segoe UI", 10))
        self.lbl_cheapest.pack(anchor="w", pady=2)
        
        self.lbl_savings = ttk.Label(summary_frame, text="", font=("Segoe UI", 10))
        self.lbl_savings.pack(anchor="w", pady=2)
        
        # Cargar comparación inicial
        self._update_comparison()
    
    # ========================================================================
    # MÉTODOS DE LÓGICA
    # ========================================================================
    
    def _apply_config_to_ui(self):
        """Aplicar configuración cargada a la UI"""
        if hasattr(self, 'model_var'):
            self.model_var.set(self.config.model)
        if hasattr(self, 'openai_key_var'):
            self.openai_key_var.set(self.config.openai_api_key)
        if hasattr(self, 'groq_key_var'):
            self.groq_key_var.set(self.config.groq_api_key)
        if hasattr(self, 'br_var'):
            self.br_var.set(self.config.bitrate)
        if hasattr(self, 'vad_var'):
            self.vad_var.set(self.config.use_vad)
        if hasattr(self, 'srt_var'):
            self.srt_var.set(self.config.export_srt)
        if hasattr(self, 'budget_var'):
            self.budget_var.set(self.config.daily_budget)
        if hasattr(self, 'inbox_var'):
            self.inbox_var.set(self.config.inbox_dir)
        if hasattr(self, 'out_var'):
            self.out_var.set(self.config.output_dir)
        
        # Configurar variables de entorno
        if self.config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.groq_api_key:
            os.environ['GROQ_API_KEY'] = self.config.groq_api_key
    
    def _update_config_from_ui(self):
        """Actualizar configuración desde la UI"""
        self.config.model = self.model_var.get()
        self.config.openai_api_key = self.openai_key_var.get()
        self.config.groq_api_key = self.groq_key_var.get()
        self.config.bitrate = int(self.br_var.get())
        self.config.use_vad = self.vad_var.get()
        self.config.export_srt = self.srt_var.get()
        self.config.daily_budget = float(self.budget_var.get())
        self.config.inbox_dir = self.inbox_var.get()
        self.config.output_dir = self.out_var.get()
        
        # Configurar variables de entorno para las APIs
        if self.config.openai_api_key:
            os.environ['OPENAI_API_KEY'] = self.config.openai_api_key
        if self.config.groq_api_key:
            os.environ['GROQ_API_KEY'] = self.config.groq_api_key
    
    def _save_config(self):
        """Guardar configuración"""
        try:
            # Actualizar config desde UI
            self._update_config_from_ui()
            
            # Validar que al menos una API key esté configurada si no es modo local
            if not self.config.model.startswith('local'):
                if not self.config.openai_api_key and not self.config.groq_api_key:
                    messagebox.showwarning(
                        "Advertencia",
                        "No has configurado ninguna API key.\n\n"
                        "Necesitas al menos una para transcribir:\n"
                        "- Groq API (recomendado, 98% más barato)\n"
                        "- OpenAI API\n\n"
                        "¿Continuar guardando de todas formas?"
                    )
            
            # Guardar
            self.config.save()
            budget_set_limit(self.config.daily_budget)
            
            # Actualizar barra de estado
            status_text = "Configuración guardada"
            if self.config.groq_api_key:
                status_text += " · Groq configurado ✓"
            if self.config.openai_api_key:
                status_text += " · OpenAI configurado ✓"
            self.status_bar.config(text=status_text)
            
            # Mensaje de éxito con detalles
            details = "✅ Configuración guardada correctamente\n\n"
            details += f"Modelo: {self.config.model}\n"
            if self.config.groq_api_key:
                details += f"Groq API: Configurada ({len(self.config.groq_api_key)} caracteres)\n"
            if self.config.openai_api_key:
                details += f"OpenAI API: Configurada ({len(self.config.openai_api_key)} caracteres)\n"
            details += f"Presupuesto: ${self.config.daily_budget}/día\n"
            
            messagebox.showinfo("Éxito", details)
            self._update_budget_status()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración:\n{e}")
            import traceback
            traceback.print_exc()
    
    def _reset_config(self):
        """Restaurar configuración por defecto"""
        if messagebox.askyesno("Confirmar", "¿Restaurar configuración por defecto?"):
            self.config = AppConfig()
            self._apply_config_to_ui()
            messagebox.showinfo("Configuración", "✓ Valores restaurados")
    
    def _on_model_change(self, event=None):
        """Cuando cambia el modelo seleccionado"""
        self._update_model_info()
    
    def _update_model_info(self):
        """Actualizar información del modelo seleccionado"""
        model = self.model_var.get()
        info = get_provider_info(model)
        
        cost_hour = info['cost_per_hour']
        provider = info['provider'].upper()
        
        text = f"💰 ${cost_hour:.4f}/hora"
        
        if info['is_free']:
            text += " · 🎉 GRATIS"
        elif info['savings_vs_openai'] > 0:
            text += f" · 📉 {info['savings_vs_openai']:.1f}% ahorro vs OpenAI"
        
        text += f" · 🔧 {provider}"
        
        if info['requires_api_key']:
            text += " (requiere API key)"
        
        self.lbl_model_info.config(text=text)
    
    def _update_budget_status(self):
        """Actualizar estado del presupuesto"""
        remaining = budget_get_remaining()
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
        
        self.lbl_budget_status.config(text=text, foreground=color)
    
    def _toggle_password(self, entry: ttk.Entry):
        """Mostrar/ocultar contraseña"""
        if entry.cget('show') == '*':
            entry.config(show='')
        else:
            entry.config(show='*')
    
    def _open_groq_website(self):
        """Abrir página de Groq para obtener API key"""
        import webbrowser
        webbrowser.open("https://console.groq.com/keys")
        messagebox.showinfo("Groq API", 
            "🎁 Abriendo console.groq.com\n\n"
            "1. Crea una cuenta gratis\n"
            "2. Ve a 'API Keys'\n"
            "3. Crea una nueva key\n"
            "4. Cópiala y pégala aquí\n\n"
            "¡Groq es 50x más barato que OpenAI!")
    
    def _test_api_connection(self):
        """Probar conexión con las APIs configuradas"""
        self._update_config_from_ui()
        
        results = []
        
        # Probar OpenAI
        if self.config.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.config.openai_api_key)
                # Intentar listar modelos como test
                client.models.list()
                results.append("✅ OpenAI: Conectado")
            except Exception as e:
                results.append(f"❌ OpenAI: {str(e)[:50]}")
        else:
            results.append("⚠️ OpenAI: Sin API key")
        
        # Probar Groq
        if self.config.groq_api_key:
            try:
                from groq import Groq
                client = Groq(api_key=self.config.groq_api_key)
                # Intentar listar modelos como test
                client.models.list()
                results.append("✅ Groq: Conectado")
            except Exception as e:
                results.append(f"❌ Groq: {str(e)[:50]}")
        else:
            results.append("⚠️ Groq: Sin API key")
        
        messagebox.showinfo("Test de Conexión", "\n".join(results))
    
    def _show_savings_tip(self):
        """Mostrar tip de ahorro al iniciar"""
        # No mostrar si ya tiene Groq configurado
        if self.config.groq_api_key:
            return
        
        # No mostrar si ya usa Groq
        if self.config.model.startswith('groq'):
            return
        
        # Solo mostrar si usa OpenAI
        if self.config.model.startswith('openai') or self.config.model == 'whisper-1':
            response = messagebox.askyesno(
                "💡 Tip de Ahorro",
                "Estás usando OpenAI Whisper que cuesta $0.006/min.\n\n"
                "¿Sabías que Groq ofrece la misma calidad por $0.00011/min?\n"
                "¡Eso es un 98% de ahorro!\n\n"
                "¿Quieres cambiar a Groq ahora?",
                icon='info'
            )
            if response:
                self._open_groq_website()
    
    def _update_comparison(self):
        """Actualizar tabla de comparación de costes"""
        duration_min = self.compare_duration_var.get()
        
        # Limpiar tabla
        for item in self.compare_tree.get_children():
            self.compare_tree.delete(item)
        
        # Obtener info de todos los modelos
        models_info = get_all_models_info()
        
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
            
            # Determinar si necesita API key
            needs_key = "✓ Sí" if info['requires_api_key'] else "No (local)"
            
            # Formato de ahorro
            if info['is_free']:
                savings_text = "GRATIS 🎉"
            elif savings > 0:
                savings_text = f"{savings:.1f}% 📉"
            else:
                savings_text = "Referencia"
            
            # Insertar en tabla
            self.compare_tree.insert("", "end", values=(
                info['model'],
                info['provider'].upper(),
                f"${cost:.4f}",
                savings_text,
                needs_key
            ))
        
        # Actualizar resumen
        if openai_cost > 0 and cheapest_cost < float('inf'):
            savings_amount = openai_cost - cheapest_cost
            savings_pct = (savings_amount / openai_cost * 100)
            
            self.lbl_cheapest.config(
                text=f"🏆 Más barato: {cheapest_model} (${cheapest_cost:.4f})"
            )
            self.lbl_savings.config(
                text=f"💰 Ahorrarías: ${savings_amount:.4f} ({savings_pct:.1f}%) vs OpenAI"
            )
    
    # ========================================================================
    # ARCHIVO ÚNICO
    # ========================================================================
    
    def _choose_file(self):
        """Seleccionar archivo"""
        ext_str = " ".join(f"*{ext}" for ext in AUDIO_EXT)
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[("Audio", ext_str), ("Todos", "*.*")]
        )
        
        if not file_path:
            return
        
        self.audio = Path(file_path)
        self.lbl_filename.config(text=self.audio.name)
        
        try:
            duration_sec = probe_duration(self.audio)
            cost = estimate_cost(duration_sec, self.config.model)
            
            minutes = duration_sec // 60
            seconds = duration_sec % 60
            
            info = f"⏱️ {minutes}:{seconds:02d} | 💰 ${cost:.4f} | 🤖 {PROVIDER_MAP.get(self.config.model, '?').upper()}"
            self.lbl_file_info.config(text=info)
            self.status_bar.config(text=f"Archivo cargado: {self.audio.name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
    
    def _run_single(self):
        """Transcribir archivo único"""
        if not self.audio:
            messagebox.showwarning("Sin archivo", "Selecciona un archivo primero")
            return
        
        # Deshabilitar botón de transcripción
        self.transcribe_btn.configure(state="disabled")
        self._update_config_from_ui()
        threading.Thread(target=self._worker_single, daemon=True).start()
    
    def _worker_single(self):
        """Worker para transcripción única"""
        try:
            src = self.audio
            
            # Si VAD está activado, verificar tamaño del archivo y avisar
            if self.config.use_vad:
                file_size_mb = self.audio.stat().st_size / (1024 * 1024)
                
                if file_size_mb > 10:  # Mayor a 10 MB
                    response = messagebox.askyesno(
                        "⚠️ Advertencia VAD",
                        f"El archivo pesa {file_size_mb:.1f} MB.\n\n"
                        "VAD (eliminación de silencios) puede tardar mucho\n"
                        "y consumir toda la CPU/RAM de tu PC.\n\n"
                        "Recomendación: Desactiva VAD en archivos grandes.\n\n"
                        "¿Continuar con VAD de todas formas?",
                        icon='warning'
                    )
                    
                    if not response:
                        self.after(0, lambda: messagebox.showinfo(
                            "Cancelado",
                            "Transcripción cancelada.\n\n"
                            "Tip: Desactiva VAD en Configuración para archivos grandes."
                        ))
                        return
                
                self.after(0, lambda: self.status_bar.config(text="Aplicando VAD... (puede tardar)"))
                src = preprocess_vad_ffmpeg(self.audio)
            
            # Barra de progreso
            progress = ttk.Progressbar(self.status_bar, mode='determinate', length=200)
            progress.pack(side="right", padx=5)
            self.status_bar.progress = progress
            
            def update_progress(current, total, msg=""):
                if not hasattr(self.status_bar, "progress"):
                    return
                progress = self.status_bar.progress
                progress["value"] = (current / total) * 100
                if msg:
                    self.status_bar.config(text=msg)
                self.update_idletasks()
            
            # Procesar audio
            update_progress(0, 100, "Dividiendo audio...")
            parts = split_for_api(src, bitrate_kbps=self.config.bitrate)
            total = sum(probe_duration(x) for x in parts)
            cost = estimate_cost(total, self.config.model)
            
            if not budget_allow(cost):
                self.after(0, lambda: messagebox.showwarning(
                    "Presupuesto", f"Sin presupuesto para ${cost:.4f}"))
                progress.destroy()
                return
            
            update_progress(10, 100, "Transcribiendo...")
            result = transcribe_file(src, model=self.config.model)
            update_progress(90, 100, "Guardando...")
            
            # Guardar archivos en carpeta de transcripciones
            timestamp = dt.datetime.now().timestamp()
            transcriptions_dir = Path(self.config.output_dir).parent / "transcripciones"
            transcriptions_dir.mkdir(exist_ok=True)
            
            out_base = transcriptions_dir / f"{self.audio.stem}_{int(timestamp)}"
            out_txt = out_base.with_suffix(".txt")
            out_txt.write_text(result.text, encoding="utf-8")
            
            has_srt = False
            if self.config.export_srt:
                out_srt = out_base.with_suffix(".srt")
                out_srt.write_text(write_srt(result), encoding="utf-8")
                has_srt = True
            
            # Limpiar archivos temporales
            try:
                for f in TEMP_DIR.glob("*"):
                    try:
                        f.unlink()
                    except:
                        pass
            except:
                pass
            
            # Guardar referencia del resultado para el historial
            self._last_transcript = result
            
            # Guardar en el archivo del historial
            duration = probe_duration(self.audio)
            history_record = {
                "id": str(uuid.uuid4()),
                "date": timestamp,
                "original_file": str(self.audio),
                "model": self.config.model,
                "duration": duration,
                "cost": cost,
                "language": result.language,
                "output_path": str(out_txt),
                "has_srt": has_srt,
                "use_vad": self.config.use_vad
            }
            
            # Cargar historial existente
            history_path = Path(self.config.output_dir).parent / "history.json"
            try:
                if history_path.exists():
                    with open(history_path, 'r', encoding='utf-8') as f:
                        history = json.load(f)
                else:
                    history = []
                    
                # Agregar nueva transcripción
                history.append(history_record)
                
                # Guardar historial actualizado
                with open(history_path, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                
                # Actualizar vista del historial
                self.history_tab._refresh_history()
            except Exception as e:
                print(f"Error actualizando historial: {e}")
            
            self.after(0, lambda: self.txt_result.delete("1.0", tk.END))
            self.after(0, lambda: self.txt_result.insert("1.0", result.text))
            
            budget_consume(cost)
            
            msg = f"✅ Transcripción completada\n\n"
            msg += f"📄 {out_txt}\n"
            msg += f"💰 Coste: ${cost:.4f}\n"
            msg += f"🤖 {PROVIDER_MAP.get(self.config.model, '?').upper()}"
            
            self.after(0, lambda: messagebox.showinfo("Éxito", msg))
            self.after(0, self._update_budget_status)
            
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
        finally:
            # Re-habilitar botón de transcripción al terminar (éxito o error)
            self.after(0, lambda: self.transcribe_btn.configure(state="normal"))
    
    # ========================================================================
    # PROCESAMIENTO POR LOTES
    # ========================================================================
    
    def _pick_dir(self, var: tk.StringVar):
        """Seleccionar directorio"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)
    
    def _run_batch(self):
        """Procesar lote"""
        self._update_config_from_ui()
        self.log_text.delete("1.0", tk.END)
        # Deshabilitar botón de procesamiento por lotes
        self.batch_btn.configure(state="disabled")
        threading.Thread(target=self._worker_batch, daemon=True).start()
    
    def _worker_batch(self):
        """Worker para procesamiento por lotes"""
        inbox = Path(self.inbox_var.get())
        outdir = Path(self.out_var.get())
        outdir.mkdir(parents=True, exist_ok=True)
        
        files = [f for f in sorted(inbox.glob("*")) if f.suffix.lower() in AUDIO_EXT]
        total_files = len(files)
        
        self._log(f"📁 Encontrados {total_files} archivos")
        
        successful = 0
        failed = 0
        total_cost = 0.0
        
        for i, p in enumerate(files, 1):
            try:
                self._log(f"[{i}/{total_files}] {p.name}...")
                self.after(0, lambda v=(i/total_files)*100: self.batch_progress.config(value=v))
                
                src = preprocess_vad_ffmpeg(p) if self.config.use_vad else p
                parts = split_for_api(src, bitrate_kbps=self.config.bitrate)
                total = sum(probe_duration(x) for x in parts)
                cost = estimate_cost(total, self.config.model)
                
                if not budget_allow(cost):
                    self._log(f"  ⚠️ SKIP: sin presupuesto (${cost:.4f})")
                    failed += 1
                    continue
                
                result = transcribe_file(src, model=self.config.model)
                
                base = outdir / p.stem
                (base.with_suffix(".txt")).write_text(result.text, encoding="utf-8")
                if self.config.export_srt:
                    (base.with_suffix(".srt")).write_text(write_srt(result), encoding="utf-8")
                
                budget_consume(cost)
                total_cost += cost
                successful += 1
                
                self._log(f"  ✅ OK (${cost:.4f})")
                
            except Exception as e:
                self._log(f"  ❌ ERROR: {e}")
                failed += 1
        
        self._log(f"\n{'='*50}")
        self._log(f"✅ Completado: {successful}/{total_files}")
        self._log(f"❌ Fallidos: {failed}")
        self._log(f"💰 Coste total: ${total_cost:.4f}")
        
        self.after(0, lambda: self.batch_progress.config(value=0))
        self.after(0, self._update_budget_status)
        # Re-habilitar botón de procesamiento por lotes al terminar
        self.after(0, lambda: self.batch_btn.configure(state="normal"))
    
    def _log(self, msg: str):
        """Añadir mensaje al log"""
        self.after(0, lambda: self.log_text.insert(tk.END, msg + "\n"))
        self.after(0, lambda: self.log_text.see(tk.END))
    
    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def _save_transcript(self):
        """Guardar transcripción"""
        text = self.txt_result.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin contenido", "No hay texto para guardar")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Subtítulos", "*.srt"), ("Todos", "*.*")]
        )
        
        if file_path:
            try:
                # Obtener detalles de la última transcripción
                segments = []
                original_file = ""
                language = None
                if hasattr(self, '_last_transcript') and self._last_transcript:
                    segments = self._last_transcript.segments or []
                    language = self._last_transcript.language
                    original_file = str(self.audio) if self.audio else ""
                
                # Guardar archivo de transcripción
                Path(file_path).write_text(text, encoding='utf-8')
                messagebox.showinfo("Guardado", f"✅ Guardado en:\n{file_path}")
                
                # Actualizar historial
                record = {
                    "id": str(uuid.uuid4()),
                    "date": time.time(),
                    "original_file": original_file,
                    "text": text,
                    "segments": segments,
                    "language": language
                }
                
                # Cargar historial existente
                history_path = Path(self.config.output_dir).parent / "history.json"
                try:
                    if history_path.exists():
                        with open(history_path, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    else:
                        history = []
                        
                    # Agregar nueva transcripción
                    history.append(record)
                    
                    # Guardar historial actualizado
                    with open(history_path, 'w', encoding='utf-8') as f:
                        json.dump(history, f, ensure_ascii=False, indent=2)
                    
                    # Actualizar vista del historial
                    self.history_tab._refresh_history()
                
                except Exception as e:
                    print(f"Error actualizando historial: {e}")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")
    
    def _copy_to_clipboard(self):
        """Copiar al portapapeles"""
        text = self.txt_result.get("1.0", tk.END).strip()
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
        app = App()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Error Fatal", 
            f"Error crítico:\n{e}\n\n"
            f"Revisa el log en: {ROOT}")

if __name__ == "__main__":
    main()
