"""
light/gouraud.py
Modelo de iluminación de Gouraud.
Calcula la intensidad lumínica por vértice interpolando el resultado
a lo largo del triángulo en el rasterizador.

Componentes: ambiental + difusa (Lambertiana) + especular (Phong por vértice).
"""

import numpy as np


class GouraudLight:
    """
    Iluminación calculada POR VÉRTICE.
    El rasterizador interpola los colores resultantes entre vértices.
    """

    def __init__(
        self,
        light_pos=(3.0, 5.0, 5.0),
        light_color=(1.0, 1.0, 1.0),
        ambient=0.15,
        diffuse=0.75,
        specular=0.3,
        shininess=16,
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
        Calcula el color iluminado en un punto del vértice.
        position : np.ndarray (3,) - posición en espacio mundo
        normal   : np.ndarray (3,) - normal normalizada en espacio mundo
        base_color: (r, g, b) en rango 0-255
        Retorna: (r, g, b) en rango 0-255
        """
        pos = np.array(position, dtype=np.float64)
        N = np.array(normal, dtype=np.float64)
        n_len = np.linalg.norm(N)
        if n_len > 1e-8:
            N /= n_len

        base = np.array([c / 255.0 for c in base_color[:3]], dtype=np.float64)

        # Vector hacia la luz
        L = self.light_pos - pos
        L_len = np.linalg.norm(L)
        if L_len > 1e-8:
            L /= L_len

        # Ambiental
        ambient_term = self.ambient * base * self.light_color

        # Difusa (Lambert)
        diff = max(0.0, np.dot(N, L))
        diffuse_term = self.diffuse * diff * base * self.light_color

        # Especular (Phong por vértice)
        V = self.view_pos - pos
        V_len = np.linalg.norm(V)
        if V_len > 1e-8:
            V /= V_len
        R = 2.0 * np.dot(N, L) * N - L
        R_len = np.linalg.norm(R)
        if R_len > 1e-8:
            R /= R_len
        spec = max(0.0, np.dot(R, V)) ** self.shininess
        specular_term = self.specular * spec * self.light_color

        color = np.clip(ambient_term + diffuse_term + specular_term, 0.0, 1.0)
        return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
