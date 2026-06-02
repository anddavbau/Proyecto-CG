"""
Script para generar una esfera UV y guardarla como .obj.
Ejecutar: python models/generate_sphere.py
"""
import math
import os

def generate_sphere(stacks=16, slices=16, radius=1.0):
    verts = []
    normals = []
    uvs = []
    faces = []

    for i in range(stacks + 1):
        phi = math.pi * i / stacks
        for j in range(slices + 1):
            theta = 2 * math.pi * j / slices
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.cos(phi)
            z = radius * math.sin(phi) * math.sin(theta)
            verts.append((x, y, z))
            normals.append((x/radius, y/radius, z/radius))
            uvs.append((j/slices, 1 - i/stacks))

    for i in range(stacks):
        for j in range(slices):
            a = i * (slices + 1) + j
            b = a + 1
            c = a + slices + 1
            d = c + 1
            faces.append((a, b, d, a, b, d))
            faces.append((a, d, c, a, d, c))

    out = os.path.join(os.path.dirname(__file__), 'sphere.obj')
    with open(out, 'w') as f:
        f.write('# Esfera UV generada automáticamente\n')
        for v in verts:
            f.write(f'v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
        for vt in uvs:
            f.write(f'vt {vt[0]:.6f} {vt[1]:.6f}\n')
        for vn in normals:
            f.write(f'vn {vn[0]:.6f} {vn[1]:.6f} {vn[2]:.6f}\n')
        for face in faces:
            i0,i1,i2, u0,u1,u2 = face
            f.write(f'f {i0+1}/{u0+1}/{i0+1} {i1+1}/{u1+1}/{i1+1} {i2+1}/{u2+1}/{i2+1}\n')
    print(f'Esfera guardada en: {out}')

if __name__ == '__main__':
    generate_sphere(stacks=20, slices=20)
