"""
Pestaña de historial con funcionalidad completa
Vista, búsqueda, filtros y estadísticas de transcripciones
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import datetime as dt
import os
from typing import Optional

from .history import get_history_manager
from .ui_utils import ScrollableFrame, ConfirmDialog, format_duration, format_cost, format_filesize


class HistoryTabManager:
    """Gestor de la pestaña de historial"""

    def __init__(self, parent_frame: ttk.Frame, app):
        """
        Inicializar gestor de historial

        Args:
            parent_frame: Frame padre (la pestaña)
            app: Referencia a la aplicación principal
        """
        self.frame = parent_frame
        self.app = app
        self.history_mgr = get_history_manager()
        self.current_filter = "all"  # all, today, week, month
        self.search_query = ""

        self._build_ui()
        self._load_history()

    def _build_ui(self):
        """Construir interfaz de la pestaña"""
        # Frame superior - Búsqueda y filtros
        top_frame = ttk.Frame(self.frame, padding=10)
        top_frame.pack(fill="x")

        # Título y estadísticas
        header_frame = ttk.Frame(top_frame)
        header_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header_frame,
            text="📋 Historial de Transcripciones",
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        self.lbl_stats = ttk.Label(
            header_frame,
            text="",
            font=("Segoe UI", 9),
            foreground="gray"
        )
        self.lbl_stats.pack(side="left", padx=20)

        # Botones de acción
        ttk.Button(
            header_frame,
            text="📊 Estadísticas",
            command=self._show_statistics
        ).pack(side="right", padx=2)

        ttk.Button(
            header_frame,
            text="💾 Exportar CSV",
            command=self._export_csv
        ).pack(side="right", padx=2)

        ttk.Button(
            header_frame,
            text="🗑️ Limpiar todo",
            command=self._clear_all
        ).pack(side="right", padx=2)

        # Búsqueda
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="🔍 Buscar:").pack(side="left", padx=5)

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=30
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        ttk.Button(
            search_frame,
            text="Buscar",
            command=self._on_search
        ).pack(side="left", padx=2)

        ttk.Button(
            search_frame,
            text="Limpiar",
            command=self._clear_search
        ).pack(side="left", padx=2)

        # Filtros
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(fill="x", pady=5)

        ttk.Label(filter_frame, text="📅 Filtrar:").pack(side="left", padx=5)

        filters = [
            ("Todos", "all"),
            ("Hoy", "today"),
            ("Esta semana", "week"),
            ("Este mes", "month")
        ]

        self.filter_var = tk.StringVar(value="all")
        for text, value in filters:
            ttk.Radiobutton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._apply_filter
            ).pack(side="left", padx=5)

        ttk.Label(filter_frame, text="|").pack(side="left", padx=10)

        ttk.Button(
            filter_frame,
            text="🔄 Actualizar",
            command=self._load_history
        ).pack(side="left", padx=2)

        # Separador
        ttk.Separator(self.frame, orient="horizontal").pack(fill="x", padx=10)

        # Frame central - Lista de transcripciones
        list_frame = ttk.Frame(self.frame, padding=10)
        list_frame.pack(fill="both", expand=True)

        # Treeview con scrollbar
        columns = ("Fecha", "Archivo", "Modelo", "Duración", "Coste", "Idioma")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse",
            height=15
        )

        # Configurar columnas
        self.tree.column("#0", width=30, stretch=False)
        self.tree.heading("#0", text="")

        column_widths = {
            "Fecha": 150,
            "Archivo": 250,
            "Modelo": 180,
            "Duración": 100,
            "Coste": 80,
            "Idioma": 80
        }

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Doble clic para ver detalles
        self.tree.bind("<Double-1>", self._on_double_click)

        # Click derecho para menú contextual
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Frame inferior - Vista previa
        preview_frame = ttk.LabelFrame(
            self.frame,
            text="📄 Vista Previa",
            padding=10
        )
        preview_frame.pack(fill="x", padx=10, pady=10)

        # Texto de vista previa
        preview_text_frame = ttk.Frame(preview_frame)
        preview_text_frame.pack(fill="both", expand=True)

        preview_scroll = ttk.Scrollbar(preview_text_frame)
        preview_scroll.pack(side="right", fill="y")

        self.txt_preview = tk.Text(
            preview_text_frame,
            wrap="word",
            font=("Segoe UI", 9),
            height=4,
            yscrollcommand=preview_scroll.set,
            state="disabled"
        )
        self.txt_preview.pack(side="left", fill="both", expand=True)
        preview_scroll.config(command=self.txt_preview.yview)

        # Botones de vista previa
        preview_btns = ttk.Frame(preview_frame)
        preview_btns.pack(fill="x", pady=(5, 0))

        ttk.Button(
            preview_btns,
            text="👁️ Ver completo",
            command=self._view_full
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_btns,
            text="📂 Abrir archivo",
            command=self._open_file
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_btns,
            text="🎵 Abrir audio",
            command=self._open_audio
        ).pack(side="left", padx=2)

        ttk.Button(
            preview_btns,
            text="🗑️ Eliminar",
            command=self._delete_selected
        ).pack(side="right", padx=2)

        # Bind de selección
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _load_history(self):
        """Cargar historial y mostrar en tree"""
        # Limpiar tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtener registros
        records = self.history_mgr.get_all(sort_by='date', reverse=True)

        # Aplicar filtros
        if self.current_filter != "all":
            records = self._filter_records(records)

        # Aplicar búsqueda
        if self.search_query:
            records = self.history_mgr.search(self.search_query)

        # Insertar en tree
        for record in records:
            date_str = dt.datetime.fromtimestamp(
                record.get('timestamp', 0)
            ).strftime("%Y-%m-%d %H:%M")

            filename = Path(record.get('original_file', '')).name
            model = record.get('model', 'N/A')
            duration = format_duration(record.get('duration', 0))
            cost = format_cost(record.get('cost', 0))
            language = record.get('language', 'N/A')

            # Icono según modelo
            icon = "🤖" if record.get('model', '').startswith('groq') else "🔷"

            self.tree.insert(
                "",
                "end",
                text=icon,
                values=(date_str, filename, model, duration, cost, language),
                tags=(record.get('id'),)
            )

        # Actualizar estadísticas
        self._update_stats(len(records))

    def _filter_records(self, records):
        """Filtrar registros por fecha"""
        now = dt.datetime.now()

        if self.current_filter == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.current_filter == "week":
            start = now - dt.timedelta(days=7)
        elif self.current_filter == "month":
            start = now - dt.timedelta(days=30)
        else:
            return records

        filtered = []
        for record in records:
            record_date = dt.datetime.fromtimestamp(record.get('timestamp', 0))
            if record_date >= start:
                filtered.append(record)

        return filtered

    def _apply_filter(self):
        """Aplicar filtro seleccionado"""
        self.current_filter = self.filter_var.get()
        self._load_history()

    def _on_search(self):
        """Ejecutar búsqueda"""
        self.search_query = self.search_var.get().strip()
        self._load_history()

    def _clear_search(self):
        """Limpiar búsqueda"""
        self.search_var.set("")
        self.search_query = ""
        self._load_history()

    def _update_stats(self, count: int):
        """Actualizar estadísticas en la cabecera"""
        stats = self.history_mgr.get_statistics()
        text = (
            f"{count} transcripciones | "
            f"{stats['total_duration_hours']:.1f}h | "
            f"${stats['total_cost']:.2f}"
        )
        self.lbl_stats.config(text=text)

    def _on_select(self, event):
        """Cuando se selecciona un item"""
        selection = self.tree.selection()
        if not selection:
            return

        # Obtener ID del registro
        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        record_id = tags[0]
        record = self.history_mgr.get_by_id(record_id)

        if not record:
            return

        # Mostrar vista previa
        self.txt_preview.config(state="normal")
        self.txt_preview.delete("1.0", tk.END)

        preview_text = record.get('text_preview', record.get('text', 'Sin vista previa disponible'))
        self.txt_preview.insert("1.0", preview_text[:500])

        self.txt_preview.config(state="disabled")

    def _on_double_click(self, event):
        """Doble click en item"""
        self._view_full()

    def _view_full(self):
        """Ver transcripción completa"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Selecciona una transcripción primero")
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        record_id = tags[0]
        record = self.history_mgr.get_by_id(record_id)

        if not record:
            return

        # Crear ventana
        window = tk.Toplevel(self.app)
        window.title(f"Transcripción - {Path(record.get('original_file', '')).name}")
        window.geometry("800x600")

        # Frame con scroll
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill="both", expand=True)

        # Info
        info_text = (
            f"📄 Archivo: {record.get('original_file', 'N/A')}\n"
            f"🤖 Modelo: {record.get('model', 'N/A')}\n"
            f"⏱️ Duración: {format_duration(record.get('duration', 0))}\n"
            f"💰 Coste: {format_cost(record.get('cost', 0))}\n"
            f"🌐 Idioma: {record.get('language', 'N/A')}\n"
            f"📅 Fecha: {dt.datetime.fromtimestamp(record.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        ttk.Label(
            frame,
            text=info_text,
            font=("Segoe UI", 9),
            justify="left"
        ).pack(anchor="w", pady=10)

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=5)

        # Texto
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(
            text_frame,
            wrap="word",
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # Cargar texto desde archivo
        output_path = record.get('output_path')
        if output_path and Path(output_path).exists():
            try:
                text_widget.insert("1.0", Path(output_path).read_text(encoding='utf-8'))
            except Exception as e:
                text_widget.insert("1.0", f"Error cargando archivo: {e}")
        else:
            text_widget.insert("1.0", "Archivo no disponible")

        text_widget.config(state="disabled")

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(
            btn_frame,
            text="📋 Copiar",
            command=lambda: self._copy_text(text_widget)
        ).pack(side="left", padx=2)

        ttk.Button(
            btn_frame,
            text="Cerrar",
            command=window.destroy
        ).pack(side="right", padx=2)

    def _copy_text(self, text_widget):
        """Copiar texto al portapapeles"""
        text = text_widget.get("1.0", tk.END).strip()
        self.app.clipboard_clear()
        self.app.clipboard_append(text)
        messagebox.showinfo("Copiado", "Texto copiado al portapapeles")

    def _open_file(self):
        """Abrir archivo de transcripción"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        record = self.history_mgr.get_by_id(tags[0])
        if not record:
            return

        output_path = record.get('output_path')
        if output_path and Path(output_path).exists():
            os.startfile(output_path)
        else:
            messagebox.showerror("Error", "Archivo no encontrado")

    def _open_audio(self):
        """Abrir archivo de audio original"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        record = self.history_mgr.get_by_id(tags[0])
        if not record:
            return

        audio_path = record.get('original_file')
        if audio_path and Path(audio_path).exists():
            os.startfile(audio_path)
        else:
            messagebox.showerror("Error", "Archivo de audio no encontrado")

    def _delete_selected(self):
        """Eliminar transcripción seleccionada"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Sin selección", "Selecciona una transcripción primero")
            return

        if not ConfirmDialog.ask(
            self.app,
            "Confirmar eliminación",
            "¿Eliminar esta transcripción del historial?"
        ):
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        if not tags:
            return

        if self.history_mgr.delete(tags[0]):
            self.tree.delete(item)
            self.txt_preview.config(state="normal")
            self.txt_preview.delete("1.0", tk.END)
            self.txt_preview.config(state="disabled")
            messagebox.showinfo("Eliminado", "Transcripción eliminada del historial")

    def _clear_all(self):
        """Limpiar todo el historial"""
        if not ConfirmDialog.ask(
            self.app,
            "Confirmar limpieza",
            "¿Eliminar TODO el historial?\n\nEsta acción no se puede deshacer."
        ):
            return

        count = self.history_mgr.clear_all()
        self._load_history()
        messagebox.showinfo("Limpiado", f"{count} transcripciones eliminadas del historial")

    def _show_statistics(self):
        """Mostrar ventana de estadísticas"""
        stats = self.history_mgr.get_statistics()

        window = tk.Toplevel(self.app)
        window.title("📊 Estadísticas")
        window.geometry("500x600")

        frame = ttk.Frame(window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="📊 Estadísticas de Uso",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        # Estadísticas generales
        general_frame = ttk.LabelFrame(frame, text="General", padding=15)
        general_frame.pack(fill="x", pady=10)

        general_text = (
            f"Total de transcripciones: {stats['total_transcriptions']}\n"
            f"Duración total: {stats['total_duration_hours']:.2f} horas\n"
            f"Coste total: ${stats['total_cost']:.2f}\n"
            f"Coste promedio: ${stats['average_cost']:.4f}\n\n"
            f"Primera transcripción: {stats['first_transcription'] or 'N/A'}\n"
            f"Última transcripción: {stats['last_transcription'] or 'N/A'}"
        )

        ttk.Label(
            general_frame,
            text=general_text,
            font=("Segoe UI", 10),
            justify="left"
        ).pack(anchor="w")

        # Modelos usados
        models_frame = ttk.LabelFrame(frame, text="Modelos Usados", padding=15)
        models_frame.pack(fill="x", pady=10)

        for model, count in stats['models_used'].items():
            ttk.Label(
                models_frame,
                text=f"• {model}: {count} veces",
                font=("Segoe UI", 9)
            ).pack(anchor="w")

        # Idiomas detectados
        langs_frame = ttk.LabelFrame(frame, text="Idiomas Detectados", padding=15)
        langs_frame.pack(fill="x", pady=10)

        for lang, count in stats['languages_detected'].items():
            ttk.Label(
                langs_frame,
                text=f"• {lang}: {count} veces",
                font=("Segoe UI", 9)
            ).pack(anchor="w")

        ttk.Button(
            frame,
            text="Cerrar",
            command=window.destroy
        ).pack(pady=20)

    def _export_csv(self):
        """Exportar historial a CSV"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile=f"historial_{dt.datetime.now().strftime('%Y%m%d')}.csv"
        )

        if not file_path:
            return

        if self.history_mgr.export_to_csv(Path(file_path)):
            messagebox.showinfo("Exportado", f"Historial exportado a:\n{file_path}")
        else:
            messagebox.showerror("Error", "No se pudo exportar el historial")

    def _show_context_menu(self, event):
        """Mostrar menú contextual"""
        # Seleccionar item bajo el cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

            # Crear menú
            menu = tk.Menu(self.tree, tearoff=0)
            menu.add_command(label="👁️ Ver completo", command=self._view_full)
            menu.add_command(label="📂 Abrir archivo", command=self._open_file)
            menu.add_command(label="🎵 Abrir audio", command=self._open_audio)
            menu.add_separator()
            menu.add_command(label="🗑️ Eliminar", command=self._delete_selected)

            # Mostrar menú
            menu.post(event.x_root, event.y_root)

    def refresh(self):
        """Refrescar vista del historial"""
        self._load_history()
