"""
gui/statusbar.py
Barra de estado inferior: muestra tiempo de render, estadísticas de malla
y modo activo.
"""

import tkinter as tk
import time


DARK_BG  = '#0f0f18'
ACCENT   = '#7c6af7'
TEXT_COL = '#888899'


class StatusBar(tk.Frame):
    """Barra de estado en la parte inferior de la ventana."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=DARK_BG, height=24, **kw)
        self.pack_propagate(False)

        self._left  = tk.Label(self, text='Listo', bg=DARK_BG, fg=TEXT_COL,
                               font=('Consolas', 8), anchor='w')
        self._left.pack(side='left', padx=10)

        self._right = tk.Label(self, text='', bg=DARK_BG, fg=ACCENT,
                               font=('Consolas', 8), anchor='e')
        self._right.pack(side='right', padx=10)

    def set(self, left_text: str, right_text: str = ''):
        self._left.config(text=left_text)
        self._right.config(text=right_text)

    def set_render_stats(self, elapsed_ms: float, triangles: int, mode: str):
        self._left.config(
            text=f'Modo: {mode}  |  Triángulos: {triangles:,}'
        )
        self._right.config(text=f'{elapsed_ms:.0f} ms')
