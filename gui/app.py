"""
gui/app.py
Orquestador principal: conecta panel, viewport, barra de estado,
pipeline de render y controlador de animación.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.viewport   import Viewport
from gui.panel      import ControlPanel
from gui.statusbar  import StatusBar
from core.renderer  import Renderer
from core.obj_loader import load_obj, center_and_normalize
from transforms     import build_model_matrix
from light          import get_light_model
from animation      import AnimationController, TOTAL_FRAMES, FPS

RENDER_W = 640
RENDER_H = 520
DARK_BG  = '#16161f'
ACCENT   = '#7c6af7'


class App:
    """Ventana principal del renderizador 3D por software."""

    def __init__(self, width=900, height=650, title='3D Renderer', default_model='pyramid.obj'):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.configure(bg=DARK_BG)
        self.root.resizable(False, False)
        self.root.geometry(
            f'{width}x{height}+'
            f'{(self.root.winfo_screenwidth()-width)//2}+'
            f'{(self.root.winfo_screenheight()-height)//2}'
        )

        self._renderer  = Renderer(RENDER_W, RENDER_H)
        self._mesh      = None
        self._texture   = None
        self._rendering = False

        # Animación
        self._anim_controller = AnimationController(
            on_frame  = self._on_anim_frame,
            on_finish = self._on_anim_finish,
            fps       = FPS,
            total_frames = TOTAL_FRAMES,
            loop      = False,
        )


        self._build_ui(width, height)
        self._default_model = default_model
        self._load_default_mesh()

    # ------------------------------------------------------------------ #
    #  UI
    # ------------------------------------------------------------------ #

    def _build_ui(self, w, h):
        self._status = StatusBar(self.root)
        self._status.pack(side='bottom', fill='x')

        self._panel = ControlPanel(
            self.root,
            on_change        = self._request_render,
            on_load_model    = self._load_model_dialog,
            on_load_texture  = self._load_texture_dialog,
            on_anim_play     = self._anim_play,
            on_anim_pause    = self._anim_pause,
            on_anim_stop     = self._anim_stop,
            on_anim_loop     = self._anim_loop_changed,
        )
        self._panel.pack(side='right', fill='y')
        tk.Frame(self.root, bg='#2a2a3a', width=1).pack(side='right', fill='y')

        self._viewport = Viewport(self.root, RENDER_W, RENDER_H)
        self._viewport.pack(side='left', padx=10, pady=10)
        self._viewport.show_message('Cargando modelo por defecto...')

    # ------------------------------------------------------------------ #
    #  Controles de animación
    # ------------------------------------------------------------------ #

    def _anim_play(self):
        """Inicia o reanuda la animación."""
        self._anim_controller.loop = self._panel.get_loop()
        self._anim_controller.play()
        self._panel.set_anim_state(playing=True)

    def _anim_pause(self):
        """Pausa la animación."""
        self._anim_controller.pause()
        self._panel.set_anim_state(playing=False)

    def _anim_stop(self):
        """Detiene y resetea la animación."""
        self._anim_controller.stop()
        self._panel.set_anim_state(playing=False)
        self._panel.set_anim_progress(0, TOTAL_FRAMES, FPS)
        # Renderiza el frame 0 para mostrar la pose inicial
        self._request_render()

    def _anim_loop_changed(self, loop: bool):
        self._anim_controller.loop = loop

    def _on_anim_frame(self, frame_idx: int, transforms: dict):
        """
        Llamado por AnimationController en cada frame.
        Actualiza los sliders y lanza el render en el hilo principal de tkinter.
        """
        # Programa la actualización en el hilo principal de tkinter
        self.root.after(0, self._apply_anim_frame, frame_idx, transforms)

    def _apply_anim_frame(self, frame_idx: int, transforms: dict):
        """Aplica los transforms de la animación y renderiza."""
        self._panel.set_transforms_from_anim(transforms)
        self._panel.set_anim_progress(frame_idx, TOTAL_FRAMES, FPS)
        self._request_render()

    def _on_anim_finish(self):
        """Llamado cuando la animación llega al último frame."""
        self.root.after(0, self._panel.set_anim_state, False)

    # ------------------------------------------------------------------ #
    #  Carga de archivos
    # ------------------------------------------------------------------ #

    def _load_default_mesh(self):
        path = os.path.join(ROOT, 'models', self._default_model)
        if os.path.isfile(path):
            self._load_mesh_from_path(path)
        else:
            models_dir = os.path.join(ROOT, 'models')
            obj_files = []
            if os.path.isdir(models_dir):
                obj_files = [f for f in os.listdir(models_dir) if f.endswith('.obj')]
            if obj_files:
                self._load_mesh_from_path(os.path.join(models_dir, obj_files[0]))
            else:
                self._mesh = self._generate_cube()
                self._panel.set_info('Cubo de ejemplo (sin .obj)')
                self._request_render()

    def _load_model_dialog(self):
        models_dir = os.path.join(ROOT, 'models')
        os.makedirs(models_dir, exist_ok=True)
        path = filedialog.askopenfilename(
            title='Abrir modelo .obj', initialdir=models_dir,
            filetypes=[('Wavefront OBJ', '*.obj'), ('Todos', '*.*')])
        if path:
            self._load_mesh_from_path(path)

    def _load_texture_dialog(self, *_):
        textures_dir = os.path.join(ROOT, 'textures')
        os.makedirs(textures_dir, exist_ok=True)
        path = filedialog.askopenfilename(
            title='Abrir textura', initialdir=textures_dir,
            filetypes=[('Imágenes', '*.png *.jpg *.jpeg *.bmp *.tga'), ('Todos', '*.*')])
        if path:
            try:
                self._texture = Image.open(path).convert('RGB')
                self._panel.set_info(
                    self._panel._info_var.get().split('\n')[0] +
                    f'\nTextura: {os.path.basename(path)}')
                self._request_render()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo cargar la textura:\n{e}')

    def _load_mesh_from_path(self, path: str):
        self._status.set('Cargando modelo...')
        self._viewport.show_message(f'Cargando {os.path.basename(path)}...')
        self.root.update()
        try:
            mesh = load_obj(path)
            mesh = center_and_normalize(mesh)
            self._mesh = mesh
            nv = len(mesh['vertices']); nf = len(mesh['faces'])
            self._panel.set_info(
                f'{os.path.basename(path)}\n{nv:,} vértices  {nf:,} triángulos')
            self._request_render()
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo cargar el modelo:\n{e}')
            self._status.set('Error al cargar modelo')

    # ------------------------------------------------------------------ #
    #  Render
    # ------------------------------------------------------------------ #

    def _request_render(self, clear_texture=False):
        if clear_texture:
            self._texture = None
        if self._mesh is None:
            return
        if self._rendering:
            return
        self._rendering = True
        threading.Thread(target=self._render_thread, daemon=True).start()

    def _render_thread(self):
        try:
            t0 = time.perf_counter()

            tf      = self._panel.get_transforms()
            lp      = self._panel.get_light_params()
            cam     = self._panel.get_camera()
            color   = self._panel.get_color()
            shading = self._panel.get_shading()

            model_mat = build_model_matrix(**tf)
            dist      = cam['dist']
            view_mat  = Renderer.look_at(eye=[0,0,dist], center=[0,0,0], up=[0,1,0])
            proj_mat  = Renderer.perspective_matrix(cam['fov'], RENDER_W/RENDER_H, 0.1, 100.0)

            light_model = get_light_model(
                shading,
                light_pos=lp['light_pos'],
                ambient=lp['ambient'],
                diffuse=lp['diffuse'],
                specular=lp['specular'],
                shininess=lp['shininess'],
                view_pos=(0.0, 0.0, dist),
            )

            image = self._renderer.render_mesh(
                self._mesh, model_mat, view_mat, proj_mat,
                light_model, color,
                texture=self._texture,
                shading_mode=shading if shading != 'flat' else 'flat',
            )

            elapsed_ms = (time.perf_counter() - t0) * 1000
            n_tris = len(self._mesh['faces'])
            self.root.after(0, self._update_ui, image, elapsed_ms, n_tris, shading)
        finally:
            self._rendering = False

    def _update_ui(self, image, elapsed_ms, n_tris, shading):
        self._viewport.display(image)
        self._status.set_render_stats(elapsed_ms, n_tris, shading)

    # ------------------------------------------------------------------ #

    @staticmethod
    def _generate_cube():
        v = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
        faces = [
            [4,5,6,-1,-1,-1,-1,-1,-1],[4,6,7,-1,-1,-1,-1,-1,-1],
            [1,0,3,-1,-1,-1,-1,-1,-1],[1,3,2,-1,-1,-1,-1,-1,-1],
            [0,4,7,-1,-1,-1,-1,-1,-1],[0,7,3,-1,-1,-1,-1,-1,-1],
            [5,1,2,-1,-1,-1,-1,-1,-1],[5,2,6,-1,-1,-1,-1,-1,-1],
            [7,6,2,-1,-1,-1,-1,-1,-1],[7,2,3,-1,-1,-1,-1,-1,-1],
            [0,1,5,-1,-1,-1,-1,-1,-1],[0,5,4,-1,-1,-1,-1,-1,-1],
        ]
        return {'vertices': v, 'normals': [], 'uvs': [], 'faces': faces}

    def run(self):
        self.root.mainloop()
