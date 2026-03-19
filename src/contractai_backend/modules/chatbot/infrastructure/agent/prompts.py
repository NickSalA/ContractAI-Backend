from typing import Any

def get_chat_system_prompt() -> str:
    # Combinamos las secciones del prompt de tu amigo en un solo string para LangGraph
    identity = "Eres el 'Asistente de Gestión y Normativa Educativa', una IA especializada en el ecosistema regulatorio..."
    rules = "1. Fidelidad RAG Absoluta: Tu conocimiento se limita EXCLUSIVAMENTE a la herramienta bc_tool..."
    format_res = "Estructura tu respuesta con Título, Misión, Acciones y Fuente..."
    return f"{identity}\n\n{rules}\n\n{format_res}"