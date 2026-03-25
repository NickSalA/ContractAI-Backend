"""Checkpointer: Configuración y manejo del checkpointing para LangGraph."""

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from contractai_backend.shared.config import settings


async def init_checkpointer():
    """Abre el pool de conexiones y prepara las tablas de LangGraph."""
    pool: AsyncConnectionPool[AsyncConnection[DictRow]] = AsyncConnectionPool(
        conninfo=settings.CONN_STRING, open=False, kwargs={"prepare_threshold": 0, "autocommit": True, "row_factory": dict_row}
    )
    await pool.open()

    saver = AsyncPostgresSaver(conn=pool)
    await saver.setup()

    return pool
