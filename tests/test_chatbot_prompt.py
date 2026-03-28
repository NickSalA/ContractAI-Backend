"""Tests for chatbot prompt routing rules."""

from contractai_backend.modules.chatbot.infrastructure.agent.prompts import get_chat_system_prompt


def test_prompt_routes_signer_lists_to_document_search() -> None:
    prompt = get_chat_system_prompt()

    assert "datos que viven dentro del texto de los contratos" in prompt
    assert "personas que firman" in prompt
    assert "usa bc_tool aunque el usuario pida una lista" in prompt
    assert "### Personas identificadas" in prompt
