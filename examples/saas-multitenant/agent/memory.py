# agent/memory.py — Acceso a datos, siempre filtrado por negocio_id
# Generado por AgentKit (modo multi-tenant)

"""
Cada función acá recibe negocio_id como primer argumento y lo usa para
filtrar. Ninguna query debe tocar una tabla sin pasar por negocio_id —
es la única barrera real entre los datos de un cliente y los de otro.
"""

from datetime import datetime
from sqlalchemy import select

from agent.db import async_session
from agent.models import Negocio, Mensaje, EventoWebhook, Lead, Visita, Propiedad


# ── Negocios ──────────────────────────────────────────────────────

async def obtener_negocio(negocio_id: str) -> Negocio | None:
    async with async_session() as session:
        return await session.get(Negocio, negocio_id)


async def crear_negocio(negocio: Negocio):
    async with async_session() as session:
        session.add(negocio)
        await session.commit()


async def listar_negocios(solo_activos: bool = True) -> list[Negocio]:
    async with async_session() as session:
        query = select(Negocio)
        if solo_activos:
            query = query.where(Negocio.activo.is_(True))
        result = await session.execute(query)
        return list(result.scalars().all())


# ── Idempotencia de webhooks ──────────────────────────────────────

async def mensaje_ya_procesado(negocio_id: str, mensaje_id: str) -> bool:
    if not mensaje_id:
        return False
    async with async_session() as session:
        query = select(EventoWebhook).where(
            EventoWebhook.negocio_id == negocio_id,
            EventoWebhook.mensaje_id == mensaje_id,
        )
        result = await session.execute(query)
        return result.scalar_one_or_none() is not None


async def marcar_mensaje_procesado(negocio_id: str, mensaje_id: str):
    if not mensaje_id:
        return
    if await mensaje_ya_procesado(negocio_id, mensaje_id):
        return
    async with async_session() as session:
        session.add(EventoWebhook(negocio_id=negocio_id, mensaje_id=mensaje_id))
        await session.commit()


# ── Historial de conversación ─────────────────────────────────────

async def guardar_mensaje(negocio_id: str, telefono: str, role: str, content: str):
    async with async_session() as session:
        session.add(Mensaje(
            negocio_id=negocio_id,
            telefono=telefono,
            role=role,
            content=content,
            timestamp=datetime.utcnow(),
        ))
        await session.commit()


async def obtener_historial(negocio_id: str, telefono: str, limite: int = 20) -> list[dict]:
    async with async_session() as session:
        query = (
            select(Mensaje)
            .where(Mensaje.negocio_id == negocio_id, Mensaje.telefono == telefono)
            .order_by(Mensaje.timestamp.desc())
            .limit(limite)
        )
        result = await session.execute(query)
        mensajes = result.scalars().all()
        mensajes = list(reversed(mensajes))
        return [{"role": m.role, "content": m.content} for m in mensajes]


async def limpiar_historial(negocio_id: str, telefono: str):
    async with async_session() as session:
        query = select(Mensaje).where(Mensaje.negocio_id == negocio_id, Mensaje.telefono == telefono)
        result = await session.execute(query)
        for m in result.scalars().all():
            await session.delete(m)
        await session.commit()


# ── Leads y visitas (vertical inmobiliaria) ───────────────────────

async def registrar_lead(negocio_id: str, telefono: str, nombre: str, interes: str, presupuesto: float | None = None):
    async with async_session() as session:
        session.add(Lead(negocio_id=negocio_id, telefono=telefono, nombre=nombre, interes=interes, presupuesto=presupuesto))
        await session.commit()


async def registrar_visita(negocio_id: str, telefono: str, id_propiedad: str, fecha: str, hora: str) -> int:
    async with async_session() as session:
        visita = Visita(negocio_id=negocio_id, telefono=telefono, id_propiedad=id_propiedad, fecha=fecha, hora=hora)
        session.add(visita)
        await session.commit()
        await session.refresh(visita)
        return visita.id


async def listar_visitas(negocio_id: str, telefono: str) -> list[dict]:
    async with async_session() as session:
        query = (
            select(Visita)
            .where(Visita.negocio_id == negocio_id, Visita.telefono == telefono)
            .order_by(Visita.fecha, Visita.hora)
        )
        result = await session.execute(query)
        return [
            {"id": v.id, "id_propiedad": v.id_propiedad, "fecha": v.fecha, "hora": v.hora, "estado": v.estado}
            for v in result.scalars().all()
        ]


# ── Propiedades (catálogo por negocio) ────────────────────────────

def _propiedad_a_dict(p: Propiedad) -> dict:
    return {
        "id": p.codigo,
        "tipo": p.tipo,
        "operacion": p.operacion,
        "zona": p.zona,
        "precio": p.precio,
        "moneda": p.moneda,
        "ambientes": p.ambientes,
        "dormitorios": p.dormitorios,
        "banos": p.banos,
        "m2_cubierta": p.m2_cubierta,
        "m2_semicubierta": p.m2_semicubierta,
        "m2_descubierta": p.m2_descubierta,
        "expensas": p.expensas,
        "estacionamientos": p.estacionamientos,
        "descripcion": p.descripcion,
        "amenidades": [a for a in p.amenidades.split(",") if a],
        "disponible": p.disponible,
    }


async def buscar_propiedades_db(
    negocio_id: str,
    zona: str | None = None,
    tipo: str | None = None,
    operacion: str | None = None,
    moneda: str | None = None,
    precio_min: float | None = None,
    precio_max: float | None = None,
    ambientes_min: int | None = None,
) -> list[dict]:
    async with async_session() as session:
        query = select(Propiedad).where(Propiedad.negocio_id == negocio_id, Propiedad.disponible.is_(True))
        result = await session.execute(query)
        propiedades = result.scalars().all()

    resultados = []
    for p in propiedades:
        if zona and zona.lower() not in p.zona.lower():
            continue
        if tipo and tipo.lower() != p.tipo.lower():
            continue
        if operacion and operacion.lower() != p.operacion.lower():
            continue
        if moneda and moneda.upper() != p.moneda.upper():
            continue
        if precio_min and p.precio < precio_min:
            continue
        if precio_max and p.precio > precio_max:
            continue
        if ambientes_min and p.ambientes < ambientes_min:
            continue
        resultados.append(_propiedad_a_dict(p))

    return resultados


async def obtener_propiedad_db(negocio_id: str, codigo: str) -> dict | None:
    async with async_session() as session:
        query = select(Propiedad).where(Propiedad.negocio_id == negocio_id, Propiedad.codigo == codigo)
        result = await session.execute(query)
        p = result.scalar_one_or_none()
        return _propiedad_a_dict(p) if p else None


async def cargar_catalogo(negocio_id: str, propiedades: list[dict]):
    """Inserta un lote de propiedades para un negocio (usado por scripts/cargar_propiedades.py)."""
    async with async_session() as session:
        for p in propiedades:
            session.add(Propiedad(
                negocio_id=negocio_id,
                codigo=p["id"],
                tipo=p.get("tipo", ""),
                operacion=p.get("operacion", ""),
                zona=p.get("zona", ""),
                precio=p.get("precio", 0),
                moneda=p.get("moneda", ""),
                ambientes=p.get("ambientes", 0),
                dormitorios=p.get("dormitorios", 0),
                banos=p.get("banos", 0),
                m2_cubierta=p.get("m2_cubierta", 0),
                m2_semicubierta=p.get("m2_semicubierta", 0),
                m2_descubierta=p.get("m2_descubierta", 0),
                expensas=p.get("expensas"),
                estacionamientos=p.get("estacionamientos", 0),
                descripcion=p.get("descripcion", ""),
                amenidades=",".join(p.get("amenidades", [])),
                disponible=p.get("disponible", True),
            ))
        await session.commit()
