# agent/tools.py — Herramientas del agente (rubro: inmobiliaria)
# Generado por AgentKit

"""
Herramientas expuestas al modelo como tools de la API de Claude.
Trabajan sobre el catálogo de config/propiedades.yaml y sobre las
tablas Lead/Visita de memory.py.

Contrato con brain.py:
  - TOOLS: lista de schemas JSON que se le pasan al modelo.
  - EJECUTAR_TOOL: dict {nombre: función} para despachar la llamada real.
  - Cada función recibe `telefono` inyectado por brain.py (el modelo
    nunca lo maneja) + los parámetros que decida el modelo.
  - Cada función retorna un dict serializable a JSON.
"""

import yaml
import logging
from datetime import datetime

from agent.memory import registrar_lead as _registrar_lead_db
from agent.memory import registrar_visita as _registrar_visita_db
from agent.memory import listar_visitas as _listar_visitas_db

logger = logging.getLogger("agentkit")


def _cargar_propiedades() -> list[dict]:
    """Lee el catálogo de propiedades desde config/propiedades.yaml."""
    try:
        with open("config/propiedades.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return data.get("propiedades", [])
    except FileNotFoundError:
        logger.error("config/propiedades.yaml no encontrado")
        return []


async def buscar_propiedades(
    telefono: str,
    zona: str | None = None,
    tipo: str | None = None,
    operacion: str | None = None,
    moneda: str | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    ambientes_min: int | None = None,
) -> dict:
    """
    Filtra el catálogo según los criterios recibidos del modelo.

    Nota: precio_min/precio_max se comparan contra el precio publicado TAL
    CUAL está en el catálogo (no se convierte USD<->ARS). Si el cliente da
    un presupuesto en una moneda distinta a la de la propiedad, conviene
    filtrar además por `moneda` para no comparar cifras que no son comparables.
    """
    resultados = []
    for p in _cargar_propiedades():
        if not p.get("disponible", True):
            continue
        if zona and zona.lower() not in p.get("zona", "").lower():
            continue
        if tipo and tipo.lower() != p.get("tipo", "").lower():
            continue
        if operacion and operacion.lower() != p.get("operacion", "").lower():
            continue
        if moneda and moneda.upper() != p.get("moneda", "").upper():
            continue
        if precio_min and p.get("precio", 0) < precio_min:
            continue
        if precio_max and p.get("precio", 0) > precio_max:
            continue
        if ambientes_min and p.get("ambientes", 0) < ambientes_min:
            continue
        resultados.append(p)

    # Limitamos resultados para no saturar el chat de WhatsApp
    return {"total_encontradas": len(resultados), "propiedades": resultados[:5]}


async def obtener_propiedad(telefono: str, id_propiedad: str) -> dict:
    """Detalle completo de una propiedad por su ID."""
    for p in _cargar_propiedades():
        if p.get("id") == id_propiedad:
            return p
    return {"error": f"No existe una propiedad con id {id_propiedad}"}


async def agendar_visita(telefono: str, id_propiedad: str, fecha: str, hora: str) -> dict:
    """Agenda una visita presencial. fecha en YYYY-MM-DD, hora en HH:MM (24h)."""
    propiedad = await obtener_propiedad(telefono, id_propiedad)
    if "error" in propiedad:
        return propiedad

    try:
        datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Formato de fecha/hora inválido. Usa YYYY-MM-DD y HH:MM"}

    visita_id = await _registrar_visita_db(telefono, id_propiedad, fecha, hora)
    return {
        "confirmado": True,
        "visita_id": visita_id,
        "propiedad": propiedad.get("zona"),
        "fecha": fecha,
        "hora": hora,
    }


async def listar_mis_visitas(telefono: str) -> dict:
    """Lista las visitas que este cliente ya tiene agendadas."""
    return {"visitas": await _listar_visitas_db(telefono)}


async def registrar_lead(telefono: str, nombre: str, interes: str, presupuesto: float | None = None) -> dict:
    """Guarda los datos de contacto e interés del cliente para el equipo de ventas."""
    await _registrar_lead_db(telefono, nombre, interes, presupuesto)
    return {"registrado": True}


async def escalar_a_asesor(telefono: str, motivo: str) -> dict:
    """Deriva la conversación a un asesor humano (negociación, caso complejo, etc.)."""
    logger.warning(f"ESCALAR A ASESOR — telefono={telefono} motivo={motivo}")
    # TODO: conectar con el canal real del equipo (Slack, email, CRM, etc.)
    return {"escalado": True, "mensaje": "Un asesor se pondrá en contacto contigo pronto."}


# ════════════════════════════════════════════════════════════
# Contrato con brain.py — schemas + dispatcher
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
                "moneda": {"type": "string", "enum": ["USD", "ARS"], "description": "Filtra por la moneda en la que está publicado el precio"},
                "precio_min": {"type": "number"},
                "precio_max": {"type": "number"},
                "ambientes_min": {"type": "integer", "description": "Ambientes = dormitorios + living/comedor (no cuenta cocina ni baño)"},
            },
        },
    },
    {
        "name": "obtener_propiedad",
        "description": "Obtiene el detalle completo de UNA propiedad específica por su ID (usa el ID que aparece en los resultados de buscar_propiedades).",
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
        "description": "Guarda los datos de contacto del cliente y qué está buscando, para que el equipo de ventas le dé seguimiento. Úsala en cuanto el cliente muestre interés real (no en el primer saludo).",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "interes": {"type": "string", "description": "Qué está buscando el cliente"},
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
