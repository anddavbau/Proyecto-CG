"""
transforms/rotation.py
Genera matrices de rotación 4x4 alrededor de los ejes X, Y, Z
y rotación por ángulos de Euler arbitrarios.
"""

import math
import numpy as np


def rotation_x(angle_deg: float) -> np.ndarray:
    """Rotación alrededor del eje X."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([
        [1, 0,  0, 0],
        [0, c, -s, 0],
        [0, s,  c, 0],
        [0, 0,  0, 1],
    ], dtype=np.float64)


def rotation_y(angle_deg: float) -> np.ndarray:
    """Rotación alrededor del eje Y."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([
        [ c, 0, s, 0],
        [ 0, 1, 0, 0],
        [-s, 0, c, 0],
        [ 0, 0, 0, 1],
    ], dtype=np.float64)


def rotation_z(angle_deg: float) -> np.ndarray:
    """Rotación alrededor del eje Z."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([
        [c, -s, 0, 0],
        [s,  c, 0, 0],
        [0,  0, 1, 0],
        [0,  0, 0, 1],
    ], dtype=np.float64)


def rotation_euler(rx: float, ry: float, rz: float) -> np.ndarray:
    """
    Rotación combinada: primero X, luego Y, luego Z.
    Los ángulos están en grados.
    """
    return rotation_z(rz) @ rotation_y(ry) @ rotation_x(rx)


def rotation_axis_angle(axis, angle_deg: float) -> np.ndarray:
    """
    Rotación de `angle_deg` grados alrededor de un eje arbitrario (fórmula de Rodrigues).
    axis: array-like de 3 componentes.
    """
    axis = np.array(axis, dtype=np.float64)
    axis /= np.linalg.norm(axis)
    a = math.radians(angle_deg)
    c = math.cos(a)
    s = math.sin(a)
    t = 1.0 - c
    x, y, z = axis
    m = np.eye(4, dtype=np.float64)
    m[0, 0] = t*x*x + c
    m[0, 1] = t*x*y - s*z
    m[0, 2] = t*x*z + s*y
    m[1, 0] = t*x*y + s*z
    m[1, 1] = t*y*y + c
    m[1, 2] = t*y*z - s*x
    m[2, 0] = t*x*z - s*y
    m[2, 1] = t*y*z + s*x
    m[2, 2] = t*z*z + c
    return m
