from datetime import datetime
from pydantic import BaseModel

class Message(BaseModel):
    content: str
    role: str
    timestamp: datetime

class ChatThread(BaseModel):
    id: int
    messages: list[Message]