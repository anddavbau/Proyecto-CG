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

    @staticmethod
    def _edge(ax, ay, bx, by, px, py):
        return (px - ax) * (by - ay) - (py - ay) * (bx - ax)

    def draw_triangle(self, v0, v1, v2, color0, color1, color2,
                      uv0=None, uv1=None, uv2=None, texture=None):
        """
        Rasteriza un triángulo con interpolación de color (Gouraud) o textura.
        v0/v1/v2: arrays NDC (x, y, z, w).
        color0..2: tuplas RGB por vértice.
        """
        w = self.width
        h = self.height

        # NDC → píxel
        px0 = int((v0[0] + 1.0) * 0.5 * w)
        py0 = int((1.0 - (v0[1] + 1.0) * 0.5) * h)
        px1 = int((v1[0] + 1.0) * 0.5 * w)
        py1 = int((1.0 - (v1[1] + 1.0) * 0.5) * h)
        px2 = int((v2[0] + 1.0) * 0.5 * w)
        py2 = int((1.0 - (v2[1] + 1.0) * 0.5) * h)

        min_x = max(0, min(px0, px1, px2))
        max_x = min(w - 1, max(px0, px1, px2))
        min_y = max(0, min(py0, py1, py2))
        max_y = min(h - 1, max(py0, py1, py2))

        if min_x > max_x or min_y > max_y:
            return

        area = self._edge(px0, py0, px1, py1, px2, py2)
        if abs(area) < 1e-6:
            return

        z0, z1, z2 = float(v0[2]), float(v1[2]), float(v2[2])

        # Pre-convertir colores a floats
        r0, g0, b0 = float(color0[0]), float(color0[1]), float(color0[2])
        r1, g1, b1 = float(color1[0]), float(color1[1]), float(color1[2])
        r2, g2, b2 = float(color2[0]), float(color2[1]), float(color2[2])

        tex_arr = None
        tex_w, tex_h_px = 1, 1
        if texture is not None and uv0 is not None:
            tex_arr = np.array(texture, dtype=np.uint8)
            tex_h_px, tex_w = tex_arr.shape[:2]

        z_buf = self.fb.z_buffer
        col_buf = self.fb.color_buffer

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                w0 = self._edge(px1, py1, px2, py2, px, py)
                w1 = self._edge(px2, py2, px0, py0, px, py)
                w2 = self._edge(px0, py0, px1, py1, px, py)

                if w0 >= 0 and w1 >= 0 and w2 >= 0:
                    l0 = w0 / area
                    l1 = w1 / area
                    l2 = w2 / area
                    z = l0 * z0 + l1 * z1 + l2 * z2

                    if z >= z_buf[py, px]:
                        continue

                    if tex_arr is not None:
                        u = l0 * uv0[0] + l1 * uv1[0] + l2 * uv2[0]
                        v = l0 * uv0[1] + l1 * uv1[1] + l2 * uv2[1]
                        tx = int(u * tex_w) % tex_w
                        ty = int((1.0 - v) * tex_h_px) % tex_h_px
                        pixel_color = tex_arr[ty, tx, :3]
                    else:
                        r = int(l0 * r0 + l1 * r1 + l2 * r2)
                        g = int(l0 * g0 + l1 * g1 + l2 * g2)
                        b = int(l0 * b0 + l1 * b1 + l2 * b2)
                        pixel_color = (
                            r if 0 <= r <= 255 else max(0, min(255, r)),
                            g if 0 <= g <= 255 else max(0, min(255, g)),
                            b if 0 <= b <= 255 else max(0, min(255, b)),
                        )

                    z_buf[py, px] = z
                    col_buf[py, px] = pixel_color

    def render_mesh(self, mesh, model_matrix, view_matrix, proj_matrix,
                    light_model, flat_color, texture=None, shading_mode='flat'):
        """Transforma y rasteriza todas las caras del mesh."""
        self.fb.clear()
        mvp = proj_matrix @ view_matrix @ model_matrix

        verts = mesh['vertices']
        faces = mesh['faces']
        normals = mesh.get('normals', None)
        uvs = mesh.get('uvs', None)

        # Transformar vértices a NDC
        ones = np.ones((len(verts), 1))
        verts_np = np.hstack([np.array(verts, dtype=np.float64), ones])
        clip = (mvp @ verts_np.T).T  # Nx4
        w_vals = clip[:, 3:4]
        valid_mask = np.abs(w_vals.flatten()) > 1e-7
        ndc = np.where(
            valid_mask[:, None],
            clip / np.where(np.abs(w_vals) > 1e-7, w_vals, 1.0),
            np.full_like(clip, 9999.0)
        )

        for face in faces:
            i0, i1, i2 = face[0], face[1], face[2]
            if not (valid_mask[i0] and valid_mask[i1] and valid_mask[i2]):
                continue

            ndc0 = ndc[i0]
            ndc1 = ndc[i1]
            ndc2 = ndc[i2]

            # Clipping básico
            if any(
                abs(n[0]) > 1.5 or abs(n[1]) > 1.5 or not (-1.1 <= n[2] <= 1.1)
                for n in (ndc0, ndc1, ndc2)
            ):
                continue

            # Vectores mundo para iluminación
            p0w = np.array(verts[i0])
            p1w = np.array(verts[i1])
            p2w = np.array(verts[i2])

            # ── Back-face culling en espacio de pantalla (NDC) ─────────
            # Se calcula el signo del área del triángulo proyectado.
            # Si el área es negativa, los vértices están en orden antihorario
            # visto desde la cámara → la cara da la espalda → descartada.
            # Esto respeta cualquier rotación, traslación o escala aplicada.
            ax = ndc1[0] - ndc0[0];  ay = ndc1[1] - ndc0[1]
            bx = ndc2[0] - ndc0[0];  by = ndc2[1] - ndc0[1]
            screen_area = ax * by - ay * bx   # componente Z del cross product 2D
            if screen_area <= 0:
                continue

            # Normal de cara en espacio mundo (para iluminación)
            edge1 = p1w - p0w
            edge2 = p2w - p0w
            face_normal = np.cross(edge1, edge2)
            fn_len = np.linalg.norm(face_normal)
            if fn_len < 1e-8:
                continue
            face_normal /= fn_len

            # Colores por vértice
            if shading_mode == 'flat':
                center = (p0w + p1w + p2w) / 3.0
                c = light_model.shade(center, face_normal, flat_color)
                c0 = c1 = c2 = c
            else:
                if normals and i0 < len(normals) and i1 < len(normals) and i2 < len(normals):
                    n0 = np.array(normals[i0])
                    n1 = np.array(normals[i1])
                    n2 = np.array(normals[i2])
                else:
                    n0 = n1 = n2 = face_normal
                c0 = light_model.shade(p0w, n0, flat_color)
                c1 = light_model.shade(p1w, n1, flat_color)
                c2 = light_model.shade(p2w, n2, flat_color)

            # UVs
            uv0 = uv1 = uv2 = None
            if uvs and len(face) >= 6:
                ui0, ui1, ui2 = face[3], face[4], face[5]
                if ui0 < len(uvs) and ui1 < len(uvs) and ui2 < len(uvs):
                    uv0, uv1, uv2 = uvs[ui0], uvs[ui1], uvs[ui2]

            self.draw_triangle(
                ndc0, ndc1, ndc2,
                c0, c1, c2,
                uv0, uv1, uv2,
                texture
            )

        return self.fb.to_image()
