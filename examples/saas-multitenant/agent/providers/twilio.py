# agent/providers/twilio.py — Adaptador para Twilio WhatsApp
# Generado por AgentKit (modo multi-tenant)

import logging
import base64
import httpx
from fastapi import Request
from twilio.request_validator import RequestValidator
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorTwilio(ProveedorWhatsApp):
    """
    Proveedor de WhatsApp usando Twilio, configurado con las credenciales
    de UN negocio específico (no las globales del proceso).

    En la práctica, si tu plataforma compra los números bajo una sola
    cuenta Twilio, `account_sid`/`auth_token` pueden repetirse entre
    negocios y lo único que cambia es `phone_number` — pero cada uno
    igual se guarda por separado en la fila de Negocio, por si algún
    cliente trae su propia cuenta de Twilio.
    """

    def __init__(self, account_sid: str, auth_token: str, phone_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.phone_number = phone_number
        self.validator = RequestValidator(auth_token) if auth_token else None

    async def validar_autenticidad(self, request: Request) -> bool:
        if not self.validator:
            logger.error("Negocio sin TWILIO_AUTH_TOKEN configurado — no se puede validar el webhook")
            return False

        firma = request.headers.get("X-Twilio-Signature", "")
        if not firma:
            return False

        proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
        url_publica = str(request.url).replace(request.url.scheme, proto, 1)

        form = await request.form()
        parametros = dict(form)

        return self.validator.validate(url_publica, parametros, firma)

    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        form = await request.form()
        texto = form.get("Body", "")
        telefono = form.get("From", "").replace("whatsapp:", "")
        mensaje_id = form.get("MessageSid", "")
        if not texto:
            return []
        return [MensajeEntrante(telefono=telefono, texto=texto, mensaje_id=mensaje_id, es_propio=False)]

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Credenciales de Twilio incompletas para este negocio")
            return False
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        auth = base64.b64encode(f"{self.account_sid}:{self.auth_token}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {
            "From": f"whatsapp:{self.phone_number}",
            "To": f"whatsapp:{telefono}",
            "Body": mensaje,
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(url, data=data, headers=headers)
            if r.status_code != 201:
                logger.error(f"Error Twilio: {r.status_code} — {r.text}")
            return r.status_code == 201
