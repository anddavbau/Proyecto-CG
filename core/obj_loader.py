"""
core/obj_loader.py
Cargador de archivos .obj de Wavefront.
Soporta: vértices, normales, coordenadas UV y caras trianguladas/polígonos.
"""

import os
from typing import Dict, Any


def load_obj(filepath: str) -> Dict[str, Any]:
    """
    Parsea un archivo .obj y retorna un diccionario con:
      vertices  : list of (x, y, z)
      normals   : list of (nx, ny, nz)
      uvs       : list of (u, v)
      faces     : list of (i0, i1, i2, [uv0, uv1, uv2], [n0, n1, n2])
                  índices 0-based
    """
    vertices = []
    normals = []
    uvs = []
    faces = []

    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            token = parts[0]

            if token == 'v':
                vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))

            elif token == 'vn':
                normals.append((float(parts[1]), float(parts[2]), float(parts[3])))

            elif token == 'vt':
                u = float(parts[1])
                v = float(parts[2]) if len(parts) > 2 else 0.0
                uvs.append((u, v))

            elif token == 'f':
                # Cada token puede ser: v, v/vt, v//vn, v/vt/vn
                poly_v = []
                poly_uv = []
                poly_n = []

                for token_f in parts[1:]:
                    indices = token_f.split('/')
                    vi = int(indices[0]) - 1  # 1-based → 0-based

                    ui = -1
                    ni = -1
                    if len(indices) > 1 and indices[1]:
                        ui = int(indices[1]) - 1
                    if len(indices) > 2 and indices[2]:
                        ni = int(indices[2]) - 1

                    poly_v.append(vi)
                    poly_uv.append(ui)
                    poly_n.append(ni)

                # Triangular el polígono (fan)
                for i in range(1, len(poly_v) - 1):
                    face = [
                        poly_v[0], poly_v[i], poly_v[i + 1],
                        poly_uv[0], poly_uv[i], poly_uv[i + 1],
                        poly_n[0], poly_n[i], poly_n[i + 1],
                    ]
                    faces.append(face)

    # Normalizar: si hay normales por vértice en las caras, construir array por vértice
    vertex_normals = _build_vertex_normals(vertices, normals, faces)

    return {
        'vertices': vertices,
        'normals': vertex_normals if vertex_normals else normals,
        'uvs': uvs,
        'faces': faces,
        'source': os.path.basename(filepath),
    }


def _build_vertex_normals(vertices, normals, faces):
    """
    Construye normales por vértice promediando las normales de las caras
    que los comparten. Si el .obj ya tiene normales, las usa directamente.
    """
    import numpy as np

    n_verts = len(vertices)
    accum = [np.zeros(3) for _ in range(n_verts)]
    count = [0] * n_verts

    has_face_normals = any(f[6] >= 0 for f in faces if len(f) >= 9)

    if has_face_normals and normals:
        for f in faces:
            for j, vi in enumerate((f[0], f[1], f[2])):
                ni = f[6 + j] if len(f) >= 9 else -1
                if 0 <= ni < len(normals):
                    accum[vi] += np.array(normals[ni])
                    count[vi] += 1
    else:
        # Calcular normales de cara y acumular
        verts_np = [np.array(v) for v in vertices]
        for f in faces:
            i0, i1, i2 = f[0], f[1], f[2]
            if i0 >= n_verts or i1 >= n_verts or i2 >= n_verts:
                continue
            e1 = verts_np[i1] - verts_np[i0]
            e2 = verts_np[i2] - verts_np[i0]
            fn = np.cross(e1, e2)
            for vi in (i0, i1, i2):
                accum[vi] += fn
                count[vi] += 1

    result = []
    for i in range(n_verts):
        n = accum[i]
        ln = np.linalg.norm(n)
        if ln > 1e-8:
            result.append(tuple(n / ln))
        else:
            result.append((0.0, 1.0, 0.0))
    return result


def center_and_normalize(mesh: dict) -> dict:
    """
    Centra el mesh en el origen y lo escala para caber en [-1, 1].
    Retorna el mesh modificado.
    """
    import numpy as np
    verts = np.array(mesh['vertices'], dtype=np.float64)
    if len(verts) == 0:
        return mesh
    mn = verts.min(axis=0)
    mx = verts.max(axis=0)
    center = (mn + mx) / 2.0
    extent = (mx - mn).max()
    if extent < 1e-8:
        extent = 1.0
    scale = 2.0 / extent
    normalized = ((verts - center) * scale).tolist()
    mesh['vertices'] = [tuple(v) for v in normalized]
    return mesh
