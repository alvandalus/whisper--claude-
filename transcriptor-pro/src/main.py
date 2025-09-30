"""
Interfaz gráfica principal de Transcriptor Pro
Aplicación Tkinter para transcripción de audio multi-proveedor
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import datetime as dt
import logging
import webbrowser
from typing import Optional

from .config import AppConfig, TRANSCRIPTS_DIR
from .budget import get_budget_manager
from .history import get_history_manager
from .history_tab import HistoryTabManager
from .ui_utils import (
    ProgressDialog,
    StatusBarManager,
    ScrollableFrame,
    ConfirmDialog,
    format_cost,
    format_filesize,
    format_duration
)
from .audio_utils import (
    AUDIO_EXTENSIONS,
    get_audio_duration,
    apply_vad_preprocessing,
    validate_audio_file
)
from .core import (
    transcribe_audio,
    calculate_cost,
    generate_srt,
    get_model_info,
    get_all_models,
    MODEL_PRICING,
    PROVIDER_MAPPING
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TranscriptorProApp(tk.Tk):
    """Aplicación principal de Transcriptor Pro"""

    def __init__(self):
        super().__init__()
        self.title("Transcriptor Pro v1.0 – Multi-Provider Edition 🎙️")
        self.geometry("1100x750")
        self.minsize(1000, 700)

        # Cargar configuración
        self.config = AppConfig.load()
        self.config.setup_environment()

        # Estado
        self.current_audio: Optional[Path] = None
        self.last_result = None

        # Construir interfaz
        self._build_ui()

        # Aplicar configuración
        self.after(100, self._apply_config_to_ui)
        self.after(1000, self._show_welcome_message)

    # ========================================================================
    # CONSTRUCCIÓN DE INTERFAZ
    # ========================================================================

    def _build_ui(self):
        """Construir interfaz de usuario"""
        # Notebook principal
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Crear pestañas
        self.tab_single = ttk.Frame(notebook)
        notebook.add(self.tab_single, text="📄 Archivo único")

        self.tab_batch = ttk.Frame(notebook)
        notebook.add(self.tab_batch, text="📁 Procesamiento por lotes")

        self.tab_history = ttk.Frame(notebook)
        notebook.add(self.tab_history, text="📋 Historial")

        self.tab_config = ttk.Frame(notebook)
        notebook.add(self.tab_config, text="⚙️ Configuración")

        self.tab_compare = ttk.Frame(notebook)
        notebook.add(self.tab_compare, text="💰 Comparador")

        # Construir cada pestaña
        self._build_single_tab()
        self._build_batch_tab()
        self._build_history_tab()
        self._build_config_tab()
        self._build_compare_tab()

        # Barra de estado
        self._build_status_bar()

    def _build_single_tab(self):
        """Pestaña de archivo único"""
        # Frame superior - Controles
        top_frame = ttk.Frame(self.tab_single, padding=10)
        top_frame.pack(fill="x")

        ttk.Button(
            top_frame,
            text="📂 Abrir archivo",
            command=self._select_file
        ).pack(side="left", padx=2)

        self.lbl_filename = ttk.Label(
            top_frame,
            text="(sin archivo)",
            font=("Segoe UI", 9, "italic")
        )
        self.lbl_filename.pack(side="left", padx=10)

        self.lbl_file_info = ttk.Label(
            top_frame,
            text="",
            foreground="blue"
        )
        self.lbl_file_info.pack(side="left", padx=10)

        self.btn_transcribe = ttk.Button(
            top_frame,
            text="▶️ Transcribir",
            command=self._run_single_transcription,
            state="disabled"
        )
        self.btn_transcribe.pack(side="right", padx=2)

        # Frame de progreso
        progress_frame = ttk.Frame(self.tab_single, padding=(10, 5))
        progress_frame.pack(fill="x")

        # Barra de progreso
        self.single_progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=400
        )
        self.single_progress.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Label de porcentaje y estado
        self.lbl_progress = ttk.Label(
            progress_frame,
            text="",
            font=("Segoe UI", 9)
        )
        self.lbl_progress.pack(side="left")

        # Frame central - Resultado
        body_frame = ttk.Frame(self.tab_single, padding=10)
        body_frame.pack(fill="both", expand=True)

        ttk.Label(
            body_frame,
            text="Transcripción:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        # Área de texto con scrollbar
        text_frame = ttk.Frame(body_frame)
        text_frame.pack(fill="both", expand=True, pady=5)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        self.txt_result = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.txt_result.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.txt_result.yview)

        # Frame inferior - Acciones
        actions_frame = ttk.Frame(body_frame)
        actions_frame.pack(fill="x", pady=5)

        ttk.Button(
            actions_frame,
            text="💾 Guardar",
            command=self._save_transcription
        ).pack(side="left", padx=2)

        ttk.Button(
            actions_frame,
            text="📋 Copiar",
            command=self._copy_to_clipboard
        ).pack(side="left", padx=2)

        ttk.Button(
            actions_frame,
            text="🗑️ Limpiar",
            command=lambda: self.txt_result.delete("1.0", tk.END)
        ).pack(side="left", padx=2)

    def _build_batch_tab(self):
        """Pestaña de procesamiento por lotes"""
        # Frame superior - Configuración de carpetas
        top_frame = ttk.Frame(self.tab_batch, padding=10)
        top_frame.pack(fill="x")

        # INBOX
        ttk.Label(
            top_frame,
            text="📥 INBOX:",
            font=("Segoe UI", 9, "bold")
        ).grid(row=0, column=0, sticky="w", pady=2)

        self.var_inbox = tk.StringVar(value=self.config.inbox_dir)
        ttk.Entry(
            top_frame,
            textvariable=self.var_inbox,
            width=60
        ).grid(row=0, column=1, padx=5)

        ttk.Button(
            top_frame,
            text="...",
            width=3,
            command=lambda: self._select_directory(self.var_inbox)
        ).grid(row=0, column=2)

        # OUTPUT
        ttk.Label(
            top_frame,
            text="📤 OUT:",
            font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=0, sticky="w", pady=2)

        self.var_output = tk.StringVar(value=self.config.output_dir)
        ttk.Entry(
            top_frame,
            textvariable=self.var_output,
            width=60
        ).grid(row=1, column=1, padx=5)

        ttk.Button(
            top_frame,
            text="...",
            width=3,
            command=lambda: self._select_directory(self.var_output)
        ).grid(row=1, column=2)

        # Botón de proceso
        btn_frame = ttk.Frame(self.tab_batch, padding=10)
        btn_frame.pack(fill="x")

        self.btn_batch = ttk.Button(
            btn_frame,
            text="▶️ Procesar carpeta",
            command=self._run_batch_processing
        )
        self.btn_batch.pack(side="left", padx=2)

        # Barra de progreso
        self.batch_progress = ttk.Progressbar(
            self.tab_batch,
            mode='determinate'
        )
        self.batch_progress.pack(fill="x", padx=10, pady=5)

        # Log de procesamiento
        log_frame = ttk.Frame(self.tab_batch, padding=10)
        log_frame.pack(fill="both", expand=True)

        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")

        self.log_batch = tk.Text(
            log_frame,
            wrap="word",
            font=("Consolas", 9),
            yscrollcommand=log_scroll.set
        )
        self.log_batch.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_batch.yview)

    def _build_history_tab(self):
        """Pestaña de historial"""
        # Inicializar el gestor de historial
        self.history_tab_manager = HistoryTabManager(self.tab_history, self)

    def _build_config_tab(self):
        """Pestaña de configuración"""
        # Canvas con scroll
        canvas = tk.Canvas(self.tab_config)
        scrollbar = ttk.Scrollbar(
            self.tab_config,
            orient="vertical",
            command=canvas.yview
        )

        frame = ttk.Frame(canvas, padding=15)

        frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Scroll con rueda del mouse
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sección: Modelo
        section_model = ttk.LabelFrame(
            frame,
            text="🤖 Proveedor y Modelo",
            padding=10
        )
        section_model.pack(fill="x", pady=5)

        ttk.Label(section_model, text="Modelo:").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.var_model = tk.StringVar(value=self.config.model)
        self.combo_model = ttk.Combobox(
            section_model,
            textvariable=self.var_model,
            values=list(MODEL_PRICING.keys()),
            width=35,
            state="readonly"
        )
        self.combo_model.grid(row=0, column=1, sticky="w", pady=5)
        self.combo_model.bind("<<ComboboxSelected>>", self._on_model_change)

        self.lbl_model_info = ttk.Label(
            section_model,
            text="",
            foreground="blue"
        )
        self.lbl_model_info.grid(
            row=1, column=0, columnspan=2, sticky="w", pady=5
        )

        # Sección: API Keys
        section_keys = ttk.LabelFrame(
            frame,
            text="🔑 API Keys",
            padding=10
        )
        section_keys.pack(fill="x", pady=5)

        # OpenAI
        ttk.Label(section_keys, text="OpenAI API Key:").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.var_openai_key = tk.StringVar(value=self.config.openai_api_key)
        self.entry_openai = ttk.Entry(
            section_keys,
            textvariable=self.var_openai_key,
            width=50,
            show="*"
        )
        self.entry_openai.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        ttk.Button(
            section_keys,
            text="👁️",
            width=3,
            command=lambda: self._toggle_password(self.entry_openai)
        ).grid(row=0, column=2)

        # Groq
        ttk.Label(section_keys, text="Groq API Key:").grid(
            row=1, column=0, sticky="w", pady=5
        )

        self.var_groq_key = tk.StringVar(value=self.config.groq_api_key)
        self.entry_groq = ttk.Entry(
            section_keys,
            textvariable=self.var_groq_key,
            width=50,
            show="*"
        )
        self.entry_groq.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        ttk.Button(
            section_keys,
            text="👁️",
            width=3,
            command=lambda: self._toggle_password(self.entry_groq)
        ).grid(row=1, column=2)

        # Botón guardar
        ttk.Button(
            section_keys,
            text="💾 GUARDAR CONFIGURACIÓN",
            command=self._save_config
        ).grid(row=2, column=0, columnspan=3, pady=15, sticky="ew")

        # Link a Groq
        link_groq = ttk.Label(
            section_keys,
            text="🎁 Obtener Groq API gratis (clic aquí)",
            foreground="blue",
            cursor="hand2"
        )
        link_groq.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        link_groq.bind("<Button-1>", lambda e: self._open_groq_website())

        # Sección: Opciones
        section_opts = ttk.LabelFrame(
            frame,
            text="🎛️ Opciones de Procesamiento",
            padding=10
        )
        section_opts.pack(fill="x", pady=5)

        ttk.Label(section_opts, text="Bitrate (kbps):").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.var_bitrate = tk.IntVar(value=self.config.bitrate)
        ttk.Spinbox(
            section_opts,
            from_=64,
            to=320,
            increment=16,
            textvariable=self.var_bitrate,
            width=10
        ).grid(row=0, column=1, sticky="w", pady=5)

        self.var_vad = tk.BooleanVar(value=self.config.use_vad)
        ttk.Checkbutton(
            section_opts,
            text="VAD (recortar silencios) ⚠️ Consume CPU",
            variable=self.var_vad
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=5)

        self.var_srt = tk.BooleanVar(value=self.config.export_srt)
        ttk.Checkbutton(
            section_opts,
            text="Exportar subtítulos (SRT)",
            variable=self.var_srt
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        # Sección: Presupuesto
        section_budget = ttk.LabelFrame(
            frame,
            text="💰 Control de Presupuesto",
            padding=10
        )
        section_budget.pack(fill="x", pady=5)

        ttk.Label(section_budget, text="Límite diario (USD):").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.var_budget = tk.DoubleVar(value=self.config.daily_budget)
        ttk.Entry(
            section_budget,
            textvariable=self.var_budget,
            width=15
        ).grid(row=0, column=1, sticky="w", pady=5)

        self.lbl_budget_status = ttk.Label(section_budget, text="")
        self.lbl_budget_status.grid(
            row=1, column=0, columnspan=2, sticky="w", pady=5
        )

        # Actualizar info inicial
        self._update_model_info()
        self._update_budget_status()

    def _build_compare_tab(self):
        """Pestaña de comparación de costes"""
        frame = ttk.Frame(self.tab_compare, padding=20)
        frame.pack(fill="both", expand=True)

        # Título
        ttk.Label(
            frame,
            text="💰 Comparador de Costes entre Proveedores",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        # Input
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill="x", pady=10)

        ttk.Label(
            input_frame,
            text="Duración del audio (minutos):"
        ).pack(side="left", padx=5)

        self.var_duration = tk.IntVar(value=60)
        ttk.Spinbox(
            input_frame,
            from_=1,
            to=600,
            textvariable=self.var_duration,
            width=10
        ).pack(side="left", padx=5)

        ttk.Button(
            input_frame,
            text="🔄 Calcular",
            command=self._update_comparison
        ).pack(side="left", padx=5)

        # Tabla
        columns = ("Modelo", "Proveedor", "Coste", "Ahorro vs OpenAI", "API Key")
        self.tree_compare = ttk.Treeview(
            frame,
            columns=columns,
            show="headings",
            height=12
        )

        for col in columns:
            self.tree_compare.heading(col, text=col)

        self.tree_compare.column("Modelo", width=250)
        self.tree_compare.column("Proveedor", width=100)
        self.tree_compare.column("Coste", width=100)
        self.tree_compare.column("Ahorro vs OpenAI", width=150)
        self.tree_compare.column("API Key", width=100)

        tree_scroll = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=self.tree_compare.yview
        )
        self.tree_compare.configure(yscrollcommand=tree_scroll.set)

        self.tree_compare.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Resumen
        summary_frame = ttk.LabelFrame(frame, text="📊 Resumen", padding=15)
        summary_frame.pack(fill="x", pady=10)

        self.lbl_cheapest = ttk.Label(
            summary_frame,
            text="",
            font=("Segoe UI", 10)
        )
        self.lbl_cheapest.pack(anchor="w", pady=2)

        self.lbl_savings = ttk.Label(
            summary_frame,
            text="",
            font=("Segoe UI", 10)
        )
        self.lbl_savings.pack(anchor="w", pady=2)

        # Cargar datos iniciales
        self._update_comparison()

    def _build_status_bar(self):
        """Barra de estado"""
        status_text = "Listo"
        if self.config.groq_api_key:
            status_text += " · Groq configurado ✓"
        elif self.config.openai_api_key:
            status_text += " · OpenAI configurado ✓"

        self.status_bar = ttk.Label(
            self,
            text=status_text,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ========================================================================
    # LÓGICA - ARCHIVO ÚNICO
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

        self.current_audio = Path(file_path)

        # Validar archivo
        is_valid, error = validate_audio_file(self.current_audio)
        if not is_valid:
            messagebox.showerror("Error", f"Archivo inválido:\n{error}")
            self.current_audio = None
            return

        # Actualizar UI
        self.lbl_filename.config(text=self.current_audio.name)

        try:
            duration_sec = get_audio_duration(self.current_audio)
            cost = calculate_cost(duration_sec, self.config.model)

            provider = PROVIDER_MAPPING.get(self.config.model, '?').upper()
            info = f"⏱️ {format_duration(duration_sec)} | 💰 ${cost:.4f} | 🤖 {provider}"

            self.lbl_file_info.config(text=info)
            self.btn_transcribe.config(state="normal")
            self.status_bar.config(text=f"Archivo cargado: {self.current_audio.name}")

        except Exception as e:
            logger.error(f"Error procesando archivo: {e}")
            messagebox.showerror("Error", f"Error procesando archivo:\n{e}")

    def _run_single_transcription(self):
        """Ejecutar transcripción de archivo único"""
        if not self.current_audio:
            messagebox.showwarning("Sin archivo", "Selecciona un archivo primero")
            return

        self.btn_transcribe.config(state="disabled")
        self._sync_config()

        threading.Thread(
            target=self._worker_single_transcription,
            daemon=True
        ).start()

    def _worker_single_transcription(self):
        """Worker thread para transcripción única"""
        try:
            # Inicializar progreso
            self._update_progress(0, "Iniciando...")

            src = self.current_audio

            # Aplicar VAD si está activado
            if self.config.use_vad:
                file_size_mb = src.stat().st_size / (1024 * 1024)

                if file_size_mb > 10:
                    response = messagebox.askyesno(
                        "⚠️ Advertencia VAD",
                        f"El archivo pesa {file_size_mb:.1f} MB.\n\n"
                        "VAD puede tardar mucho y consumir CPU.\n\n"
                        "¿Continuar?",
                        icon='warning'
                    )

                    if not response:
                        self.after(0, lambda: self.btn_transcribe.config(state="normal"))
                        self._update_progress(0, "")
                        return

                self._update_status("Aplicando VAD...")
                self._update_progress(10, "Aplicando VAD...")
                src = apply_vad_preprocessing(src)
                self._update_progress(20, "VAD completado")

            # Verificar presupuesto
            self._update_progress(25, "Verificando presupuesto...")
            duration = get_audio_duration(src)
            cost = calculate_cost(duration, self.config.model)

            budget_mgr = get_budget_manager()
            if not budget_mgr.check_available(cost):
                self.after(0, lambda: messagebox.showwarning(
                    "Presupuesto",
                    f"Sin presupuesto para ${cost:.4f}\n"
                    f"Disponible: ${budget_mgr.get_remaining():.4f}"
                ))
                self._update_progress(0, "")
                return

            # Transcribir
            self._update_status("Transcribiendo...")
            self._update_progress(40, "Transcribiendo audio...")
            result = transcribe_audio(src, model=self.config.model)
            self._update_progress(80, "Transcripción completada")

            # Guardar
            self._update_progress(85, "Guardando archivos...")
            timestamp = int(dt.datetime.now().timestamp())
            out_dir = Path(self.config.output_dir)
            out_dir.mkdir(exist_ok=True, parents=True)

            base_name = f"{self.current_audio.stem}_{timestamp}"
            out_txt = out_dir / f"{base_name}.txt"
            out_txt.write_text(result.text, encoding="utf-8")

            if self.config.export_srt:
                out_srt = out_dir / f"{base_name}.srt"
                out_srt.write_text(generate_srt(result), encoding="utf-8")

            self._update_progress(95, "Actualizando historial...")

            # Guardar en historial
            history_mgr = get_history_manager()
            history_mgr.add_transcription({
                'original_file': str(self.current_audio),
                'model': self.config.model,
                'duration': duration,
                'cost': cost,
                'language': result.language if hasattr(result, 'language') else 'unknown',
                'output_path': str(out_txt),
                'text_preview': result.text[:200] + '...' if len(result.text) > 200 else result.text,
                'has_srt': self.config.export_srt
            })

            # Actualizar UI
            self.after(0, lambda: self.txt_result.delete("1.0", tk.END))
            self.after(0, lambda: self.txt_result.insert("1.0", result.text))

            # Refrescar historial si está visible
            if hasattr(self, 'history_tab_manager'):
                self.after(0, lambda: self.history_tab_manager.refresh())

            # Consumir presupuesto
            budget_mgr.consume(cost)

            # Mensaje de éxito
            msg = (
                f"✅ Transcripción completada\n\n"
                f"📄 {out_txt}\n"
                f"💰 Coste: ${cost:.4f}\n"
                f"🤖 {PROVIDER_MAPPING.get(self.config.model, '?').upper()}"
            )

            self._update_progress(100, "¡Completado!")
            self.after(0, lambda: messagebox.showinfo("Éxito", msg))
            self.after(0, self._update_budget_status)
            self._update_status("Listo")

            # Limpiar progreso después de 2 segundos
            self.after(2000, lambda: self._update_progress(0, ""))

        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            self.after(0, lambda: messagebox.showerror(
                "Error",
                f"Error en transcripción:\n{str(e)}"
            ))
            self._update_progress(0, "Error")
        finally:
            self.after(0, lambda: self.btn_transcribe.config(state="normal"))

    # ========================================================================
    # LÓGICA - LOTES
    # ========================================================================

    def _run_batch_processing(self):
        """Ejecutar procesamiento por lotes"""
        self._sync_config()
        self.log_batch.delete("1.0", tk.END)
        self.btn_batch.config(state="disabled")

        threading.Thread(
            target=self._worker_batch_processing,
            daemon=True
        ).start()

    def _worker_batch_processing(self):
        """Worker thread para procesamiento por lotes"""
        inbox = Path(self.var_inbox.get())
        outdir = Path(self.var_output.get())
        outdir.mkdir(parents=True, exist_ok=True)

        files = [
            f for f in sorted(inbox.glob("*"))
            if f.suffix.lower() in AUDIO_EXTENSIONS
        ]
        total_files = len(files)

        self._log(f"📁 Encontrados {total_files} archivos\n")

        successful = 0
        failed = 0
        total_cost = 0.0
        budget_mgr = get_budget_manager()

        for i, audio_file in enumerate(files, 1):
            try:
                self._log(f"[{i}/{total_files}] {audio_file.name}...")
                self.after(
                    0,
                    lambda v=(i/total_files)*100: self.batch_progress.config(value=v)
                )

                # Aplicar VAD si está activado
                src = audio_file
                if self.config.use_vad:
                    src = apply_vad_preprocessing(audio_file)

                # Calcular coste
                duration = get_audio_duration(src)
                cost = calculate_cost(duration, self.config.model)

                # Verificar presupuesto
                if not budget_mgr.check_available(cost):
                    self._log(f"  ⚠️ SKIP: sin presupuesto (${cost:.4f})\n")
                    failed += 1
                    continue

                # Transcribir
                result = transcribe_audio(src, model=self.config.model)

                # Guardar
                base = outdir / audio_file.stem
                out_txt = base.with_suffix(".txt")
                out_txt.write_text(result.text, encoding="utf-8")

                if self.config.export_srt:
                    base.with_suffix(".srt").write_text(
                        generate_srt(result),
                        encoding="utf-8"
                    )

                # Guardar en historial
                history_mgr = get_history_manager()
                history_mgr.add_transcription({
                    'original_file': str(audio_file),
                    'model': self.config.model,
                    'duration': duration,
                    'cost': cost,
                    'language': result.language if hasattr(result, 'language') else 'unknown',
                    'output_path': str(out_txt),
                    'text_preview': result.text[:200] + '...' if len(result.text) > 200 else result.text,
                    'has_srt': self.config.export_srt
                })

                # Consumir presupuesto
                budget_mgr.consume(cost)
                total_cost += cost
                successful += 1

                self._log(f"  ✅ OK (${cost:.4f})\n")

            except Exception as e:
                logger.error(f"Error procesando {audio_file.name}: {e}")
                self._log(f"  ❌ ERROR: {e}\n")
                failed += 1

        # Resumen
        self._log(f"\n{'='*50}\n")
        self._log(f"✅ Completado: {successful}/{total_files}\n")
        self._log(f"❌ Fallidos: {failed}\n")
        self._log(f"💰 Coste total: ${total_cost:.4f}\n")

        self.after(0, lambda: self.batch_progress.config(value=0))
        self.after(0, self._update_budget_status)
        self.after(0, lambda: self.btn_batch.config(state="normal"))

        # Refrescar historial si hay nuevas transcripciones
        if successful > 0 and hasattr(self, 'history_tab_manager'):
            self.after(0, lambda: self.history_tab_manager.refresh())

    def _log(self, msg: str):
        """Añadir mensaje al log de lotes"""
        self.after(0, lambda: self.log_batch.insert(tk.END, msg))
        self.after(0, lambda: self.log_batch.see(tk.END))

    # ========================================================================
    # LÓGICA - CONFIGURACIÓN
    # ========================================================================

    def _sync_config(self):
        """Sincronizar configuración desde UI"""
        self.config.model = self.var_model.get()
        self.config.openai_api_key = self.var_openai_key.get()
        self.config.groq_api_key = self.var_groq_key.get()
        self.config.bitrate = int(self.var_bitrate.get())
        self.config.use_vad = self.var_vad.get()
        self.config.export_srt = self.var_srt.get()
        self.config.daily_budget = float(self.var_budget.get())
        self.config.inbox_dir = self.var_inbox.get()
        self.config.output_dir = self.var_output.get()

        self.config.setup_environment()

    def _apply_config_to_ui(self):
        """Aplicar configuración cargada a UI"""
        if hasattr(self, 'var_model'):
            self.var_model.set(self.config.model)
        if hasattr(self, 'var_openai_key'):
            self.var_openai_key.set(self.config.openai_api_key)
        if hasattr(self, 'var_groq_key'):
            self.var_groq_key.set(self.config.groq_api_key)
        if hasattr(self, 'var_bitrate'):
            self.var_bitrate.set(self.config.bitrate)
        if hasattr(self, 'var_vad'):
            self.var_vad.set(self.config.use_vad)
        if hasattr(self, 'var_srt'):
            self.var_srt.set(self.config.export_srt)
        if hasattr(self, 'var_budget'):
            self.var_budget.set(self.config.daily_budget)
        if hasattr(self, 'var_inbox'):
            self.var_inbox.set(self.config.inbox_dir)
        if hasattr(self, 'var_output'):
            self.var_output.set(self.config.output_dir)

    def _save_config(self):
        """Guardar configuración"""
        try:
            self._sync_config()

            # Validar
            is_valid, error = self.config.validate()
            if not is_valid:
                messagebox.showwarning("Validación", error)
                return

            # Guardar
            self.config.save()
            get_budget_manager().set_limit(self.config.daily_budget)

            # Actualizar barra de estado
            status_text = "Configuración guardada"
            if self.config.groq_api_key:
                status_text += " · Groq configurado ✓"
            if self.config.openai_api_key:
                status_text += " · OpenAI configurado ✓"
            self.status_bar.config(text=status_text)

            messagebox.showinfo("Éxito", "✅ Configuración guardada correctamente")
            self._update_budget_status()

        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _on_model_change(self, event=None):
        """Cuando cambia el modelo"""
        self._update_model_info()

    def _update_model_info(self):
        """Actualizar información del modelo"""
        model = self.var_model.get()
        info = get_model_info(model)

        text = f"💰 ${info['cost_per_hour']:.4f}/hora"

        if info['is_free']:
            text += " · 🎉 GRATIS"
        elif info['savings_vs_openai'] > 0:
            text += f" · 📉 {info['savings_vs_openai']:.1f}% ahorro"

        text += f" · 🔧 {info['provider'].upper()}"

        if info['requires_api_key']:
            text += " (requiere API key)"

        self.lbl_model_info.config(text=text)

    def _update_budget_status(self):
        """Actualizar estado de presupuesto"""
        stats = get_budget_manager().get_stats()

        text = (
            f"Gastado hoy: ${stats['consumed']:.2f} "
            f"de ${stats['limit']:.2f} ({stats['percentage']:.1f}%)"
        )

        if stats['remaining'] <= 0:
            text += " ⚠️ LÍMITE ALCANZADO"
            color = "red"
        elif stats['percentage'] > 75:
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
        """Abrir página de Groq"""
        webbrowser.open("https://console.groq.com/keys")

    # ========================================================================
    # LÓGICA - COMPARADOR
    # ========================================================================

    def _update_comparison(self):
        """Actualizar tabla de comparación"""
        duration_min = self.var_duration.get()

        # Limpiar tabla
        for item in self.tree_compare.get_children():
            self.tree_compare.delete(item)

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

            self.tree_compare.insert("", "end", values=(
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
    # UTILIDADES
    # ========================================================================

    def _select_directory(self, var: tk.StringVar):
        """Seleccionar directorio"""
        directory = filedialog.askdirectory()
        if directory:
            var.set(directory)

    def _save_transcription(self):
        """Guardar transcripción"""
        text = self.txt_result.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin contenido", "No hay texto para guardar")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Texto", "*.txt"),
                ("Subtítulos", "*.srt"),
                ("Todos", "*.*")
            ]
        )

        if file_path:
            try:
                Path(file_path).write_text(text, encoding='utf-8')
                messagebox.showinfo("Guardado", f"✅ Guardado en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

    def _copy_to_clipboard(self):
        """Copiar al portapapeles"""
        text = self.txt_result.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin contenido", "No hay texto para copiar")
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self._update_status("✓ Copiado al portapapeles")
        self.after(2000, lambda: self._update_status("Listo"))

    def _update_status(self, text: str):
        """Actualizar barra de estado"""
        self.after(0, lambda: self.status_bar.config(text=text))

    def _update_progress(self, value: int, message: str = ""):
        """Actualizar barra de progreso y mensaje"""
        def update():
            self.single_progress['value'] = value
            if message:
                self.lbl_progress.config(text=f"{value}% - {message}")
            else:
                self.lbl_progress.config(text="")
        self.after(0, update)

    def _show_welcome_message(self):
        """Mostrar mensaje de bienvenida"""
        if not self.config.groq_api_key and not self.config.openai_api_key:
            messagebox.showinfo(
                "🎙️ Bienvenido a Transcriptor Pro",
                "Transcriptor Pro es una herramienta profesional de transcripción.\n\n"
                "Para empezar:\n"
                "1. Ve a la pestaña 'Configuración'\n"
                "2. Configura tu API key (Groq recomendado)\n"
                "3. Guarda la configuración\n"
                "4. ¡Empieza a transcribir!\n\n"
                "Groq es 98% más barato que OpenAI 💰"
            )


def main():
    """Función principal"""
    try:
        app = TranscriptorProApp()
        app.mainloop()
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        messagebox.showerror(
            "Error Fatal",
            f"Error crítico:\n{e}\n\n"
            f"Revisa los logs en: {TRANSCRIPTS_DIR.parent}"
        )


if __name__ == "__main__":
    main()
