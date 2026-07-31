# agent/verticals/inmobiliaria/tools.py — Herramientas del rubro inmobiliario
# Generado por AgentKit (modo multi-tenant)

"""
Mismo contrato que en el modo single-tenant (TOOLS + EJECUTAR_TOOL), pero
cada función recibe además `negocio_id` (inyectado por brain.py junto con
`telefono`) y lo usa para consultar SOLO el catálogo y los datos de ESE
negocio — nunca cruza datos entre clientes de la plataforma.
"""

import logging
from datetime import datetime

from agent.memory import (
    buscar_propiedades_db,
    obtener_propiedad_db,
    registrar_visita,
    listar_visitas,
    registrar_lead as _registrar_lead_db,
)

logger = logging.getLogger("agentkit")


async def buscar_propiedades(
    telefono: str,
    negocio_id: str,
    zona: str | None = None,
    tipo: str | None = None,
    operacion: str | None = None,
    moneda: str | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    ambientes_min: int | None = None,
) -> dict:
    """Filtra el catálogo DE ESTE NEGOCIO según los criterios del modelo."""
    resultados = await buscar_propiedades_db(
        negocio_id, zona, tipo, operacion, moneda, precio_min, precio_max, ambientes_min
    )
    return {"total_encontradas": len(resultados), "propiedades": resultados[:5]}


async def obtener_propiedad(telefono: str, negocio_id: str, id_propiedad: str) -> dict:
    """Detalle completo de una propiedad de este negocio por su código."""
    propiedad = await obtener_propiedad_db(negocio_id, id_propiedad)
    if not propiedad:
        return {"error": f"No existe una propiedad con id {id_propiedad}"}
    return propiedad


async def agendar_visita(telefono: str, negocio_id: str, id_propiedad: str, fecha: str, hora: str) -> dict:
    """Agenda una visita presencial. fecha en YYYY-MM-DD, hora en HH:MM (24h)."""
    propiedad = await obtener_propiedad_db(negocio_id, id_propiedad)
    if not propiedad:
        return {"error": f"No existe una propiedad con id {id_propiedad}"}

    try:
        datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Formato de fecha/hora inválido. Usa YYYY-MM-DD y HH:MM"}

    visita_id = await registrar_visita(negocio_id, telefono, id_propiedad, fecha, hora)
    return {
        "confirmado": True,
        "visita_id": visita_id,
        "propiedad": propiedad.get("zona"),
        "fecha": fecha,
        "hora": hora,
    }


async def listar_mis_visitas(telefono: str, negocio_id: str) -> dict:
    """Lista las visitas que este cliente ya tiene agendadas con este negocio."""
    return {"visitas": await listar_visitas(negocio_id, telefono)}


async def registrar_lead(telefono: str, negocio_id: str, nombre: str, interes: str, presupuesto: float | None = None) -> dict:
    """Guarda los datos de contacto e interés del cliente para el equipo de ventas de este negocio."""
    await _registrar_lead_db(negocio_id, telefono, nombre, interes, presupuesto)
    return {"registrado": True}


async def escalar_a_asesor(telefono: str, negocio_id: str, motivo: str) -> dict:
    """Deriva la conversación a un asesor humano de este negocio."""
    logger.warning(f"ESCALAR A ASESOR — negocio={negocio_id} telefono={telefono} motivo={motivo}")
    # TODO: conectar con el canal real del equipo de CADA negocio (Slack, email, CRM propio, etc.)
    return {"escalado": True, "mensaje": "Un asesor se pondrá en contacto contigo pronto."}


# ════════════════════════════════════════════════════════════
# Contrato con brain.py — schemas + dispatcher
# (idéntico al single-tenant; `negocio_id` NUNCA aparece acá porque
# el modelo no debe verlo ni controlarlo — brain.py lo inyecta)
# ════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "buscar_propiedades",
        "description": "Busca propiedades en el catálogo según zona, tipo, operación, moneda, precio o número de ambientes. Úsala cuando el cliente pregunte por propiedades disponibles.",
        "input_schema": {
            "type": "object",
            "properties": {
                "zona": {"type": "string", "description": "Barrio o zona, ej: 'Palermo', 'Nordelta'"},
                "tipo": {"type": "string", "enum": ["departamento", "PH", "casa", "oficina", "terreno", "local", "monoambiente", "piso", "semipiso"]},
                "operacion": {"type": "string", "enum": ["venta", "alquiler"]},
                "moneda": {"type": "string", "enum": ["USD", "ARS"]},
                "precio_min": {"type": "number"},
                "precio_max": {"type": "number"},
                "ambientes_min": {"type": "integer"},
            },
        },
    },
    {
        "name": "obtener_propiedad",
        "description": "Obtiene el detalle completo de UNA propiedad específica por su ID.",
        "input_schema": {
            "type": "object",
            "properties": {"id_propiedad": {"type": "string"}},
            "required": ["id_propiedad"],
        },
    },
    {
        "name": "agendar_visita",
        "description": "Agenda una visita presencial a una propiedad en una fecha y hora específicas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "id_propiedad": {"type": "string"},
                "fecha": {"type": "string", "description": "Formato YYYY-MM-DD"},
                "hora": {"type": "string", "description": "Formato HH:MM, 24 horas"},
            },
            "required": ["id_propiedad", "fecha", "hora"],
        },
    },
    {
        "name": "listar_mis_visitas",
        "description": "Lista las visitas que este cliente ya tiene agendadas.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "registrar_lead",
        "description": "Guarda los datos de contacto del cliente y qué está buscando, para seguimiento del equipo de ventas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "interes": {"type": "string"},
                "presupuesto": {"type": "number"},
            },
            "required": ["nombre", "interes"],
        },
    },
    {
        "name": "escalar_a_asesor",
        "description": "Deriva la conversación a un asesor humano. Úsala cuando el cliente quiera negociar precio, firmar, o pida hablar con una persona.",
        "input_schema": {
            "type": "object",
            "properties": {"motivo": {"type": "string"}},
            "required": ["motivo"],
        },
    },
]

EJECUTAR_TOOL = {
    "buscar_propiedades": buscar_propiedades,
    "obtener_propiedad": obtener_propiedad,
    "agendar_visita": agendar_visita,
    "listar_mis_visitas": listar_mis_visitas,
    "registrar_lead": registrar_lead,
    "escalar_a_asesor": escalar_a_asesor,
}
