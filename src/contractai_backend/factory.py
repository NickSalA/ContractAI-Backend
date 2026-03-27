"""Factory module for creating and configuring the FastAPI application."""

from contextlib import asynccontextmanager
from importlib.metadata import version as get_version

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.exceptions.base import AppError
from .modules.chatbot.api.routers import chat_router, conversation_router
from .modules.chatbot.infrastructure.agent.checkpointer import init_checkpointer
from .modules.documents.api.routers import router as documents_router
from .modules.users.api.routers import auth_router, users_router
from contractai_backend.modules.integrations.api.routers import router as integrations_router
from .modules.notifications.api.routers import router as notifications_router
from .modules.documents.infrastructure import configure_embedding
from .shared.api.error_handlers import app_error_handler, global_exception_handler, http_exception_handler, validation_exception_handler
from .shared.api.middlewares import LoguruMiddleware
from .shared.config import settings

__version__: str = get_version(distribution_name="contractai-backend")


def create() -> FastAPI:
    """Creates and configures the FastAPI application."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        """Lifespan context manager for startup and shutdown events."""
        configure_embedding()
        pool = await init_checkpointer()
        app.state.pool = pool

        yield

        await app.state.pool.close()

    app = FastAPI(title=settings.PROJECT_NAME, version=__version__, lifespan=lifespan)

    app.include_router(router=documents_router, prefix="/documents", tags=["Documentos"])
    app.include_router(router=auth_router, prefix="/login", tags=["Autenticación"])
    app.include_router(router=users_router, prefix="/user", tags=["Usuarios"])
    app.include_router(router=chat_router, prefix="/chatbot", tags=["Chatbot"])
    app.include_router(router=conversation_router, prefix="/conversations", tags=["Conversaciones"])
    app.include_router(router=integrations_router, prefix="/integrations", tags=["Integraciones"])
    app.include_router(router=notifications_router, prefix="/notifications", tags=["Notificaciones"])

    app.add_middleware(
        middleware_class=CORSMiddleware,  # ty:ignore[invalid-argument-type]
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(middleware_class=LoguruMiddleware)  # ty:ignore[invalid-argument-type]

    app.add_exception_handler(exc_class_or_status_code=AppError, handler=app_error_handler)  # ty:ignore[invalid-argument-type]
    app.add_exception_handler(exc_class_or_status_code=StarletteHTTPException, handler=http_exception_handler)  # ty:ignore[invalid-argument-type]
    app.add_exception_handler(exc_class_or_status_code=RequestValidationError, handler=validation_exception_handler)  # ty:ignore[invalid-argument-type]
    app.add_exception_handler(exc_class_or_status_code=Exception, handler=global_exception_handler)

    @app.get(path="/")
    def home():
        """Endpoint raíz para verificar que la aplicación está funcionando."""
        return {"message": "¡Bienvenido a ContractAI-Backend!", "version": __version__}

    return app
