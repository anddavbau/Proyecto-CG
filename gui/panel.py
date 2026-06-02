"""
gui/panel.py
Panel lateral de controles: sliders de transformación, selector de modelo,
textura, color, modo de sombreado y parámetros de luz.
"""

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import os


DARK_BG   = '#16161f'
PANEL_BG  = '#1e1e2a'
ACCENT    = '#7c6af7'
TEXT_COL  = '#d0d0e8'
LABEL_COL = '#8888aa'
ENTRY_BG  = '#2a2a3a'


def _label(parent, text, **kw):
    return tk.Label(parent, text=text, bg=PANEL_BG, fg=LABEL_COL,
                    font=('Consolas', 8), **kw)


def _section(parent, title):
    frame = tk.Frame(parent, bg=PANEL_BG)
    frame.pack(fill='x', padx=8, pady=(10, 2))
    tk.Label(frame, text=title.upper(), bg=PANEL_BG, fg=ACCENT,
             font=('Consolas', 8, 'bold')).pack(anchor='w')
    tk.Frame(parent, bg=ACCENT, height=1).pack(fill='x', padx=8, pady=(0, 4))
    return frame


def _slider(parent, label, from_, to, var, callback, resolution=0.01):
    row = tk.Frame(parent, bg=PANEL_BG)
    row.pack(fill='x', padx=10, pady=1)
    tk.Label(row, text=label, bg=PANEL_BG, fg=TEXT_COL,
             font=('Consolas', 8), width=4, anchor='w').pack(side='left')
    sl = tk.Scale(
        row, from_=from_, to=to, orient='horizontal', variable=var,
        resolution=resolution, command=callback,
        bg=PANEL_BG, fg=TEXT_COL, troughcolor=ENTRY_BG,
        activebackground=ACCENT, highlightthickness=0,
        sliderlength=12, length=160, bd=0
    )
    sl.pack(side='left', fill='x', expand=True)
    val_lbl = tk.Label(row, textvariable=var, bg=PANEL_BG, fg=ACCENT,
                       font=('Consolas', 8), width=6)
    val_lbl.pack(side='right')
    return sl


class ControlPanel(tk.Frame):
    """Panel lateral con todos los controles de la escena."""

    def __init__(self, parent, on_change, on_load_model, on_load_texture, **kw):
        super().__init__(parent, bg=PANEL_BG, width=240, **kw)
        self.pack_propagate(False)
        self.on_change = on_change
        self._build(on_load_model, on_load_texture)

    # ------------------------------------------------------------------ #

    def _build(self, on_load_model, on_load_texture):
        # Scroll
        canvas = tk.Canvas(self, bg=PANEL_BG, highlightthickness=0)
        sb = tk.Scrollbar(self, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        self._inner = tk.Frame(canvas, bg=PANEL_BG)
        self._win_id = canvas.create_window((0, 0), window=self._inner, anchor='nw')
        self._inner.bind('<Configure>', lambda e: canvas.configure(
            scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(
            self._win_id, width=e.width))
        canvas.bind_all('<MouseWheel>', lambda e: canvas.yview_scroll(
            -1 if e.delta > 0 else 1, 'units'))

        p = self._inner

        # ── Título ──────────────────────────────────────────────────────
        tk.Label(p, text='⬡  3D RENDERER', bg=PANEL_BG, fg=ACCENT,
                 font=('Consolas', 11, 'bold')).pack(pady=(14, 2))
        tk.Label(p, text='Software Rasterizer', bg=PANEL_BG, fg=LABEL_COL,
                 font=('Consolas', 8)).pack()

        # ── Modelo y textura ────────────────────────────────────────────
        _section(p, '▸ Archivo')

        btn_frame = tk.Frame(p, bg=PANEL_BG)
        btn_frame.pack(fill='x', padx=10, pady=3)
        tk.Button(btn_frame, text='Cargar modelo .obj', command=on_load_model,
                  bg=ACCENT, fg='white', font=('Consolas', 8, 'bold'),
                  relief='flat', cursor='hand2', activebackground='#9a8fff',
                  activeforeground='white').pack(fill='x', pady=2)
        tk.Button(btn_frame, text='Cargar textura', command=on_load_texture,
                  bg=ENTRY_BG, fg=TEXT_COL, font=('Consolas', 8),
                  relief='flat', cursor='hand2').pack(fill='x', pady=2)
        tk.Button(btn_frame, text='Quitar textura', command=self._clear_texture,
                  bg=ENTRY_BG, fg=LABEL_COL, font=('Consolas', 8),
                  relief='flat', cursor='hand2').pack(fill='x', pady=2)

        # ── Sombreado ────────────────────────────────────────────────────
        _section(p, '▸ Sombreado')

        # Cada tipo de iluminación es un checkbox independiente.
        # Si ninguno está activo se usa color plano puro.
        self._light_vars = {
            'gouraud':     tk.BooleanVar(value=False),
            'phong':       tk.BooleanVar(value=True),
            'blinn-phong': tk.BooleanVar(value=False),
        }
        light_labels = {
            'gouraud':     'Gouraud',
            'phong':       'Phong',
            'blinn-phong': 'Blinn-Phong',
        }

        shading_frame = tk.Frame(p, bg=PANEL_BG)
        shading_frame.pack(fill='x', padx=10, pady=2)

        for key, var in self._light_vars.items():
            row = tk.Frame(shading_frame, bg=PANEL_BG)
            row.pack(fill='x', pady=1)
            tk.Checkbutton(
                row, text=light_labels[key], variable=var,
                command=self._on_light_toggle,
                bg=PANEL_BG, fg=TEXT_COL, selectcolor=DARK_BG,
                activebackground=PANEL_BG, font=('Consolas', 8),
                highlightthickness=0, cursor='hand2',
            ).pack(side='left')

        # Indicador del modo activo resultante
        self._shading_active_var = tk.StringVar(value='activo: phong')
        tk.Label(shading_frame, textvariable=self._shading_active_var,
                 bg=PANEL_BG, fg=ACCENT, font=('Consolas', 8, 'italic'),
                 ).pack(anchor='w', pady=(4, 0))

        # ── Color ───────────────────────────────────────────────────────
        _section(p, '▸ Color base')
        self._color = (200, 200, 200)
        self._color_preview = tk.Label(p, bg=self._rgb_hex(self._color),
                                       height=2, cursor='hand2')
        self._color_preview.pack(fill='x', padx=10, pady=3)
        self._color_preview.bind('<Button-1>', self._pick_color)

        # ── Traslación ──────────────────────────────────────────────────
        _section(p, '▸ Traslación')
        self.tx = tk.DoubleVar(value=0.0)
        self.ty = tk.DoubleVar(value=0.0)
        self.tz = tk.DoubleVar(value=0.0)
        _slider(p, 'X', -3, 3, self.tx, self._fire)
        _slider(p, 'Y', -3, 3, self.ty, self._fire)
        _slider(p, 'Z', -3, 3, self.tz, self._fire)

        # ── Rotación ────────────────────────────────────────────────────
        _section(p, '▸ Rotación')
        self.rx = tk.DoubleVar(value=0.0)
        self.ry = tk.DoubleVar(value=0.0)
        self.rz = tk.DoubleVar(value=0.0)
        _slider(p, 'X°', -180, 180, self.rx, self._fire, resolution=1)
        _slider(p, 'Y°', -180, 180, self.ry, self._fire, resolution=1)
        _slider(p, 'Z°', -180, 180, self.rz, self._fire, resolution=1)

        # ── Escala ──────────────────────────────────────────────────────
        _section(p, '▸ Escala')
        self.scale = tk.DoubleVar(value=1.0)
        _slider(p, 'S', 0.05, 3.0, self.scale, self._fire)

        # ── Luz ─────────────────────────────────────────────────────────
        _section(p, '▸ Luz')
        self.lx = tk.DoubleVar(value=3.0)
        self.ly = tk.DoubleVar(value=5.0)
        self.lz = tk.DoubleVar(value=5.0)
        self.ambient   = tk.DoubleVar(value=0.1)
        self.diffuse   = tk.DoubleVar(value=0.7)
        self.specular  = tk.DoubleVar(value=0.5)
        self.shininess = tk.IntVar(value=32)
        _slider(p, 'Lx', -8, 8, self.lx, self._fire)
        _slider(p, 'Ly', -8, 8, self.ly, self._fire)
        _slider(p, 'Lz', -8, 8, self.lz, self._fire)
        _slider(p, 'Amb', 0, 1, self.ambient,  self._fire)
        _slider(p, 'Dif', 0, 1, self.diffuse,  self._fire)
        _slider(p, 'Esp', 0, 1, self.specular, self._fire)
        _slider(p, 'Shi', 1, 256, self.shininess, self._fire, resolution=1)

        # ── Cámara ──────────────────────────────────────────────────────
        _section(p, '▸ Cámara')
        self.cam_dist = tk.DoubleVar(value=4.0)
        self.fov      = tk.DoubleVar(value=60.0)
        _slider(p, 'Dist', 1.0, 15.0, self.cam_dist, self._fire)
        _slider(p, 'FOV',  20,  120,  self.fov,      self._fire, resolution=1)

        # ── Info ─────────────────────────────────────────────────────────
        _section(p, '▸ Info')
        self._info_var = tk.StringVar(value='Sin modelo cargado')
        tk.Label(p, textvariable=self._info_var, bg=PANEL_BG, fg=LABEL_COL,
                 font=('Consolas', 8), wraplength=210, justify='left').pack(
                 padx=10, pady=(0, 20), anchor='w')

    # ------------------------------------------------------------------ #

    def _fire(self, *_):
        self.on_change()

    def _on_light_toggle(self):
        """Actualiza el indicador de modo activo y dispara el re-render."""
        active = [k for k, v in self._light_vars.items() if v.get()]
        if not active:
            self._shading_active_var.set('activo: color plano')
        elif len(active) == 1:
            self._shading_active_var.set(f'activo: {active[0]}')
        else:
            # Cuando varios están activos se usa el primero en orden de prioridad
            priority = ['blinn-phong', 'phong', 'gouraud']
            chosen = next(k for k in priority if k in active)
            self._shading_active_var.set(f'activo: {chosen}  (+{len(active)-1})')
        self._fire()

    def _pick_color(self, *_):
        rgb, hex_color = colorchooser.askcolor(
            color=self._rgb_hex(self._color), title='Seleccionar color base'
        )
        if rgb:
            self._color = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._color_preview.config(bg=self._rgb_hex(self._color))
            self._fire()

    def _clear_texture(self):
        self.on_change(clear_texture=True)

    @staticmethod
    def _rgb_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    # ── Getters públicos ────────────────────────────────────────────────

    def get_color(self):
        return self._color

    def get_shading(self):
        """
        Devuelve el modo de sombreado a usar según los checkboxes activos.
        Prioridad cuando hay varios activos: blinn-phong > phong > gouraud.
        Si ninguno está activo, devuelve 'flat' (color plano puro).
        """
        priority = ['blinn-phong', 'phong', 'gouraud']
        for mode in priority:
            if self._light_vars[mode].get():
                return mode
        return 'flat'

    def get_transforms(self):
        return {
            'tx': self.tx.get(), 'ty': self.ty.get(), 'tz': self.tz.get(),
            'rx': self.rx.get(), 'ry': self.ry.get(), 'rz': self.rz.get(),
            'sx': self.scale.get(), 'sy': self.scale.get(), 'sz': self.scale.get(),
        }

    def get_light_params(self):
        return {
            'light_pos':  (self.lx.get(), self.ly.get(), self.lz.get()),
            'ambient':    self.ambient.get(),
            'diffuse':    self.diffuse.get(),
            'specular':   self.specular.get(),
            'shininess':  self.shininess.get(),
        }

    def get_camera(self):
        return {
            'dist': self.cam_dist.get(),
            'fov':  self.fov.get(),
        }

    def set_info(self, text: str):
        self._info_var.set(text)
