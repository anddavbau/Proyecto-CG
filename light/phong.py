"""
light/phong.py
Modelo de iluminación de Phong.
El sombreado de Phong interpola las NORMALES entre vértices y calcula
la iluminación por fragmento (píxel). En nuestra implementación software,
el cálculo se hace por vértice con normal interpolada (aproximación).

Componentes: ambiental + difusa (Lambertiana) + especular (reflexión de Phong).
"""

import numpy as np


class PhongLight:
    """
    Iluminación con reflexión especular de Phong.
    Usa el vector de reflexión R = 2(N·L)N - L para la componente especular.
    """

    def __init__(
        self,
        light_pos=(3.0, 5.0, 5.0),
        light_color=(1.0, 1.0, 1.0),
        ambient=0.1,
        diffuse=0.7,
        specular=0.5,
        shininess=32,
        view_pos=(0.0, 0.0, 5.0),
    ):
        self.light_pos = np.array(light_pos, dtype=np.float64)
        self.light_color = np.array(light_color, dtype=np.float64)
        self.ambient = float(ambient)
        self.diffuse = float(diffuse)
        self.specular = float(specular)
        self.shininess = int(shininess)
        self.view_pos = np.array(view_pos, dtype=np.float64)

    def shade(self, position, normal, base_color) -> tuple:
        """
        Calcula el color Phong en una posición con su normal.
        position  : np.ndarray (3,) - posición en espacio mundo
        normal    : np.ndarray (3,) - normal (se normaliza internamente)
        base_color: (r, g, b) en rango 0-255
        Retorna: (r, g, b) en rango 0-255
        """
        pos = np.array(position, dtype=np.float64)
        N = np.array(normal, dtype=np.float64)
        n_len = np.linalg.norm(N)
        if n_len > 1e-8:
            N /= n_len

        base = np.array([c / 255.0 for c in base_color[:3]], dtype=np.float64)

        # Vector luz
        L = self.light_pos - pos
        L_len = np.linalg.norm(L)
        if L_len > 1e-8:
            L /= L_len

        # Ambiental
        ambient_term = self.ambient * base * self.light_color

        # Difusa
        NdotL = max(0.0, np.dot(N, L))
        diffuse_term = self.diffuse * NdotL * base * self.light_color

        # Especular Phong: R = reflect(-L, N)
        V = self.view_pos - pos
        V_len = np.linalg.norm(V)
        if V_len > 1e-8:
            V /= V_len

        R = 2.0 * np.dot(N, L) * N - L
        R /= max(np.linalg.norm(R), 1e-8)

        RdotV = max(0.0, np.dot(R, V))
        spec_intensity = RdotV ** self.shininess
        specular_term = self.specular * spec_intensity * self.light_color

        color = np.clip(ambient_term + diffuse_term + specular_term, 0.0, 1.0)
        return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
