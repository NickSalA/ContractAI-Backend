from fastapi import APIRouter
from contractai_backend.modules.chatbot.api.routers.chat_router import router as chat_router

router = APIRouter(tags=["Chatbot"])
router.include_router(chat_router)