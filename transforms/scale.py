"""
transforms/scale.py
Genera matrices de escalado 4x4.
"""

import numpy as np


def scale_matrix(sx: float, sy: float, sz: float) -> np.ndarray:
    """
    Retorna la matriz de escalado homogénea 4x4.

    | sx  0   0  0 |
    |  0 sy   0  0 |
    |  0  0  sz  0 |
    |  0  0   0  1 |
    """
    m = np.eye(4, dtype=np.float64)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m


def uniform_scale(s: float) -> np.ndarray:
    """Escalado uniforme en los tres ejes."""
    return scale_matrix(s, s, s)
