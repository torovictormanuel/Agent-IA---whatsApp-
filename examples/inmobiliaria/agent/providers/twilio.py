# agent/providers/twilio.py — Adaptador para Twilio WhatsApp
# Generado por AgentKit

import os
import logging
import base64
import httpx
from fastapi import Request
from twilio.request_validator import RequestValidator
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorTwilio(ProveedorWhatsApp):
    """Proveedor de WhatsApp usando Twilio."""

    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.validator = RequestValidator(self.auth_token) if self.auth_token else None

    async def validar_autenticidad(self, request: Request) -> bool:
        """
        Twilio firma cada POST con el header X-Twilio-Signature, calculado
        sobre la URL pública exacta del webhook + los parámetros del form.

        IMPORTANTE detrás de un proxy (Railway, etc.): Twilio firma usando
        la URL PÚBLICA https, pero request.url puede reportar http si el
        proxy no reenvía el esquema. Por eso reconstruimos la URL con el
        header X-Forwarded-Proto cuando está presente.
        """
        if not self.validator:
            logger.error("TWILIO_AUTH_TOKEN no configurado — no se puede validar el webhook")
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
        """Parsea el payload form-encoded de Twilio."""
        form = await request.form()
        texto = form.get("Body", "")
        telefono = form.get("From", "").replace("whatsapp:", "")
        mensaje_id = form.get("MessageSid", "")
        if not texto:
            return []
        return [MensajeEntrante(
            telefono=telefono,
            texto=texto,
            mensaje_id=mensaje_id,
            es_propio=False,
        )]

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        """Envía mensaje via Twilio API."""
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            logger.warning("Variables de Twilio no configuradas")
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
