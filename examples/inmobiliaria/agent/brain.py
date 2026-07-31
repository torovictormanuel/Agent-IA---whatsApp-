# agent/brain.py — Cerebro del agente: conexión con Claude API + tool calling
# Generado por AgentKit

"""
Lógica de IA del agente. Lee el system prompt de prompts.yaml, ofrece al
modelo las herramientas definidas en tools.py (TOOLS/EJECUTAR_TOOL) y
resuelve el loop de tool-calling hasta obtener una respuesta de texto final.

Este archivo es genérico: no sabe nada de inmobiliaria específicamente.
Para adaptar a otro rubro, se reescribe agent/tools.py, no este archivo.
"""

import os
import json
import yaml
import logging
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

from agent.tools import TOOLS, EJECUTAR_TOOL

load_dotenv()
logger = logging.getLogger("agentkit")

client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Configurable para no quemar crédito de producción durante desarrollo:
# en local/testing conviene ANTHROPIC_MODEL=claude-haiku-4-5-20251001
# (mucho más barato) y reservar Sonnet para tráfico real de clientes.
MODELO = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
MAX_TURNOS_TOOL = 5  # límite de idas y vueltas modelo <-> herramientas por mensaje


def cargar_config_prompts() -> dict:
    """Lee toda la configuración desde config/prompts.yaml."""
    try:
        with open("config/prompts.yaml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("config/prompts.yaml no encontrado")
        return {}


def cargar_system_prompt() -> str:
    """Lee el system prompt desde config/prompts.yaml."""
    config = cargar_config_prompts()
    return config.get("system_prompt", "Eres un asistente útil. Responde en español.")


def obtener_mensaje_error() -> str:
    """Retorna el mensaje de error configurado en prompts.yaml."""
    config = cargar_config_prompts()
    return config.get("error_message", "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos.")


def obtener_mensaje_fallback() -> str:
    """Retorna el mensaje de fallback configurado en prompts.yaml."""
    config = cargar_config_prompts()
    return config.get("fallback_message", "Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?")


async def _ejecutar_tool(nombre: str, tool_input: dict, telefono: str) -> str:
    """
    Ejecuta una función de tools.py y serializa el resultado para
    devolvérselo al modelo como tool_result.

    `telefono` se inyecta SIEMPRE como kwarg — el modelo nunca lo ve ni
    lo puede inventar, así se evita que alguien le pida al agente actuar
    sobre el número de teléfono de otra persona.
    """
    funcion = EJECUTAR_TOOL.get(nombre)
    if not funcion:
        return json.dumps({"error": f"Herramienta '{nombre}' no existe"})
    try:
        resultado = await funcion(telefono=telefono, **tool_input)
        return json.dumps(resultado, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Error ejecutando tool '{nombre}': {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def generar_respuesta(mensaje: str, historial: list[dict], telefono: str) -> str:
    """
    Genera una respuesta usando Claude API, resolviendo tool calls si el
    modelo las solicita (buscar propiedades, agendar visitas, etc.).

    Args:
        mensaje: el mensaje nuevo del usuario
        historial: mensajes previos [{"role": "user/assistant", "content": "..."}]
        telefono: número del cliente — se inyecta a las tools, nunca lo maneja el modelo

    Returns:
        La respuesta final en texto para enviar por WhatsApp
    """
    if not mensaje or len(mensaje.strip()) < 2:
        return obtener_mensaje_fallback()

    system_prompt = cargar_system_prompt()
    mensajes = list(historial) + [{"role": "user", "content": mensaje}]

    try:
        for _ in range(MAX_TURNOS_TOOL):
            response = await client.messages.create(
                model=MODELO,
                max_tokens=1024,
                system=system_prompt,
                messages=mensajes,
                tools=TOOLS,
            )

            if response.stop_reason != "tool_use":
                bloques_texto = [b.text for b in response.content if b.type == "text"]
                logger.info(f"Respuesta generada ({response.usage.input_tokens} in / {response.usage.output_tokens} out)")
                return "\n".join(bloques_texto) or obtener_mensaje_fallback()

            # El modelo pidió usar una o más herramientas antes de responder
            mensajes.append({"role": "assistant", "content": response.content})

            resultados_tools = []
            for bloque in response.content:
                if bloque.type != "tool_use":
                    continue
                logger.info(f"Tool call: {bloque.name}({bloque.input})")
                resultado = await _ejecutar_tool(bloque.name, bloque.input, telefono)
                resultados_tools.append({
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": resultado,
                })

            mensajes.append({"role": "user", "content": resultados_tools})

        # Se agotaron los turnos de tool-calling sin llegar a una respuesta final
        logger.warning("Límite de turnos de tool-calling alcanzado sin respuesta final")
        return obtener_mensaje_error()

    except Exception as e:
        logger.error(f"Error Claude API: {e}")
        return obtener_mensaje_error()
