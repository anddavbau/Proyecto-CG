"""
transforms/translation.py
Genera matrices de traslación 4x4.
"""

import numpy as np


def translation_matrix(tx: float, ty: float, tz: float) -> np.ndarray:
    """
    Retorna la matriz de traslación homogénea 4x4.
    
    | 1  0  0  tx |
    | 0  1  0  ty |
    | 0  0  1  tz |
    | 0  0  0   1 |
    """
    m = np.eye(4, dtype=np.float64)
    m[0, 3] = tx
    m[1, 3] = ty
    m[2, 3] = tz
    return m
