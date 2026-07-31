# agent/main.py — Servidor FastAPI multi-tenant
# Generado por AgentKit

"""
Un solo servidor atiende a TODOS los negocios de la plataforma. La URL
del webhook identifica al negocio (/webhook/{negocio_id}) — cada cliente
configura esa URL propia en su consola de Twilio o Meta. A partir de ahí,
todo (credenciales, system prompt, catálogo, vertical) se resuelve por
negocio_id, nunca por variables de proceso globales.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from agent.brain import generar_respuesta
from agent.db import inicializar_db
from agent.memory import (
    obtener_negocio,
    guardar_mensaje,
    obtener_historial,
    mensaje_ya_procesado,
    marcar_mensaje_procesado,
)
from agent.providers import construir_proveedor
from agent.verticals import obtener_vertical

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
logging.basicConfig(level=logging.DEBUG if ENVIRONMENT == "development" else logging.INFO)
logger = logging.getLogger("agentkit")

PORT = int(os.getenv("PORT", 8000))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await inicializar_db()
    logger.info("Base de datos inicializada")
    logger.info(f"Servidor AgentKit (multi-tenant) corriendo en puerto {PORT}")
    yield


app = FastAPI(title="AgentKit — WhatsApp AI Agent (SaaS multi-tenant)", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def health_check():
    return {"status": "ok", "service": "agentkit-multitenant"}


@app.get("/webhook/{negocio_id}")
async def webhook_verificacion(negocio_id: str, request: Request):
    """Verificación GET del webhook (requerida por Meta)."""
    negocio = await obtener_negocio(negocio_id)
    if not negocio or not negocio.activo:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    proveedor = construir_proveedor(negocio)
    resultado = await proveedor.validar_webhook(request)
    if resultado is not None:
        return PlainTextResponse(str(resultado))
    return {"status": "ok"}


@app.post("/webhook/{negocio_id}")
async def webhook_handler(negocio_id: str, request: Request):
    """
    Recibe mensajes de WhatsApp para UN negocio puntual. La URL ya
    resuelve el tenant — todo lo demás (credenciales, prompt, tools)
    se busca a partir de esa fila de Negocio.
    """
    negocio = await obtener_negocio(negocio_id)
    if not negocio:
        # 404 y no 403: no confirmamos si el negocio existe o no ante quien
        # no tiene ni siquiera un negocio_id válido para intentar firmar
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    if not negocio.activo:
        raise HTTPException(status_code=403, detail="Negocio inactivo")

    try:
        proveedor = construir_proveedor(negocio)

        if not await proveedor.validar_autenticidad(request):
            logger.warning(f"Webhook rechazado (negocio={negocio_id}): firma inválida o ausente")
            raise HTTPException(status_code=403, detail="Firma inválida")

        vertical = obtener_vertical(negocio.vertical)
        mensajes = await proveedor.parsear_webhook(request)

        for msg in mensajes:
            if msg.es_propio or not msg.texto:
                continue

            if await mensaje_ya_procesado(negocio_id, msg.mensaje_id):
                logger.info(f"Mensaje {msg.mensaje_id} ya procesado (negocio={negocio_id}) — se ignora reintento")
                continue
            await marcar_mensaje_procesado(negocio_id, msg.mensaje_id)

            logger.info(f"[{negocio_id}] Mensaje de {msg.telefono}: {msg.texto}")

            historial = await obtener_historial(negocio_id, msg.telefono)

            respuesta = await generar_respuesta(
                mensaje=msg.texto,
                historial=historial,
                telefono=msg.telefono,
                negocio_id=negocio_id,
                system_prompt=negocio.system_prompt,
                tools=vertical.TOOLS,
                ejecutar_tool=vertical.EJECUTAR_TOOL,
                fallback_message=negocio.fallback_message,
                error_message=negocio.error_message,
            )

            await guardar_mensaje(negocio_id, msg.telefono, "user", msg.texto)
            await guardar_mensaje(negocio_id, msg.telefono, "assistant", respuesta)

            await proveedor.enviar_mensaje(msg.telefono, respuesta)

            logger.info(f"[{negocio_id}] Respuesta a {msg.telefono}: {respuesta}")

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en webhook (negocio={negocio_id}): {e}")
        raise HTTPException(status_code=500, detail=str(e))
