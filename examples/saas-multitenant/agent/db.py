# agent/db.py — Motor de base de datos compartido (multi-tenant)

"""
Un único engine/sesión para toda la plataforma. El aislamiento entre
negocios NO es a nivel de base de datos (una DB por cliente) sino a nivel
de fila: toda tabla que guarda datos de un negocio lleva una columna
`negocio_id` y CADA query la filtra por ese valor. Ver models.py.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./agentkit.db")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def inicializar_db():
    """Crea las tablas si no existen."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
