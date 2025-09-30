"""
Utilidades para la interfaz de usuario
Componentes reutilizables y helpers para Tkinter
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
import threading


class ProgressDialog:
    """Diálogo de progreso con mensaje y barra"""

    def __init__(self, parent, title: str = "Procesando..."):
        """
        Inicializar diálogo de progreso

        Args:
            parent: Ventana padre
            title: Título del diálogo
        """
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centrar en pantalla
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Frame principal
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)

        # Mensaje
        self.lbl_message = ttk.Label(
            frame,
            text="Iniciando...",
            font=("Segoe UI", 10)
        )
        self.lbl_message.pack(pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(
            frame,
            mode='determinate',
            length=350
        )
        self.progress.pack(pady=10)

        # Label de porcentaje
        self.lbl_percent = ttk.Label(
            frame,
            text="0%",
            font=("Segoe UI", 9)
        )
        self.lbl_percent.pack()

        # Detalles (opcional)
        self.lbl_details = ttk.Label(
            frame,
            text="",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        self.lbl_details.pack(pady=5)

    def update(self, progress: float, message: str = None, details: str = None):
        """
        Actualizar progreso

        Args:
            progress: Progreso de 0 a 100
            message: Mensaje principal (opcional)
            details: Detalles adicionales (opcional)
        """
        self.progress['value'] = progress
        self.lbl_percent.config(text=f"{int(progress)}%")

        if message:
            self.lbl_message.config(text=message)

        if details:
            self.lbl_details.config(text=details)

        self.dialog.update()

    def close(self):
        """Cerrar diálogo"""
        self.dialog.grab_release()
        self.dialog.destroy()


class AsyncProgress:
    """Gestor de progreso para operaciones asíncronas"""

    def __init__(self, callback: Callable[[float, str, str], None]):
        """
        Inicializar gestor de progreso

        Args:
            callback: Función a llamar con (progress, message, details)
        """
        self.callback = callback
        self._current = 0.0
        self._total = 100.0
        self._lock = threading.Lock()

    def set_total(self, total: float):
        """Establecer total de pasos"""
        with self._lock:
            self._total = total

    def update(self, step: float = 1.0, message: str = None, details: str = None):
        """
        Actualizar progreso

        Args:
            step: Incremento (default: 1)
            message: Mensaje (opcional)
            details: Detalles (opcional)
        """
        with self._lock:
            self._current = min(self._current + step, self._total)
            percent = (self._current / self._total) * 100 if self._total > 0 else 0

        self.callback(percent, message or "", details or "")

    def set(self, value: float, message: str = None, details: str = None):
        """
        Establecer progreso absoluto

        Args:
            value: Valor de progreso (0-100)
            message: Mensaje (opcional)
            details: Detalles (opcional)
        """
        with self._lock:
            self._current = min(value, 100)

        self.callback(self._current, message or "", details or "")

    def reset(self):
        """Resetear progreso"""
        with self._lock:
            self._current = 0.0


class StatusBarManager:
    """Gestor de barra de estado con mensajes temporales"""

    def __init__(self, status_label: ttk.Label):
        """
        Inicializar gestor

        Args:
            status_label: Label de la barra de estado
        """
        self.label = status_label
        self._timer_id = None
        self._default_text = "Listo"

    def set_message(self, text: str, duration: int = 0, icon: str = ""):
        """
        Mostrar mensaje en barra de estado

        Args:
            text: Texto a mostrar
            duration: Duración en ms (0 = permanente)
            icon: Icono opcional (ej: "✓", "⚠", "✗")
        """
        # Cancelar timer anterior
        if self._timer_id:
            try:
                self.label.after_cancel(self._timer_id)
            except:
                pass

        # Actualizar texto
        display_text = f"{icon} {text}" if icon else text
        self.label.config(text=display_text)

        # Programar reset si hay duración
        if duration > 0:
            self._timer_id = self.label.after(
                duration,
                lambda: self.label.config(text=self._default_text)
            )

    def set_default(self, text: str):
        """Establecer texto por defecto"""
        self._default_text = text

    def reset(self):
        """Resetear a texto por defecto"""
        self.label.config(text=self._default_text)

    def show_success(self, text: str, duration: int = 3000):
        """Mostrar mensaje de éxito"""
        self.set_message(text, duration, "✓")

    def show_error(self, text: str, duration: int = 5000):
        """Mostrar mensaje de error"""
        self.set_message(text, duration, "✗")

    def show_warning(self, text: str, duration: int = 4000):
        """Mostrar mensaje de advertencia"""
        self.set_message(text, duration, "⚠")

    def show_info(self, text: str, duration: int = 3000):
        """Mostrar mensaje informativo"""
        self.set_message(text, duration, "ℹ")


class ScrollableFrame(ttk.Frame):
    """Frame con scroll automático"""

    def __init__(self, parent, **kwargs):
        """
        Inicializar frame scrolleable

        Args:
            parent: Widget padre
            **kwargs: Argumentos para Frame
        """
        super().__init__(parent, **kwargs)

        # Canvas
        self.canvas = tk.Canvas(self, borderwidth=0, background="#ffffff")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )

        # Frame interno
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configurar scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Scroll con rueda del mouse
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """Manejar scroll con rueda del mouse"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ConfirmDialog:
    """Diálogo de confirmación personalizado"""

    def __init__(self, parent, title: str, message: str,
                 icon: str = "⚠", confirm_text: str = "Sí",
                 cancel_text: str = "No"):
        """
        Crear diálogo de confirmación

        Args:
            parent: Ventana padre
            title: Título
            message: Mensaje
            icon: Icono
            confirm_text: Texto del botón confirmar
            cancel_text: Texto del botón cancelar
        """
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("350x150")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Centrar
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (150 // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Frame principal
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill="both", expand=True)

        # Icono y mensaje
        msg_frame = ttk.Frame(frame)
        msg_frame.pack(fill="x", pady=10)

        ttk.Label(
            msg_frame,
            text=icon,
            font=("Segoe UI", 24)
        ).pack(side="left", padx=10)

        ttk.Label(
            msg_frame,
            text=message,
            font=("Segoe UI", 10),
            wraplength=250
        ).pack(side="left", fill="x", expand=True)

        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame,
            text=confirm_text,
            command=self._confirm
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text=cancel_text,
            command=self._cancel
        ).pack(side="left", padx=5)

        # Esperar resultado
        self.dialog.wait_window()

    def _confirm(self):
        """Confirmar"""
        self.result = True
        self.dialog.destroy()

    def _cancel(self):
        """Cancelar"""
        self.result = False
        self.dialog.destroy()

    @staticmethod
    def ask(parent, title: str, message: str) -> bool:
        """
        Mostrar diálogo y retornar resultado

        Args:
            parent: Ventana padre
            title: Título
            message: Mensaje

        Returns:
            bool: True si confirmó, False si canceló
        """
        dialog = ConfirmDialog(parent, title, message)
        return dialog.result


def format_duration(seconds: float) -> str:
    """
    Formatear duración en formato legible

    Args:
        seconds: Duración en segundos

    Returns:
        str: Duración formateada
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def format_cost(cost: float) -> str:
    """
    Formatear coste en formato legible

    Args:
        cost: Coste en USD

    Returns:
        str: Coste formateado
    """
    if cost == 0:
        return "GRATIS"
    elif cost < 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.2f}"


def format_filesize(size_bytes: int) -> str:
    """
    Formatear tamaño de archivo

    Args:
        size_bytes: Tamaño en bytes

    Returns:
        str: Tamaño formateado
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"
