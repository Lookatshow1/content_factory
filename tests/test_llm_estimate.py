from app.services.llm.client import LLMClient


def test_estimate_tokens():
    client = LLMClient()
    tokens = client._estimate_tokens(
        [{"role": "user", "content": "Привет мир"}],
        "Ответ",
    )
    assert tokens > 0
