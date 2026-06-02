"""
core/renderer.py
Pipeline de renderizado software: framebuffer, z-buffer, rasterización de triángulos.
No utiliza OpenGL ni ninguna API gráfica de bajo nivel.
"""

import math
import numpy as np
from PIL import Image


class Framebuffer:
    """Buffer de píxeles donde se dibuja la escena."""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.color_buffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.z_buffer = np.full((height, width), float('inf'), dtype=np.float64)

    def clear(self, bg_color=(30, 30, 35)):
        self.color_buffer[:] = bg_color
        self.z_buffer[:] = float('inf')

    def set_pixel(self, x: int, y: int, z: float, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            if z < self.z_buffer[y, x]:
                self.z_buffer[y, x] = z
                self.color_buffer[y, x] = color

    def to_image(self) -> Image.Image:
        return Image.fromarray(self.color_buffer, 'RGB')


class Renderer:
    """
    Rasterizador de triángulos por software.
    Implementa la transformación MVP, recorte y rasterización con z-buffer.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.fb = Framebuffer(width, height)

    def resize(self, width: int, height: int):
        self.width = width
        self.height = height
        self.fb = Framebuffer(width, height)

    # ------------------------------------------------------------------ #
    # Matrices de transformación                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def perspective_matrix(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
        fov = math.radians(fov_deg)
        f = 1.0 / math.tan(fov / 2.0)
        nf = near - far
        return np.array([
            [f / aspect, 0,               0,                    0],
            [0,          f,               0,                    0],
            [0,          0, (far + near) / nf, (2*far*near) / nf],
            [0,          0,              -1,                    0],
        ], dtype=np.float64)

    @staticmethod
    def look_at(eye, center, up) -> np.ndarray:
        eye = np.array(eye, dtype=np.float64)
        center = np.array(center, dtype=np.float64)
        up = np.array(up, dtype=np.float64)
        f = center - eye
        f /= np.linalg.norm(f)
        s = np.cross(f, up)
        s /= np.linalg.norm(s)
        u = np.cross(s, f)
        m = np.eye(4, dtype=np.float64)
        m[0, :3] = s
        m[1, :3] = u
        m[2, :3] = -f
        m[0, 3] = -np.dot(s, eye)
        m[1, 3] = -np.dot(u, eye)
        m[2, 3] = np.dot(f, eye)
        return m

    # ------------------------------------------------------------------ #
    # Rasterización                                                        #
    # ------------------------------------------------------------------ #

    def _to_screen(self, ndc_x: float, ndc_y: float):
        sx = int((ndc_x + 1.0) * 0.5 * self.width)
        sy = int((1.0 - (ndc_y + 1.0) * 0.5) * self.height)
        return sx, sy

    @staticmethod
    def _edge(a, b, p):
        return (p[0] - a[0]) * (b[1] - a[1]) - (p[1] - a[1]) * (b[0] - a[0])

    def draw_triangle(self, v0, v1, v2, color0, color1, color2,
                      uv0=None, uv1=None, uv2=None, texture=None):
        """
        Rasteriza un triángulo con interpolación de color (Gouraud) o textura.
        v0/v1/v2: (x, y, z, w) en clip-space ya dividido por w (NDC).
        color0..2: tupla RGB por vértice.
        """
        w = self.width
        h = self.height

        # NDC → píxel
        def ndc2px(v):
            px = int((v[0] + 1.0) * 0.5 * w)
            py = int((1.0 - (v[1] + 1.0) * 0.5) * h)
            return px, py

        p0 = ndc2px(v0)
        p1 = ndc2px(v1)
        p2 = ndc2px(v2)

        # Bounding box
        min_x = max(0, min(p0[0], p1[0], p2[0]))
        max_x = min(w - 1, max(p0[0], p1[0], p2[0]))
        min_y = max(0, min(p0[1], p1[1], p2[1]))
        max_y = min(h - 1, max(p0[1], p1[1], p2[1]))

        if min_x > max_x or min_y > max_y:
            return

        # Área del triángulo en 2D
        area = self._edge(p0, p1, p2)
        if abs(area) < 1e-6:
            return

        z0, z1, z2 = v0[2], v1[2], v2[2]

        # Textura como array numpy para acceso rápido
        tex_arr = None
        tex_w, tex_h = 1, 1
        if texture is not None and uv0 is not None:
            tex_arr = np.array(texture, dtype=np.uint8)
            tex_h, tex_w = tex_arr.shape[:2]

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                p = (px, py)
                w0 = self._edge(p1, p2, p)
                w1 = self._edge(p2, p0, p)
                w2 = self._edge(p0, p1, p)

                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    # Coordenadas baricéntricas
                    l0 = w0 / area
                    l1 = w1 / area
                    l2 = w2 / area

                    # Interpolación de profundidad
                    z = l0 * z0 + l1 * z1 + l2 * z2

                    if z >= self.fb.z_buffer[py, px]:
                        continue

                    # Color o textura
                    if tex_arr is not None:
                        u = l0 * uv0[0] + l1 * uv1[0] + l2 * uv2[0]
                        v = l0 * uv0[1] + l1 * uv1[1] + l2 * uv2[1]
                        tx = int(u * tex_w) % tex_w
                        ty = int((1.0 - v) * tex_h) % tex_h
                        pixel_color = tuple(tex_arr[ty, tx, :3])
                    else:
                        r = int(l0 * color0[0] + l1 * color1[0] + l2 * color2[0])
                        g = int(l0 * color0[1] + l1 * color1[1] + l2 * color2[1])
                        b = int(l0 * color0[2] + l1 * color1[2] + l2 * color2[2])
                        pixel_color = (
                            max(0, min(255, r)),
                            max(0, min(255, g)),
                            max(0, min(255, b)),
                        )

                    self.fb.z_buffer[py, px] = z
                    self.fb.color_buffer[py, px] = pixel_color

    def render_mesh(self, mesh, model_matrix, view_matrix, proj_matrix,
                    light_model, flat_color, texture=None, shading_mode='flat'):
        """
        Transforma y rasteriza todas las caras del mesh.
        """
        self.fb.clear()
        mvp = proj_matrix @ view_matrix @ model_matrix

        verts = mesh['vertices']       # list of (x,y,z)
        faces = mesh['faces']          # list of (i,j,k, [uv...])
        normals = mesh.get('normals', None)
        uvs = mesh.get('uvs', None)

        # Transformar todos los vértices
        def transform(v):
            hv = np.array([v[0], v[1], v[2], 1.0])
            clip = mvp @ hv
            if abs(clip[3]) < 1e-7:
                return None
            ndc = clip / clip[3]
            return ndc  # (x,y,z,w)

        transformed = [transform(v) for v in verts]

        for face in faces:
            i0, i1, i2 = face[0], face[1], face[2]
            ndc0 = transformed[i0]
            ndc1 = transformed[i1]
            ndc2 = transformed[i2]

            if ndc0 is None or ndc1 is None or ndc2 is None:
                continue

            # Clipping básico en NDC
            for ndc in (ndc0, ndc1, ndc2):
                if not (-1.5 <= ndc[0] <= 1.5 and -1.5 <= ndc[1] <= 1.5 and -1 <= ndc[2] <= 1):
                    break
            else:
                pass  # dentro del frustum, continuar

            # Normales para iluminación
            v0_world = np.array([verts[i0][0], verts[i0][1], verts[i0][2], 1.0])
            v1_world = np.array([verts[i1][0], verts[i1][1], verts[i1][2], 1.0])
            v2_world = np.array([verts[i2][0], verts[i2][1], verts[i2][2], 1.0])

            # Normal de la cara
            edge1 = v1_world[:3] - v0_world[:3]
            edge2 = v2_world[:3] - v0_world[:3]
            face_normal = np.cross(edge1, edge2)
            n = np.linalg.norm(face_normal)
            if n > 1e-8:
                face_normal /= n
            else:
                continue

            # Back-face culling
            view_dir = np.array([0.0, 0.0, 1.0])
            if np.dot(face_normal, view_dir) < 0:
                continue

            # Calcular colores por vértice según modelo de iluminación
            if shading_mode == 'flat':
                center = (v0_world[:3] + v1_world[:3] + v2_world[:3]) / 3.0
                c = light_model.shade(center, face_normal, flat_color)
                c0 = c1 = c2 = c
            elif shading_mode in ('gouraud', 'phong', 'blinn-phong'):
                n0 = np.array(normals[i0]) if normals and i0 < len(normals) else face_normal
                n1 = np.array(normals[i1]) if normals and i1 < len(normals) else face_normal
                n2 = np.array(normals[i2]) if normals and i2 < len(normals) else face_normal
                c0 = light_model.shade(v0_world[:3], n0, flat_color)
                c1 = light_model.shade(v1_world[:3], n1, flat_color)
                c2 = light_model.shade(v2_world[:3], n2, flat_color)
            else:
                c0 = c1 = c2 = flat_color

            # UVs
            uv0 = uv1 = uv2 = None
            if uvs and len(face) >= 6:
                uv0 = uvs[face[3]] if face[3] < len(uvs) else (0, 0)
                uv1 = uvs[face[4]] if face[4] < len(uvs) else (0, 0)
                uv2 = uvs[face[5]] if face[5] < len(uvs) else (0, 0)

            self.draw_triangle(
                ndc0, ndc1, ndc2,
                c0, c1, c2,
                uv0, uv1, uv2,
                texture if texture is not None else None
            )

        return self.fb.to_image()
