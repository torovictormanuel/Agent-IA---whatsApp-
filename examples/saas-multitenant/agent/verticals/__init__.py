# agent/verticals/__init__.py — Registro de rubros disponibles

"""
Cada rubro es un módulo con el mismo contrato que en el modo single-tenant:
TOOLS (schemas) + EJECUTAR_TOOL (dispatcher). La diferencia es que acá las
funciones reciben también `negocio_id`, para consultar SOLO los datos de
ese negocio.

Agregar un rubro nuevo = agregar un módulo acá y una entrada en VERTICALES.
Ningún otro archivo del motor (main.py, brain.py, memory.py) cambia.
"""

from types import ModuleType
import agent.verticals.inmobiliaria as inmobiliaria

VERTICALES: dict[str, ModuleType] = {
    "inmobiliaria": inmobiliaria,
}


def obtener_vertical(nombre: str) -> ModuleType:
    modulo = VERTICALES.get(nombre)
    if not modulo:
        raise ValueError(f"Vertical no registrada: {nombre}. Disponibles: {list(VERTICALES)}")
    return modulo
