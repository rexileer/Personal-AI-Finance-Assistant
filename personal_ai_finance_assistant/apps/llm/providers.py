from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import TypeVar

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProviderError(RuntimeError):
    pass


class BaseLLMClient(ABC):
    @abstractmethod
    async def complete_structured(self, messages: list[dict], model: str, schema: type[SchemaT]) -> SchemaT:
        raise NotImplementedError


def strip_markdown_code_fences(content: str) -> str:
    content = content.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else content


def parse_structured_content(content: str, schema: type[SchemaT]) -> SchemaT:
    cleaned = strip_markdown_code_fences(content)
    data = json.loads(cleaned)
    return schema.model_validate(data)


class OpenAIProvider(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str | None = None, temperature: float = 0) -> None:
        self.api_key = api_key
        self.base_url = base_url or None
        self.temperature = temperature

    async def complete_structured(self, messages: list[dict], model: str, schema: type[SchemaT]) -> SchemaT:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:  # pragma: no cover
            raise LLMProviderError("OpenAI SDK is not installed") from exc

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise LLMProviderError("OpenAI returned an empty response")
        return parse_structured_content(content, schema)


class OpenRouterProvider(BaseLLMClient):
    def __init__(self, api_key: str, base_url: str | None = None, temperature: float = 0) -> None:
        self.api_key = api_key
        self.base_url = base_url or "https://openrouter.ai/api/v1"
        self.temperature = temperature

    async def complete_structured(self, messages: list[dict], model: str, schema: type[SchemaT]) -> SchemaT:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/rexileer/personal-ai-finance-assistant",
            "X-Title": "Personal AI Finance Assistant",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(base_url=self.base_url, timeout=45) as client:
            response = await client.post("/chat/completions", headers=headers, json=payload)
        if response.status_code >= 400:
            logger.warning("OpenRouter model %s failed with HTTP %s", model, response.status_code)
            raise LLMProviderError(f"OpenRouter HTTP {response.status_code}")
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content.strip():
            raise LLMProviderError("OpenRouter returned an empty response")
        return parse_structured_content(content, schema)
