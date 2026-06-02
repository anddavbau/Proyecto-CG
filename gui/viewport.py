"""
gui/viewport.py
Widget de visualización: muestra la imagen renderizada en el canvas de tkinter.
Convierte PIL.Image → PhotoImage y la dibuja centrada en el canvas.
"""

import tkinter as tk
from PIL import ImageTk


class Viewport(tk.Canvas):
    """Canvas que muestra el framebuffer renderizado."""

    def __init__(self, parent, width: int, height: int, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg='#1a1a22', highlightthickness=0, **kwargs)
        self._photo = None
        self._img_id = None
        self.render_w = width
        self.render_h = height

    def display(self, pil_image):
        """Muestra una PIL.Image en el canvas."""
        self._photo = ImageTk.PhotoImage(pil_image)
        if self._img_id is None:
            self._img_id = self.create_image(
                self.render_w // 2, self.render_h // 2,
                image=self._photo, anchor='center'
            )
        else:
            self.itemconfig(self._img_id, image=self._photo)

    def show_message(self, text: str):
        """Muestra un mensaje centrado (ej. 'Cargando...')."""
        self.delete('msg')
        self.create_text(
            self.render_w // 2, self.render_h // 2,
            text=text, fill='#aaaacc', font=('Consolas', 13),
            tags='msg'
        )
