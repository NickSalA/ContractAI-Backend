from psycopg_pool import AsyncConnectionPool
from psycopg import AsyncConnection
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from contractai_backend.shared.config import settings

async def setup_connection(conn: AsyncConnection) -> None:
    await conn.execute("SET search_path TO checkpoint, public;")

async def init_checkpointer() -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        conninfo=settings.CONN_STRING,
        open=False,
        configure=setup_connection,
        kwargs={
            "prepare_threshold": 0,
            "row_factory": dict_row,
            "autocommit": True
        }
    )

    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    return pool