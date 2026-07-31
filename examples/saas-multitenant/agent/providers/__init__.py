# agent/providers/__init__.py — Factory de proveedores (multi-tenant)

"""
A diferencia del modo single-tenant (una sola variable WHATSAPP_PROVIDER
en .env), acá el proveedor se construye por request, a partir de LA FILA
del Negocio que corresponde a ese webhook.
"""

from agent.models import Negocio
from agent.providers.base import ProveedorWhatsApp


def construir_proveedor(negocio: Negocio) -> ProveedorWhatsApp:
    """Instancia el adaptador correcto con las credenciales de este negocio."""
    if negocio.whatsapp_provider == "meta":
        from agent.providers.meta import ProveedorMeta
        return ProveedorMeta(
            access_token=negocio.meta_access_token,
            phone_number_id=negocio.meta_phone_number_id,
            verify_token=negocio.meta_verify_token,
            app_secret=negocio.meta_app_secret,
        )
    elif negocio.whatsapp_provider == "twilio":
        from agent.providers.twilio import ProveedorTwilio
        return ProveedorTwilio(
            account_sid=negocio.twilio_account_sid,
            auth_token=negocio.twilio_auth_token,
            phone_number=negocio.twilio_phone_number,
        )
    else:
        raise ValueError(f"Proveedor no soportado: {negocio.whatsapp_provider}")
