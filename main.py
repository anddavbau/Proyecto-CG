"""
Software 3D Renderer - Punto de entrada principal
Rasterizador implementado desde cero (sin OpenGL ni APIs gráficas)
"""

import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import App


def main():
    app = App(width=900, height=650, title="Software 3D Renderer",default_model='botella.obj')
    app.run()


if __name__ == "__main__":
    main()
