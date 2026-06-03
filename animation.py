"""
animation.py
============
Define y ejecuta la animación del modelo 3D.

- Secuencia de keyframes con transformaciones TRS
- Interpolación suave entre keyframes (lerp / slerp simplificado)
- 5 segundos a 24 fps = 120 frames
- Completamente separado de la interfaz gráfica
"""

import numpy as np
import time
import threading
from typing import Callable


# ════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN DE LA ANIMACIÓN
#  Modifica estos keyframes para cambiar la animación
# ════════════════════════════════════════════════════════════════════

DURATION_SECONDS = 5
FPS              = 24
TOTAL_FRAMES     = DURATION_SECONDS * FPS   # 120 frames

# Cada keyframe define el estado en un tiempo [0.0, 1.0] del total
# t=0.0 → inicio,  t=1.0 → fin
# Transformaciones: tx,ty,tz (traslación), rx,ry,rz (rotación°), scale
KEYFRAMES = [
    # t     tx     ty     tz     rx     ry      rz    scale
    (0.00,  0.0,   0.0,   0.0,   0.0,   0.0,    0.0,  1.0),   # posición inicial
    (0.15,  0.0,   0.3,   0.0,   10.0,  0.0,    0.0,  1.0),   # sube ligeramente
    (0.25,  0.0,   0.0,   0.0,   0.0,   90.0,   0.0,  1.0),   # gira a vista lateral
    (0.40,  0.0,  -0.2,   0.0,   0.0,   180.0,  0.0,  0.85),  # vista trasera, escala baja
    (0.55,  0.0,   0.0,   0.0,  -15.0,  270.0,  0.0,  1.0),   # vista 3/4
    (0.70,  0.3,   0.3,   0.0,   20.0,  320.0,  10.0, 1.2),   # posición elevada + zoom
    (0.85,  0.0,   0.0,   0.0,   0.0,   360.0,  0.0,  1.0),   # vuelta al frente
    (1.00,  0.0,   0.0,   0.0,   0.0,   360.0,  0.0,  1.0),   # reposo final
]


# ════════════════════════════════════════════════════════════════════
#  INTERPOLACIÓN
# ════════════════════════════════════════════════════════════════════

def _lerp(a: float, b: float, t: float) -> float:
    """Interpolación lineal entre a y b."""
    return a + (b - a) * t


def _smoothstep(t: float) -> float:
    """Suaviza la interpolación en los extremos (ease-in/out)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def interpolate_keyframes(keyframes: list, global_t: float) -> dict:
    """
    Dado un tiempo global_t en [0, 1], encuentra los dos keyframes
    vecinos e interpola suavemente todos los parámetros TRS.

    Retorna un dict compatible con build_model_matrix() de transforms.py.
    """
    # Encuentra el segmento correspondiente
    prev = keyframes[0]
    nxt  = keyframes[-1]

    for i in range(len(keyframes) - 1):
        if keyframes[i][0] <= global_t <= keyframes[i + 1][0]:
            prev = keyframes[i]
            nxt  = keyframes[i + 1]
            break

    t_prev, tx0, ty0, tz0, rx0, ry0, rz0, s0 = prev
    t_nxt,  tx1, ty1, tz1, rx1, ry1, rz1, s1 = nxt

    # Normaliza t dentro del segmento
    seg_len = t_nxt - t_prev
    if seg_len < 1e-9:
        local_t = 1.0
    else:
        local_t = (global_t - t_prev) / seg_len

    # Aplica smoothstep para movimiento más natural
    smooth_t = _smoothstep(local_t)

    return {
        'tx':    _lerp(tx0, tx1, smooth_t),
        'ty':    _lerp(ty0, ty1, smooth_t),
        'tz':    _lerp(tz0, tz1, smooth_t),
        'rx':    _lerp(rx0, rx1, smooth_t),
        'ry':    _lerp(ry0, ry1, smooth_t),
        'rz':    _lerp(rz0, rz1, smooth_t),
        'sx':    _lerp(s0,  s1,  smooth_t),
        'sy':    _lerp(s0,  s1,  smooth_t),
        'sz':    _lerp(s0,  s1,  smooth_t),
    }


def get_frame_transforms(frame_index: int,
                          keyframes: list = None,
                          total_frames: int = TOTAL_FRAMES) -> dict:
    """
    Devuelve el dict de transformaciones para el frame dado (0-indexed).

    Parámetros
    ----------
    frame_index  : índice del frame actual [0, total_frames-1]
    keyframes    : lista de keyframes (usa KEYFRAMES por defecto)
    total_frames : duración total en frames

    Retorna dict con tx,ty,tz,rx,ry,rz,sx,sy,sz.
    """
    if keyframes is None:
        keyframes = KEYFRAMES

    global_t = frame_index / max(total_frames - 1, 1)
    return interpolate_keyframes(keyframes, global_t)


# ════════════════════════════════════════════════════════════════════
#  CONTROLADOR DE ANIMACIÓN
# ════════════════════════════════════════════════════════════════════

class AnimationController:
    """
    Controla el estado de la animación y notifica al renderizador
    cuando debe actualizar el frame.

    Uso:
        ctrl = AnimationController(on_frame=mi_callback, fps=24)
        ctrl.play()
        ctrl.pause()
        ctrl.stop()
    """

    def __init__(self,
                 on_frame: Callable[[int, dict], None],
                 on_finish: Callable[[], None] = None,
                 fps: int = FPS,
                 total_frames: int = TOTAL_FRAMES,
                 keyframes: list = None,
                 loop: bool = False):
        """
        Parámetros
        ----------
        on_frame     : callback(frame_idx, transforms_dict) llamado en cada frame.
        on_finish    : callback() llamado cuando termina la animación.
        fps          : frames por segundo objetivo.
        total_frames : número total de frames.
        keyframes    : secuencia de poses (usa KEYFRAMES por defecto).
        loop         : si True repite la animación indefinidamente.
        """
        self.on_frame     = on_frame
        self.on_finish    = on_finish
        self.fps          = fps
        self.total_frames = total_frames
        self.keyframes    = keyframes or KEYFRAMES
        self.loop         = loop

        self._current_frame = 0
        self._playing       = False
        self._thread        = None
        self._lock          = threading.Lock()

    # ── Control ──────────────────────────────────────────────────────

    def play(self):
        """Inicia o reanuda la animación."""
        with self._lock:
            if self._playing:
                return
            self._playing = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def pause(self):
        """Pausa la animación en el frame actual."""
        with self._lock:
            self._playing = False

    def stop(self):
        """Detiene la animación y vuelve al frame 0."""
        with self._lock:
            self._playing = False
            self._current_frame = 0

    def seek(self, frame_index: int):
        """Salta a un frame específico."""
        self._current_frame = max(0, min(frame_index, self.total_frames - 1))
        transforms = get_frame_transforms(self._current_frame, self.keyframes, self.total_frames)
        self.on_frame(self._current_frame, transforms)

    # ── Propiedades ───────────────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def current_frame(self) -> int:
        return self._current_frame

    @property
    def progress(self) -> float:
        """Progreso de la animación en [0.0, 1.0]."""
        return self._current_frame / max(self.total_frames - 1, 1)

    @property
    def current_time_str(self) -> str:
        secs = self._current_frame / self.fps
        total = self.total_frames / self.fps
        return f"{secs:.1f}s / {total:.1f}s"

    # ── Loop interno ──────────────────────────────────────────────────

    def _run(self):
        frame_duration = 1.0 / self.fps

        while self._playing:
            frame_start = time.perf_counter()

            # Si llegamos al final
            if self._current_frame >= self.total_frames:
                if self.loop:
                    self._current_frame = 0
                else:
                    self._playing = False
                    if self.on_finish:
                        self.on_finish()
                    break

            # Calcula transforms para este frame y notifica
            transforms = get_frame_transforms(
                self._current_frame, self.keyframes, self.total_frames
            )
            self.on_frame(self._current_frame, transforms)
            self._current_frame += 1

            # Espera para mantener el FPS objetivo
            elapsed = time.perf_counter() - frame_start
            sleep_time = frame_duration - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
