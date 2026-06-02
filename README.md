# Software 3D Renderer

Rasterizador 3D implementado **desde cero en Python**, sin OpenGL ni ninguna API gráfica.
Toda la rasterización, interpolación de colores, z-buffer e iluminación está escrita
a mano usando únicamente NumPy y Pillow (para mostrar la imagen en tkinter).

---

## Estructura del proyecto

```
renderer/
├── main.py                   # Punto de entrada
├── requirements.txt
│
├── core/
│   ├── renderer.py           # Framebuffer, z-buffer, rasterización de triángulos
│   └── obj_loader.py         # Parser de archivos .obj (vértices, UVs, normales, caras)
│
├── transforms/               # Transformaciones geométricas 4×4
│   ├── __init__.py           # build_model_matrix() → T × R × S
│   ├── translation.py        # translation_matrix(tx, ty, tz)
│   ├── rotation.py           # rotation_x/y/z(), rotation_euler(), rotation_axis_angle()
│   └── scale.py              # scale_matrix(), uniform_scale()
│
├── light/                    # Modelos de iluminación
│   ├── __init__.py           # get_light_model(), FlatLight
│   ├── gouraud.py            # Gouraud  — iluminación por vértice
│   ├── phong.py              # Phong    — reflexión especular R·V
│   └── blinn_phong.py        # Blinn-Phong — halfway vector H = normalize(L+V)
│
├── gui/                      # Interfaz gráfica (tkinter)
│   ├── __init__.py
│   ├── app.py                # Orquestador: conecta todo el pipeline
│   ├── viewport.py           # Canvas donde se muestra el framebuffer
│   ├── panel.py              # Panel lateral: sliders, selectores, botones
│   └── statusbar.py          # Barra inferior: tiempo de render, triángulos
│
├── models/                   # Coloca aquí tus archivos .obj
│   ├── pyramid.obj           # Pirámide de ejemplo incluida
│   └── generate_sphere.py    # Script para generar una esfera UV
│
└── textures/                 # Coloca aquí tus texturas (.png, .jpg, etc.)
```

---

## Instalación y ejecución

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. (Opcional) Generar esfera UV de ejemplo
python models/generate_sphere.py

# 3. Ejecutar
python main.py
```

---

## Características

### Rasterización desde cero
- **Framebuffer** propio: buffer de color RGB + z-buffer por píxel
- **Rasterización de triángulos** por coordenadas baricéntricas (edge function)
- **Z-buffer** para resolución de visibilidad correcta
- **Back-face culling** por producto punto con la normal de la cara
- **Perspectiva** correcta: pipeline MVP completo (Model → View → Projection)

### Modelos de iluminación
| Modelo       | Descripción                                             |
|--------------|---------------------------------------------------------|
| **Flat**     | Color plano sin iluminación                             |
| **Gouraud**  | Luz calculada por vértice, interpolada entre ellos      |
| **Phong**    | Reflexión especular `R = 2(N·L)N − L`                  |
| **Blinn-Phong** | Halfway vector `H = normalize(L+V)` (más eficiente) |

### Transformaciones
- **Traslación**, **Rotación** (Euler XYZ, eje-ángulo) y **Escala** como matrices 4×4
- Composición `M = T × R × S` en `transforms/__init__.py`

### Interfaz gráfica
- Panel lateral con sliders en tiempo real para todas las transformaciones
- Control de posición de la luz y sus componentes (ambiental, difusa, especular, shininess)
- Selector de color base y modo de sombreado
- Carga de modelos `.obj` y texturas (`.png`, `.jpg`, etc.)
- Barra de estado con tiempo de render y conteo de triángulos

---

## Agregar tus propios modelos

Coloca archivos `.obj` en la carpeta `models/`. El programa los detectará
automáticamente al iniciar y podrás cargar cualquiera desde el botón del panel.

## Agregar texturas

Coloca imágenes en la carpeta `textures/` y cárgalas desde el botón del panel.
La textura se mapea con las coordenadas UV del modelo (si las tiene).
# Proyecto-CG
# Proyecto-CG
# Proyecto-CG
