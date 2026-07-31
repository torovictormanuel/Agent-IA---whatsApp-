# agent/providers/base.py — Clase base para proveedores de WhatsApp
# Generado por AgentKit (modo multi-tenant)

"""
A diferencia de la versión single-tenant, acá el proveedor NO lee
credenciales de os.getenv() — las recibe por constructor, porque cada
negocio tiene las suyas (ver providers/factory.py).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from fastapi import Request


@dataclass
class MensajeEntrante:
    telefono: str
    texto: str
    mensaje_id: str
    es_propio: bool


class ProveedorWhatsApp(ABC):
    """Interfaz que cada proveedor de WhatsApp debe implementar."""

    @abstractmethod
    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        ...

    @abstractmethod
    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        ...

    async def validar_webhook(self, request: Request) -> dict | int | None:
        """Verificación GET del webhook (solo Meta la requiere)."""
        return None

    async def validar_autenticidad(self, request: Request) -> bool:
        """Verifica la firma del POST. Cada adaptador la sobreescribe."""
        return True
