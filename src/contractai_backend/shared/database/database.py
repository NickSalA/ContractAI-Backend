"""Database configuration and session management for ContractAI Backend."""

import ssl
from contextlib import asynccontextmanager

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from contractai_backend.shared.config import settings

DATABASE_URL: str = settings.DATABASE_URL

connect_args = {}
if DATABASE_URL and "localhost" not in DATABASE_URL:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    connect_args = {"ssl": ctx}

# 2. El Engine (Motor)
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

async def get_session():
    """Proporciona una sesión de base de datos asíncrona."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        except IntegrityError as e:
            await session.rollback()
            raise ValueError(f"Violación de integridad en la BD: {e}") from e

        except OperationalError as e:
            await session.rollback()
            raise ValueError(f"Error de conexión a la BD: {e}") from e

        except SQLAlchemyError as e:
            await session.rollback()
            raise ValueError(f"Error al ejecutar la consulta en la BD: {e}") from e

        except Exception:
            await session.rollback()
            raise

get_session_context = asynccontextmanager(get_session)
