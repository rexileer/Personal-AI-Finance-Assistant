from __future__ import annotations

import logging
from datetime import date

from pydantic import ValidationError

from apps.llm.models import LLMModelPreset, LLMProviderConfig, LLMSettings
from apps.llm.prompts import build_finance_system_prompt
from apps.llm.providers import BaseLLMClient, LLMProviderError, OpenAIProvider, OpenRouterProvider
from apps.llm.schemas import FinanceAssistantAction

logger = logging.getLogger(__name__)


def get_client(provider: LLMProviderConfig, temperature: float = 0) -> BaseLLMClient:
    if provider.provider_type == LLMProviderConfig.ProviderType.OPENAI:
        return OpenAIProvider(provider.api_key, provider.base_url, temperature)
    if provider.provider_type == LLMProviderConfig.ProviderType.OPENROUTER:
        return OpenRouterProvider(provider.api_key, provider.base_url, temperature)
    raise LLMProviderError(f"Unsupported provider type: {provider.provider_type}")


def get_active_model_presets(settings: LLMSettings) -> list[LLMModelPreset]:
    if not settings.active_provider:
        return []
    qs = settings.active_provider.model_presets.filter(is_active=True)
    if settings.custom_model_id:
        return [
            LLMModelPreset(
                provider=settings.active_provider,
                label="Custom",
                model_id=settings.custom_model_id,
                tier=LLMModelPreset.Tier.CUSTOM,
                priority=0,
            )
        ]
    return list(qs.filter(tier=settings.active_tier).order_by("priority", "label"))


async def parse_finance_message(user_text: str, current_date: date) -> FinanceAssistantAction:
    settings = LLMSettings.get_solo()
    if not settings.active_provider or not settings.active_provider.api_key:
        return FinanceAssistantAction(
            action_type="ask_clarification",
            confidence=0,
            requires_confirmation=False,
            data={},
            user_facing_summary="",
            clarification_question="LLM-провайдер не настроен. Настройте API-ключ в админке.",
        )

    messages = [
        {"role": "system", "content": build_finance_system_prompt(current_date)},
        {"role": "user", "content": user_text},
    ]
    presets = get_active_model_presets(settings)
    if not presets:
        return FinanceAssistantAction(
            action_type="ask_clarification",
            confidence=0,
            requires_confirmation=False,
            data={},
            user_facing_summary="",
            clarification_question="Активная LLM-модель не настроена в админке.",
        )

    max_attempts = max(1, settings.max_retries + 1)
    for preset in presets[:max_attempts]:
        logger.info("Trying LLM model preset '%s' (%s)", preset.label, preset.model_id)
        client = get_client(settings.active_provider, settings.temperature)
        try:
            return await client.complete_structured(messages, preset.model_id, FinanceAssistantAction)
        except (LLMProviderError, ValidationError, ValueError) as exc:
            logger.warning("LLM model '%s' failed: %s", preset.model_id, exc)

    return FinanceAssistantAction(
        action_type="ask_clarification",
        confidence=0,
        requires_confirmation=False,
        data={},
        user_facing_summary="",
        clarification_question="Не удалось надежно разобрать сообщение. Пожалуйста, переформулируйте.",
    )
