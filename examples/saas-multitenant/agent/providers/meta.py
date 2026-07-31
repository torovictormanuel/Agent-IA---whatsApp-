# agent/providers/meta.py — Adaptador para Meta WhatsApp Cloud API
# Generado por AgentKit (modo multi-tenant)

import hmac
import hashlib
import logging
import httpx
from fastapi import Request
from agent.providers.base import ProveedorWhatsApp, MensajeEntrante

logger = logging.getLogger("agentkit")


class ProveedorMeta(ProveedorWhatsApp):
    """Proveedor de WhatsApp usando Meta Cloud API, con credenciales de UN negocio."""

    def __init__(self, access_token: str, phone_number_id: str, verify_token: str, app_secret: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.verify_token = verify_token or "agentkit-verify"
        self.app_secret = app_secret
        self.api_version = "v21.0"

    async def validar_webhook(self, request: Request) -> dict | int | None:
        params = request.query_params
        mode = params.get("hub.mode")
        token = params.get("hub.verify_token")
        challenge = params.get("hub.challenge")
        if mode == "subscribe" and token == self.verify_token:
            return int(challenge)
        return None

    async def validar_autenticidad(self, request: Request) -> bool:
        if not self.app_secret:
            logger.error("Negocio sin META_APP_SECRET configurado — no se puede validar el webhook")
            return False

        firma_header = request.headers.get("X-Hub-Signature-256", "")
        if not firma_header.startswith("sha256="):
            return False

        firma_recibida = firma_header.removeprefix("sha256=")
        body = await request.body()
        firma_calculada = hmac.new(self.app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(firma_recibida, firma_calculada)

    async def parsear_webhook(self, request: Request) -> list[MensajeEntrante]:
        body = await request.json()
        mensajes = []
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") == "text":
                        mensajes.append(MensajeEntrante(
                            telefono=msg.get("from", ""),
                            texto=msg.get("text", {}).get("body", ""),
                            mensaje_id=msg.get("id", ""),
                            es_propio=False,
                        ))
        return mensajes

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        if not self.access_token or not self.phone_number_id:
            logger.warning("Credenciales de Meta incompletas para este negocio")
            return False
        url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        payload = {
            "messaging_product": "whatsapp",
            "to": telefono,
            "type": "text",
            "text": {"body": mensaje},
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload, headers=headers)
            if r.status_code != 200:
                logger.error(f"Error Meta API: {r.status_code} — {r.text}")
            return r.status_code == 200
