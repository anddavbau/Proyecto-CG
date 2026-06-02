"""
light/blinn_phong.py
Modelo de iluminación de Blinn-Phong.
Variante del modelo Phong que usa el VECTOR MEDIO (halfway vector) H
entre L y V para calcular la componente especular, lo que resulta más
eficiente y con mejores resultados a ángulos rasantes.

H = normalize(L + V)
especular = (N · H)^shininess
"""

import numpy as np


class BlinnPhongLight:
    """
    Iluminación Blinn-Phong: usa el halfway vector H = normalize(L+V)
    para la reflexión especular, más realista que Phong a ángulos rasantes.
    """

    def __init__(
        self,
        light_pos=(3.0, 5.0, 5.0),
        light_color=(1.0, 1.0, 1.0),
        ambient=0.1,
        diffuse=0.65,
        specular=0.6,
        shininess=64,
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
        Calcula el color Blinn-Phong en una posición con su normal.
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

        # Difusa (Lambertiana)
        NdotL = max(0.0, np.dot(N, L))
        diffuse_term = self.diffuse * NdotL * base * self.light_color

        # Especular Blinn-Phong: H = normalize(L + V)
        V = self.view_pos - pos
        V_len = np.linalg.norm(V)
        if V_len > 1e-8:
            V /= V_len

        H = L + V
        H_len = np.linalg.norm(H)
        if H_len > 1e-8:
            H /= H_len

        NdotH = max(0.0, np.dot(N, H))
        spec_intensity = NdotH ** self.shininess
        specular_term = self.specular * spec_intensity * self.light_color

        color = np.clip(ambient_term + diffuse_term + specular_term, 0.0, 1.0)
        return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))
