"""Factory module for creating and configuring the FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from .core.exceptions.base import AppError
from .modules.chatbot.api.routers import chat_router, conversation_router
from .modules.documents.api.routers import router as documents_router
from .modules.documents.infrastructure import configure_embedding
from .modules.users.api.routers import auth_router, users_router
from .shared.api.error_handlers import app_error_handler, global_exception_handler, http_exception_handler, validation_exception_handler
from .shared.api.middlewares import LoguruMiddleware
from .shared.config import settings


def create() -> FastAPI:
    """Creates and configures the FastAPI application."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        """Lifespan context manager for startup and shutdown events."""
        configure_embedding()
        yield
        # Aquí puedes agregar cualquier lógica de limpieza que necesites

    app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

    app.include_router(documents_router, prefix="/documents", tags=["documents"])
    app.include_router(auth_router, prefix="/login", tags=["Autenticación"])
    app.include_router(users_router, prefix="/user", tags=["Usuarios"])
    app.include_router(chat_router, prefix="/chatbot", tags=["Chatbot"])
    app.include_router(conversation_router, prefix="/conversations", tags=["Conversaciones"])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoguruMiddleware)

    app.add_exception_handler(AppError, app_error_handler) # pyright: ignore[reportArgumentType]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler) # pyright: ignore[reportArgumentType]
    app.add_exception_handler(RequestValidationError, validation_exception_handler) # pyright: ignore[reportArgumentType]
    app.add_exception_handler(Exception, global_exception_handler)

    @app.get("/")
    def home():
        """Endpoint raíz para verificar que la aplicación está funcionando."""
        return {"message": "¡Bienvenido a ContractAI-Backend!"}

    return app
