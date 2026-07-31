# agent/brain.py — Cerebro del agente: Claude API + tool calling (multi-tenant)
# Generado por AgentKit

"""
Motor genérico de conversación + tool-calling. A diferencia del modo
single-tenant (que importaba TOOLS/EJECUTAR_TOOL fijos de agent.tools),
acá TODO lo específico del negocio llega por parámetro: el system prompt,
las tools disponibles y su dispatcher. Este archivo no sabe qué negocio
ni qué rubro está atendiendo — eso lo resuelve main.py antes de llamarlo.
"""

import os
import json
import logging
from typing import Callable, Awaitable
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("agentkit")

# LLM_PROVIDER=anthropic (default) llama directo a la API de Anthropic.
# LLM_PROVIDER=bedrock llama al mismo Claude pero vía AWS Bedrock — útil
# para probar gratis con los $200 de crédito que AWS da a cuentas nuevas
# (cubre Bedrock), sin depender de crédito de la cuenta de Anthropic.
# El código de tool-calling de más abajo es IDÉNTICO en los dos casos —
# solo cambia quién factura la llamada.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")

if LLM_PROVIDER == "bedrock":
    from anthropic import AsyncAnthropicBedrock
    # Usa la cadena de credenciales estándar de AWS (env vars
    # AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, o un perfil configurado) —
    # igual que boto3, no hace falta pasarlas a mano acá.
    client = AsyncAnthropicBedrock(aws_region=os.getenv("AWS_REGION", "us-east-1"))
    # En Bedrock el nombre del modelo NO es "claude-sonnet-5" — es el ID de
    # inference profile que copiás del catálogo de modelos en la consola de
    # Bedrock (algo como "us.anthropic.claude-sonnet-5-...-v1:0"). No lo
    # hardcodeamos porque cambia por región y por versión habilitada.
    MODELO = os.getenv("ANTHROPIC_MODEL")
    if not MODELO:
        raise ValueError(
            "LLM_PROVIDER=bedrock requiere ANTHROPIC_MODEL con el inference "
            "profile ID exacto de la consola de Bedrock (Model catalog)."
        )
else:
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    # Configurable para no quemar crédito de producción durante desarrollo:
    # en local/testing conviene ANTHROPIC_MODEL=claude-haiku-4-5-20251001
    # (mucho más barato) y reservar Sonnet para tráfico real de clientes.
    MODELO = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

MAX_TURNOS_TOOL = 5


async def _ejecutar_tool(
    nombre: str,
    tool_input: dict,
    telefono: str,
    negocio_id: str,
    ejecutar_tool: dict[str, Callable[..., Awaitable[dict]]],
) -> str:
    """
    `telefono` y `negocio_id` se inyectan SIEMPRE — el modelo nunca los ve
    ni los puede falsificar. Así se garantiza que una tool jamás pueda
    operar sobre el número o los datos de otro negocio.
    """
    funcion = ejecutar_tool.get(nombre)
    if not funcion:
        return json.dumps({"error": f"Herramienta '{nombre}' no existe"})
    try:
        resultado = await funcion(telefono=telefono, negocio_id=negocio_id, **tool_input)
        return json.dumps(resultado, ensure_ascii=False, default=str)
    except Exception as e:
        logger.error(f"Error ejecutando tool '{nombre}' (negocio={negocio_id}): {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)


async def generar_respuesta(
    mensaje: str,
    historial: list[dict],
    telefono: str,
    negocio_id: str,
    system_prompt: str,
    tools: list[dict],
    ejecutar_tool: dict[str, Callable[..., Awaitable[dict]]],
    fallback_message: str = "Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?",
    error_message: str = "Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos.",
) -> str:
    """
    Genera una respuesta para UN negocio específico, resolviendo tool
    calls si el modelo las solicita.
    """
    if not mensaje or len(mensaje.strip()) < 2:
        return fallback_message

    mensajes = list(historial) + [{"role": "user", "content": mensaje}]

    try:
        for _ in range(MAX_TURNOS_TOOL):
            response = await client.messages.create(
                model=MODELO,
                max_tokens=1024,
                system=system_prompt,
                messages=mensajes,
                tools=tools,
            )

            if response.stop_reason != "tool_use":
                bloques_texto = [b.text for b in response.content if b.type == "text"]
                logger.info(
                    f"Respuesta generada (negocio={negocio_id}, "
                    f"{response.usage.input_tokens} in / {response.usage.output_tokens} out)"
                )
                return "\n".join(bloques_texto) or fallback_message

            mensajes.append({"role": "assistant", "content": response.content})

            resultados_tools = []
            for bloque in response.content:
                if bloque.type != "tool_use":
                    continue
                logger.info(f"Tool call (negocio={negocio_id}): {bloque.name}({bloque.input})")
                resultado = await _ejecutar_tool(bloque.name, bloque.input, telefono, negocio_id, ejecutar_tool)
                resultados_tools.append({
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": resultado,
                })

            mensajes.append({"role": "user", "content": resultados_tools})

        logger.warning(f"Límite de turnos de tool-calling alcanzado (negocio={negocio_id})")
        return error_message

    except Exception as e:
        logger.error(f"Error Claude API (negocio={negocio_id}): {e}")
        return error_message
