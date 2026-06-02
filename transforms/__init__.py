"""
transforms/__init__.py
Construye la matriz modelo (TRS) a partir de parámetros de traslación,
rotación y escala.
"""

import numpy as np
from transforms.translation import translation_matrix
from transforms.rotation import rotation_euler
from transforms.scale import scale_matrix


def build_model_matrix(
    tx: float = 0.0, ty: float = 0.0, tz: float = 0.0,
    rx: float = 0.0, ry: float = 0.0, rz: float = 0.0,
    sx: float = 1.0, sy: float = 1.0, sz: float = 1.0,
) -> np.ndarray:
    """
    Construye la matriz modelo M = T * R * S.
    Los ángulos están en grados.
    """
    T = translation_matrix(tx, ty, tz)
    R = rotation_euler(rx, ry, rz)
    S = scale_matrix(sx, sy, sz)
    return T @ R @ S
