# agent/memory.py — Memoria de conversaciones con SQLite
# Generado por AgentKit

"""
Sistema de memoria del agente. Guarda el historial de conversaciones
por número de teléfono usando SQLite (local) o PostgreSQL (producción).
También guarda idempotencia de webhooks y datos propios del rubro
(leads, visitas).
"""

import os
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, select, Integer, Float
from dotenv import load_dotenv

load_dotenv()

# Configuración de base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agentkit.db")

# Si es PostgreSQL en producción, ajustar el esquema de URL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Mensaje(Base):
    """Modelo de mensaje en la base de datos."""
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" o "assistant"
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EventoWebhook(Base):
    """
    Registro de mensaje_id ya procesados. Meta y Twilio reintentan la
    entrega del webhook si no reciben 200 a tiempo — sin esta tabla,
    un reintento haría que el agente responda el mismo mensaje 2+ veces.
    """
    __tablename__ = "eventos_webhook"

    mensaje_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    procesado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Lead(Base):
    """Cliente interesado, registrado por el agente para seguimiento de ventas."""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    interes: Mapped[str] = mapped_column(Text)
    presupuesto: Mapped[float | None] = mapped_column(Float, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Visita(Base):
    """Visita agendada a una propiedad."""
    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    id_propiedad: Mapped[str] = mapped_column(String(50))
    fecha: Mapped[str] = mapped_column(String(20))   # YYYY-MM-DD
    hora: Mapped[str] = mapped_column(String(10))    # HH:MM
    estado: Mapped[str] = mapped_column(String(20), default="confirmada")
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def inicializar_db():
    """Crea las tablas si no existen."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def mensaje_ya_procesado(mensaje_id: str) -> bool:
    """Retorna True si este mensaje_id ya fue procesado antes (reintento del proveedor)."""
    if not mensaje_id:
        return False
    async with async_session() as session:
        result = await session.get(EventoWebhook, mensaje_id)
        return result is not None


async def marcar_mensaje_procesado(mensaje_id: str):
    """Registra un mensaje_id como procesado. Idempotente: ignora si ya existe."""
    if not mensaje_id:
        return
    async with async_session() as session:
        existente = await session.get(EventoWebhook, mensaje_id)
        if existente is None:
            session.add(EventoWebhook(mensaje_id=mensaje_id))
            await session.commit()


async def guardar_mensaje(telefono: str, role: str, content: str):
    """Guarda un mensaje en el historial de conversación."""
    async with async_session() as session:
        mensaje = Mensaje(
            telefono=telefono,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        session.add(mensaje)
        await session.commit()


async def obtener_historial(telefono: str, limite: int = 20) -> list[dict]:
    """
    Recupera los últimos N mensajes de una conversación.

    Args:
        telefono: Número de teléfono del cliente
        limite: Máximo de mensajes a recuperar (default: 20)

    Returns:
        Lista de diccionarios con role y content
    """
    async with async_session() as session:
        query = (
            select(Mensaje)
            .where(Mensaje.telefono == telefono)
            .order_by(Mensaje.timestamp.desc())
            .limit(limite)
        )
        result = await session.execute(query)
        mensajes = result.scalars().all()

        # Invertir para orden cronológico (los más recientes están primero)
        mensajes.reverse()

        return [
            {"role": msg.role, "content": msg.content}
            for msg in mensajes
        ]


async def limpiar_historial(telefono: str):
    """Borra todo el historial de una conversación."""
    async with async_session() as session:
        query = select(Mensaje).where(Mensaje.telefono == telefono)
        result = await session.execute(query)
        mensajes = result.scalars().all()
        for msg in mensajes:
            session.delete(msg)
        await session.commit()


async def registrar_lead(telefono: str, nombre: str, interes: str, presupuesto: float | None = None):
    """Guarda un lead para que el equipo de ventas le dé seguimiento."""
    async with async_session() as session:
        session.add(Lead(telefono=telefono, nombre=nombre, interes=interes, presupuesto=presupuesto))
        await session.commit()


async def registrar_visita(telefono: str, id_propiedad: str, fecha: str, hora: str) -> int:
    """Agenda una visita y retorna su ID."""
    async with async_session() as session:
        visita = Visita(telefono=telefono, id_propiedad=id_propiedad, fecha=fecha, hora=hora)
        session.add(visita)
        await session.commit()
        await session.refresh(visita)
        return visita.id


async def listar_visitas(telefono: str) -> list[dict]:
    """Lista las visitas agendadas por un cliente, ordenadas por fecha."""
    async with async_session() as session:
        query = (
            select(Visita)
            .where(Visita.telefono == telefono)
            .order_by(Visita.fecha, Visita.hora)
        )
        result = await session.execute(query)
        return [
            {"id": v.id, "id_propiedad": v.id_propiedad, "fecha": v.fecha, "hora": v.hora, "estado": v.estado}
            for v in result.scalars().all()
        ]
