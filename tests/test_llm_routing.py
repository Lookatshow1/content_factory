import pytest

from app.services.llm.client import LLMClient, ProviderConfig


def test_llm_fallback_used(monkeypatch):
    client = LLMClient(job_id=None)
    client.primary = ProviderConfig(name="primary", base_url="http://x", api_key="k", default_model="m", headers={})
    client.fallback = ProviderConfig(name="fallback", base_url="http://y", api_key="k", default_model="m", headers={})

    def fake_call(provider, *args, **kwargs):
        if provider.name == "primary":
            raise RuntimeError("fail")
        return {"text": "ok", "json": None, "usage": {"total_tokens": 1}, "raw": {}, "provider": provider.name, "model": "m"}

    monkeypatch.setattr(client, "_call_provider", fake_call)
    monkeypatch.setattr(client, "_log_usage", lambda *args, **kwargs: None)

    resp = client.generate([{"role": "user", "content": "hi"}], model="m")
    assert resp["provider"] == "fallback"


def test_circuit_breaker_opens(monkeypatch):
    client = LLMClient(job_id=None)
    client.primary = ProviderConfig(name="primary", base_url="http://x", api_key="k", default_model="m", headers={})
    client.fallback = None

    def fail_call(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(client, "_call_provider", fail_call)
    monkeypatch.setattr(client, "_log_usage", lambda *args, **kwargs: None)

    for _ in range(3):
        with pytest.raises(RuntimeError):
            client.generate([{"role": "user", "content": "hi"}], model="m")

    assert client.primary_state.is_open()
