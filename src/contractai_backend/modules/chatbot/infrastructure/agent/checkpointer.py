from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from contractai_backend.shared.config import settings

async def init_checkpointer() -> AsyncConnectionPool:
    pool = AsyncConnectionPool(
        conninfo=settings.CONN_STRING,
        open=False,
        kwargs={
            "prepare_threshold": 0,
            "row_factory": dict_row,
            "autocommit": True,
            "options": "-c search_path=checkpoint,public"
        }
    )

    await pool.open()

    checkpointer = AsyncPostgresSaver(pool)
    await checkpointer.setup()

    return pool