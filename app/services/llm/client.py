import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from pydantic import BaseModel, ValidationError

from app import crud
from app.db import SessionLocal
from app.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    default_model: str
    headers: Dict[str, str]


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: Optional[float] = None

    def open_for(self, seconds: int):
        self.opened_at = time.time() + seconds

    def is_open(self) -> bool:
        return self.opened_at is not None and time.time() < self.opened_at

    def reset(self):
        self.failures = 0
        self.opened_at = None


class LLMClient:
    def __init__(self, job_id: Optional[UUID] = None):
        self.job_id = job_id
        self.primary = self._build_provider(settings.LLM_PROVIDER_PRIMARY)
        self.fallback = self._build_provider(settings.LLM_PROVIDER_FALLBACK)
        self.primary_state = CircuitState()
        self.fallback_state = CircuitState()

    def is_enabled(self) -> bool:
        return bool(self.primary or self.fallback)

    def generate(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        json_schema: Optional[dict] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        providers = [
            (self.primary, self.primary_state),
            (self.fallback, self.fallback_state),
        ]
        if not any(provider for provider, _ in providers):
            raise ValueError("no LLM provider configured")

        last_error = None
        for provider, state in providers:
            if not provider:
                continue
            if state.is_open():
                continue
            try:
                resolved_model = model or provider.default_model
                if provider == self.fallback and settings.LLM_MODEL_FALLBACK:
                    resolved_model = settings.LLM_MODEL_FALLBACK
                response = self._call_provider(
                    provider,
                    messages,
                    resolved_model,
                    json_schema=json_schema,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    seed=seed,
                    timeout=timeout,
                )
                state.reset()
                self._log_usage(response, provider, messages)
                return response
            except Exception as exc:
                last_error = exc
                self._register_failure(state, exc)
                if provider == self.primary and self.fallback:
                    continue
                raise

        raise last_error or RuntimeError("LLM request failed")

    def _register_failure(self, state: CircuitState, exc: Exception):
        state.failures += 1
        if state.failures >= 3:
            state.open_for(60)
        logger.warning("LLM provider failure: %s", exc)

    def _build_provider(self, name: str) -> Optional[ProviderConfig]:
        name = (name or "").lower().strip()
        if name == "yandex":
            if not settings.YANDEX_API_KEY or not settings.YANDEX_FOLDER_ID:
                return None
            if "foundationModels" in settings.YANDEX_BASE_URL:
                headers = {
                    "Authorization": f"Api-Key {settings.YANDEX_API_KEY}",
                    "x-folder-id": settings.YANDEX_FOLDER_ID,
                }
            else:
                headers = {
                    "Authorization": f"Bearer {settings.YANDEX_API_KEY}",
                    "OpenAI-Project": settings.YANDEX_FOLDER_ID,
                }
            return ProviderConfig(
                name="yandex",
                base_url=settings.YANDEX_BASE_URL,
                api_key=settings.YANDEX_API_KEY,
                default_model=settings.YANDEX_MODEL,
                headers=headers,
            )
        if name == "openrouter":
            if not settings.OPENROUTER_API_KEY:
                return None
            headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"}
            if settings.OPENROUTER_HTTP_REFERER:
                headers["HTTP-Referer"] = settings.OPENROUTER_HTTP_REFERER
            if settings.OPENROUTER_X_TITLE:
                headers["X-Title"] = settings.OPENROUTER_X_TITLE
            return ProviderConfig(
                name="openrouter",
                base_url=settings.OPENROUTER_BASE_URL,
                api_key=settings.OPENROUTER_API_KEY,
                default_model=settings.OPENROUTER_MODEL,
                headers=headers,
            )
        return None

    def _call_provider(
        self,
        provider: ProviderConfig,
        messages: List[dict],
        model: str,
        json_schema: Optional[dict],
        temperature: Optional[float],
        max_tokens: Optional[int],
        seed: Optional[int],
        timeout: Optional[int],
    ) -> Dict[str, Any]:
        if provider.name == "yandex" and "foundationModels" in provider.base_url:
            return self._call_yandex_native(
                provider,
                messages,
                model,
                json_schema=json_schema,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.LLM_TEMPERATURE,
            "max_tokens": max_tokens or settings.LLM_MAX_TOKENS,
        }
        if seed is not None:
            payload["seed"] = seed
        if json_schema:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "schema": json_schema,
                    "strict": True,
                },
            }
        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        backoff = 1
        for attempt in range(3):
            try:
                with httpx.Client(timeout=timeout or settings.LLM_TIMEOUT) as client:
                    resp = client.post(url, headers=provider.headers, json=payload)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError(
                        f"LLM error {resp.status_code}", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                data = resp.json()
                msg = data.get("choices", [{}])[0].get("message", {})
                content = msg.get("content")
                if isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, dict):
                            parts.append(str(part.get("text") or ""))
                        else:
                            parts.append(str(part))
                    content = "".join(parts)
                text = content if isinstance(content, str) else json.dumps(content or "", ensure_ascii=False)
                parsed_json = None
                if json_schema:
                    try:
                        parsed_json = self._extract_json(text)
                    except json.JSONDecodeError:
                        parsed_json = None
                return {
                    "text": text,
                    "json": parsed_json,
                    "usage": data.get("usage"),
                    "raw": data,
                    "provider": provider.name,
                    "model": model,
                }
            except httpx.HTTPStatusError as exc:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2
                last_exc = exc
            except httpx.HTTPError as exc:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2
                last_exc = exc
        raise last_exc

    def _call_yandex_native(
        self,
        provider: ProviderConfig,
        messages: List[dict],
        model: str,
        json_schema: Optional[dict],
        temperature: Optional[float],
        max_tokens: Optional[int],
        timeout: Optional[int],
    ) -> Dict[str, Any]:
        url = f\"{provider.base_url.rstrip('/')}/completion\"
        payload: Dict[str, Any] = {
            \"modelUri\": model,
            \"completionOptions\": {
                \"temperature\": temperature if temperature is not None else settings.LLM_TEMPERATURE,
                \"maxTokens\": int(max_tokens or settings.LLM_MAX_TOKENS),
            },
            \"messages\": [
                {\"role\": m.get(\"role\"), \"text\": m.get(\"content\") or \"\"} for m in messages
            ],
        }
        backoff = 1
        for attempt in range(3):
            try:
                with httpx.Client(timeout=timeout or settings.LLM_TIMEOUT) as client:
                    resp = client.post(url, headers=provider.headers, json=payload)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError(
                        f\"LLM error {resp.status_code}\", request=resp.request, response=resp
                    )
                resp.raise_for_status()
                data = resp.json()
                alt = data.get(\"result\", {}).get(\"alternatives\", [{}])[0]
                msg = alt.get(\"message\", {}) if isinstance(alt, dict) else {}
                text = msg.get(\"text\") or \"\"
                parsed_json = None
                if json_schema:
                    try:
                        parsed_json = self._extract_json(text)
                    except json.JSONDecodeError:
                        parsed_json = None
                return {
                    \"text\": text,
                    \"json\": parsed_json,
                    \"usage\": data.get(\"usage\") or data.get(\"result\", {}).get(\"usage\"),
                    \"raw\": data,
                    \"provider\": provider.name,
                    \"model\": model,
                }
            except httpx.HTTPStatusError:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2
            except httpx.HTTPError:
                if attempt == 2:
                    raise
                time.sleep(backoff)
                backoff *= 2
        raise RuntimeError(\"Yandex LLM request failed\")

    def _extract_json(self, content: Optional[str]) -> Optional[dict]:
        if not content:
            return None
        trimmed = content.strip()
        if trimmed.startswith("```"):
            trimmed = trimmed.strip("`")
            if trimmed.startswith("json"):
                trimmed = trimmed[4:].strip()
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            start = trimmed.find("{")
            end = trimmed.rfind("}")
            if start >= 0 and end > start:
                return json.loads(trimmed[start : end + 1])
            raise

    def validate_json(self, json_data: dict, validator: Optional[type[BaseModel]]) -> None:
        if not validator:
            return
        validator.model_validate(json_data)

    def _log_usage(self, response: Dict[str, Any], provider: ProviderConfig, messages: List[dict]) -> None:
        usage = response.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        estimated = False
        if total_tokens is None:
            estimated = True
            total_tokens = self._estimate_tokens(messages, response.get("text") or "")
        session = SessionLocal()
        try:
            crud.create_budget_entry(
                session,
                self.job_id,
                provider.name,
                response.get("model"),
                int(total_tokens) if total_tokens is not None else None,
                None,
                meta_json={
                    "estimated": estimated,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
            )
        finally:
            session.close()

    def _estimate_tokens(self, messages: List[dict], text: str) -> int:
        prompt_text = " ".join([m.get("content", "") for m in messages or []])
        prompt_tokens = max(1, len(prompt_text) // 4)
        completion_tokens = max(1, len(text) // 4)
        return prompt_tokens + completion_tokens

    def generate_json(
        self,
        messages: List[dict],
        schema: dict,
        validator: Optional[type[BaseModel]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        seed: Optional[int] = None,
        timeout: Optional[int] = None,
        repair_model: Optional[str] = None,
    ) -> dict:
        response = self.generate(
            messages,
            model=model,
            json_schema=schema,
            temperature=temperature,
            max_tokens=max_tokens,
            seed=seed,
            timeout=timeout,
        )
        data = response.get("json") or {}
        try:
            self.validate_json(data, validator)
            return data
        except ValidationError as err:
            if not repair_model:
                raise
            logger.warning("LLM JSON invalid, repairing: %s", err)
            repair_messages = [
                {"role": "system", "content": "Исправь JSON строго по схеме. Без лишних полей."},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"error": str(err), "original": data, "raw_text": response.get("text")},
                        ensure_ascii=False,
                    ),
                },
            ]
            response = self.generate(
                repair_messages,
                model=repair_model,
                json_schema=schema,
                temperature=0.2,
                max_tokens=max_tokens,
                seed=seed,
                timeout=timeout,
            )
            data = response.get("json") or {}
            self.validate_json(data, validator)
            return data
