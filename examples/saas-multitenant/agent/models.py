# agent/models.py — Tablas compartidas por todos los negocios
# Toda tabla que guarda datos de un cliente lleva negocio_id.

from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean, ForeignKey, UniqueConstraint

from agent.db import Base


class Negocio(Base):
    """
    Un cliente de la plataforma. Todo lo que antes vivía en config/business.yaml,
    config/prompts.yaml y el .env de un agente individual, ahora es una fila acá.
    """
    __tablename__ = "negocios"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # slug: "vista-real"
    nombre: Mapped[str] = mapped_column(String(200))
    vertical: Mapped[str] = mapped_column(String(50))  # "inmobiliaria" -> agent/verticals/inmobiliaria
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    system_prompt: Mapped[str] = mapped_column(Text)
    fallback_message: Mapped[str] = mapped_column(
        Text, default="Disculpa, no entendí tu mensaje. ¿Podrías reformularlo?"
    )
    error_message: Mapped[str] = mapped_column(
        Text, default="Lo siento, estoy teniendo problemas técnicos. Por favor intenta de nuevo en unos minutos."
    )

    whatsapp_provider: Mapped[str] = mapped_column(String(20))  # "twilio" | "meta"

    # Credenciales Twilio (si whatsapp_provider == "twilio")
    twilio_account_sid: Mapped[str | None] = mapped_column(String(100), nullable=True)
    twilio_auth_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    twilio_phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Credenciales Meta (si whatsapp_provider == "meta")
    meta_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_phone_number_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    meta_verify_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_app_secret: Mapped[str | None] = mapped_column(String(100), nullable=True)

    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Mensaje(Base):
    """Historial de conversación, aislado por negocio_id + telefono."""
    __tablename__ = "mensajes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negocio_id: Mapped[str] = mapped_column(String(50), ForeignKey("negocios.id"), index=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    role: Mapped[str] = mapped_column(String(20))  # "user" o "assistant"
    content: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EventoWebhook(Base):
    """
    Idempotencia: un mensaje_id solo cuenta como procesado DENTRO de un
    negocio (dos negocios distintos jamás deberían compartir mensaje_id,
    pero escopar por negocio_id igual es más seguro que asumirlo).
    """
    __tablename__ = "eventos_webhook"
    __table_args__ = (UniqueConstraint("negocio_id", "mensaje_id", name="uq_negocio_mensaje"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negocio_id: Mapped[str] = mapped_column(String(50), ForeignKey("negocios.id"), index=True)
    mensaje_id: Mapped[str] = mapped_column(String(150))
    procesado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negocio_id: Mapped[str] = mapped_column(String(50), ForeignKey("negocios.id"), index=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    interes: Mapped[str] = mapped_column(Text)
    presupuesto: Mapped[float | None] = mapped_column(Float, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Visita(Base):
    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negocio_id: Mapped[str] = mapped_column(String(50), ForeignKey("negocios.id"), index=True)
    telefono: Mapped[str] = mapped_column(String(50), index=True)
    id_propiedad: Mapped[str] = mapped_column(String(50))
    fecha: Mapped[str] = mapped_column(String(20))
    hora: Mapped[str] = mapped_column(String(10))
    estado: Mapped[str] = mapped_column(String(20), default="confirmada")
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Propiedad(Base):
    """Catálogo de propiedades — reemplaza a config/propiedades.yaml, ahora por negocio_id."""
    __tablename__ = "propiedades"
    __table_args__ = (UniqueConstraint("negocio_id", "codigo", name="uq_negocio_codigo_propiedad"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    negocio_id: Mapped[str] = mapped_column(String(50), ForeignKey("negocios.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(50))  # "P001" — único DENTRO del negocio, no global
    tipo: Mapped[str] = mapped_column(String(30))
    operacion: Mapped[str] = mapped_column(String(20))
    zona: Mapped[str] = mapped_column(String(200))
    precio: Mapped[float] = mapped_column(Float)
    moneda: Mapped[str] = mapped_column(String(10))
    ambientes: Mapped[int] = mapped_column(Integer, default=0)
    dormitorios: Mapped[int] = mapped_column(Integer, default=0)
    banos: Mapped[float] = mapped_column(Float, default=0)
    m2_cubierta: Mapped[float] = mapped_column(Float, default=0)
    m2_semicubierta: Mapped[float] = mapped_column(Float, default=0)
    m2_descubierta: Mapped[float] = mapped_column(Float, default=0)
    expensas: Mapped[float | None] = mapped_column(Float, nullable=True)
    estacionamientos: Mapped[int] = mapped_column(Integer, default=0)
    descripcion: Mapped[str] = mapped_column(Text, default="")
    amenidades: Mapped[str] = mapped_column(Text, default="")  # CSV simple: "pileta,quincho"
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)
