"""
gui/panel.py
Panel lateral de controles: sliders de transformación, selector de modelo,
textura, color, modo de sombreado, parámetros de luz y controles de animación.
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import os

DARK_BG   = '#16161f'
PANEL_BG  = '#1e1e2a'
ACCENT    = '#7c6af7'
TEXT_COL  = '#d0d0e8'
LABEL_COL = '#8888aa'
ENTRY_BG  = '#2a2a3a'
GREEN     = '#4caf82'
RED       = '#e05a5a'


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

    def __init__(self, parent, on_change, on_load_model, on_load_texture,
                 on_anim_play=None, on_anim_pause=None, on_anim_stop=None,
                 on_anim_loop=None, **kw):
        super().__init__(parent, bg=PANEL_BG, width=240, **kw)
        self.pack_propagate(False)
        self.on_change = on_change
        self._on_anim_play  = on_anim_play
        self._on_anim_pause = on_anim_pause
        self._on_anim_stop  = on_anim_stop
        self._on_anim_loop  = on_anim_loop
        self._build(on_load_model, on_load_texture)

    # ------------------------------------------------------------------ #

    def _build(self, on_load_model, on_load_texture):
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

        # ── Animación ───────────────────────────────────────────────────
        _section(p, '▸ Animación')
        anim_frame = tk.Frame(p, bg=PANEL_BG)
        anim_frame.pack(fill='x', padx=10, pady=4)

        # Botones Play / Pause / Stop en fila
        btn_row = tk.Frame(anim_frame, bg=PANEL_BG)
        btn_row.pack(fill='x', pady=2)

        self._btn_play = tk.Button(
            btn_row, text='▶  Play', command=self._anim_play,
            bg=GREEN, fg='white', font=('Consolas', 8, 'bold'),
            relief='flat', cursor='hand2', width=8)
        self._btn_play.pack(side='left', padx=(0, 3))

        self._btn_pause = tk.Button(
            btn_row, text='⏸ Pause', command=self._anim_pause,
            bg=ENTRY_BG, fg=TEXT_COL, font=('Consolas', 8),
            relief='flat', cursor='hand2', width=8)
        self._btn_pause.pack(side='left', padx=3)

        self._btn_stop = tk.Button(
            btn_row, text='⏹ Stop', command=self._anim_stop,
            bg=RED, fg='white', font=('Consolas', 8),
            relief='flat', cursor='hand2', width=8)
        self._btn_stop.pack(side='left', padx=(3, 0))

        # Loop checkbox
        loop_row = tk.Frame(anim_frame, bg=PANEL_BG)
        loop_row.pack(fill='x', pady=2)
        self._loop_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            loop_row, text='Loop', variable=self._loop_var,
            command=self._anim_loop_toggle,
            bg=PANEL_BG, fg=TEXT_COL, selectcolor=DARK_BG,
            activebackground=PANEL_BG, font=('Consolas', 8),
            highlightthickness=0, cursor='hand2',
        ).pack(side='left')

        # Barra de progreso + tiempo
        prog_row = tk.Frame(anim_frame, bg=PANEL_BG)
        prog_row.pack(fill='x', pady=(4, 0))
        self._anim_progress = ttk.Progressbar(
            prog_row, orient='horizontal', length=200, mode='determinate')
        self._anim_progress.pack(fill='x', pady=2)

        self._anim_time_var = tk.StringVar(value='0.0s / 5.0s  |  frame 0/120')
        tk.Label(anim_frame, textvariable=self._anim_time_var,
                 bg=PANEL_BG, fg=ACCENT, font=('Consolas', 8)).pack(anchor='w')

        # Estado
        self._anim_status_var = tk.StringVar(value='● Detenida')
        tk.Label(anim_frame, textvariable=self._anim_status_var,
                 bg=PANEL_BG, fg=LABEL_COL, font=('Consolas', 8, 'italic')).pack(anchor='w')

        # ── Sombreado ────────────────────────────────────────────────────
        _section(p, '▸ Sombreado')
        self._light_vars = {
            'gouraud':     tk.BooleanVar(value=False),
            'phong':       tk.BooleanVar(value=True),
            'blinn-phong': tk.BooleanVar(value=False),
        }
        light_labels = {'gouraud': 'Gouraud', 'phong': 'Phong', 'blinn-phong': 'Blinn-Phong'}
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
        self._shading_active_var = tk.StringVar(value='activo: phong')
        tk.Label(shading_frame, textvariable=self._shading_active_var,
                 bg=PANEL_BG, fg=ACCENT, font=('Consolas', 8, 'italic')).pack(anchor='w', pady=(4,0))

        # ── Color ───────────────────────────────────────────────────────
        _section(p, '▸ Color base')
        self._color = (250, 250, 250)
        self._color_preview = tk.Label(p, bg=self._rgb_hex(self._color),
                                       height=2, cursor='hand2')
        self._color_preview.pack(fill='x', padx=10, pady=3)
        self._color_preview.bind('<Button-1>', self._pick_color)

        # ── Traslación ──────────────────────────────────────────────────
        _section(p, '▸ Traslación')
        self.tx = tk.DoubleVar(value=0.0)
        self.ty = tk.DoubleVar(value=0.0)
        self.tz = tk.DoubleVar(value=0.0)
        self._sl_tx = _slider(p, 'X', -3, 3, self.tx, self._fire)
        self._sl_ty = _slider(p, 'Y', -3, 3, self.ty, self._fire)
        self._sl_tz = _slider(p, 'Z', -3, 3, self.tz, self._fire)

        # ── Rotación ────────────────────────────────────────────────────
        _section(p, '▸ Rotación')
        self.rx = tk.DoubleVar(value=0.0)
        self.ry = tk.DoubleVar(value=0.0)
        self.rz = tk.DoubleVar(value=0.0)
        self._sl_rx = _slider(p, 'X°', -180, 180, self.rx, self._fire, resolution=1)
        self._sl_ry = _slider(p, 'Y°', -180, 180, self.ry, self._fire, resolution=1)
        self._sl_rz = _slider(p, 'Z°', -180, 180, self.rz, self._fire, resolution=1)

        # ── Escala ──────────────────────────────────────────────────────
        _section(p, '▸ Escala')
        self.scale = tk.DoubleVar(value=1.0)
        self._sl_scale = _slider(p, 'S', 0.05, 3.0, self.scale, self._fire)

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
    #  Callbacks de animación
    # ------------------------------------------------------------------ #

    def _anim_play(self):
        if self._on_anim_play:
            self._on_anim_play()

    def _anim_pause(self):
        if self._on_anim_pause:
            self._on_anim_pause()

    def _anim_stop(self):
        if self._on_anim_stop:
            self._on_anim_stop()

    def _anim_loop_toggle(self):
        if self._on_anim_loop:
            self._on_anim_loop(self._loop_var.get())

    # ------------------------------------------------------------------ #
    #  API pública para actualizar UI desde App
    # ------------------------------------------------------------------ #

    def set_anim_state(self, playing: bool):
        """Cambia el color del botón Play según el estado."""
        if playing:
            self._btn_play.config(bg='#3a7a5a')
            self._anim_status_var.set('▶ Reproduciendo...')
        else:
            self._btn_play.config(bg=GREEN)
            self._anim_status_var.set('⏸ Pausada' if self._anim_progress['value'] > 0
                                      else '● Detenida')

    def set_anim_progress(self, frame: int, total: int, fps: int):
        """Actualiza la barra de progreso y el tiempo."""
        pct = (frame / max(total - 1, 1)) * 100
        self._anim_progress['value'] = pct
        secs = frame / fps
        total_secs = total / fps
        self._anim_time_var.set(f'{secs:.1f}s / {total_secs:.1f}s  |  frame {frame}/{total}')

    def set_transforms_from_anim(self, tf: dict):
        """
        Actualiza los sliders con los valores de la animación.
        Desactiva el callback temporalmente para no disparar un render manual.
        """
        self.tx.set(round(tf['tx'], 3))
        self.ty.set(round(tf['ty'], 3))
        self.tz.set(round(tf['tz'], 3))
        self.rx.set(round(tf['rx'], 1))
        self.ry.set(round(tf['ry'], 1))
        self.rz.set(round(tf['rz'], 1))
        self.scale.set(round(tf['sx'], 3))

    # ------------------------------------------------------------------ #

    def _fire(self, *_):
        self.on_change()

    def _on_light_toggle(self):
        active = [k for k, v in self._light_vars.items() if v.get()]
        if not active:
            self._shading_active_var.set('activo: color plano')
        elif len(active) == 1:
            self._shading_active_var.set(f'activo: {active[0]}')
        else:
            priority = ['blinn-phong', 'phong', 'gouraud']
            chosen = next(k for k in priority if k in active)
            self._shading_active_var.set(f'activo: {chosen}  (+{len(active)-1})')
        self._fire()

    def _pick_color(self, *_):
        rgb, hex_color = colorchooser.askcolor(
            color=self._rgb_hex(self._color), title='Seleccionar color base')
        if rgb:
            self._color = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
            self._color_preview.config(bg=self._rgb_hex(self._color))
            self._fire()

    def _clear_texture(self):
        self.on_change(clear_texture=True)

    @staticmethod
    def _rgb_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    # ── Getters ─────────────────────────────────────────────────────────

    def get_color(self):
        return self._color

    def get_shading(self):
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
        return {'dist': self.cam_dist.get(), 'fov': self.fov.get()}

    def set_info(self, text: str):
        self._info_var.set(text)

    def get_loop(self) -> bool:
        return self._loop_var.get()
