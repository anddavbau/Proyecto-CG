"""
light/__init__.py
Exporta los modelos de iluminación disponibles y el modelo plano (sin luz).
"""

from light.gouraud import GouraudLight
from light.phong import PhongLight
from light.blinn_phong import BlinnPhongLight


class FlatLight:
    """
    Sin cálculo de iluminación: devuelve el color base tal cual.
    Útil para modo 'flat color' puro.
    """

    def shade(self, position, normal, base_color) -> tuple:
        return tuple(int(c) for c in base_color[:3])


LIGHT_MODELS = {
    'flat':        FlatLight,
    'gouraud':     GouraudLight,
    'phong':       PhongLight,
    'blinn-phong': BlinnPhongLight,
}


def get_light_model(name: str, **kwargs):
    """Instancia y retorna el modelo de iluminación por nombre."""
    cls = LIGHT_MODELS.get(name, FlatLight)
    if cls is FlatLight:
        return cls()
    return cls(**kwargs)
