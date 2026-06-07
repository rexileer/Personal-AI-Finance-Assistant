from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class LLMProviderConfig(TimeStampedModel):
    class ProviderType(models.TextChoices):
        OPENAI = "openai", _("OpenAI")
        OPENROUTER = "openrouter", _("OpenRouter")

    name = models.CharField(_("name"), max_length=255)
    provider_type = models.CharField(_("provider type"), max_length=32, choices=ProviderType.choices)
    api_key = models.CharField(_("API key"), max_length=512, blank=True)
    base_url = models.URLField(_("base URL"), blank=True)
    is_active = models.BooleanField(_("is active"), default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("LLM provider")
        verbose_name_plural = _("LLM providers")

    def __str__(self) -> str:
        return self.name


class LLMModelPreset(TimeStampedModel):
    class Tier(models.TextChoices):
        FREE_OR_CHEAP = "free_or_cheap", _("Free or cheap")
        MEDIUM = "medium", _("Medium")
        HEAVY = "heavy", _("Heavy")
        CUSTOM = "custom", _("Custom")

    provider = models.ForeignKey(LLMProviderConfig, on_delete=models.CASCADE, related_name="model_presets")
    label = models.CharField(_("label"), max_length=255)
    model_id = models.CharField(_("model ID"), max_length=255)
    tier = models.CharField(_("tier"), max_length=32, choices=Tier.choices, default=Tier.FREE_OR_CHEAP)
    is_active = models.BooleanField(_("is active"), default=True)
    priority = models.PositiveIntegerField(_("priority"), default=100)

    class Meta:
        ordering = ["provider", "tier", "priority", "label"]
        verbose_name = _("LLM model preset")
        verbose_name_plural = _("LLM model presets")

    def __str__(self) -> str:
        return f"{self.label} ({self.model_id})"


class LLMSettings(TimeStampedModel):
    active_provider = models.ForeignKey(LLMProviderConfig, on_delete=models.SET_NULL, null=True, blank=True)
    active_tier = models.CharField(
        _("active tier"),
        max_length=32,
        choices=LLMModelPreset.Tier.choices,
        default=LLMModelPreset.Tier.FREE_OR_CHEAP,
    )
    custom_model_id = models.CharField(_("custom model ID"), max_length=255, blank=True)
    use_rotation_for_openrouter_free_models = models.BooleanField(
        _("use rotation for OpenRouter free models"),
        default=True,
    )
    max_retries = models.PositiveIntegerField(_("max retries"), default=2)
    temperature = models.FloatField(_("temperature"), default=0)

    class Meta:
        verbose_name = _("LLM settings")
        verbose_name_plural = _("LLM settings")

    def __str__(self) -> str:
        return "LLM settings"

    @classmethod
    def get_solo(cls) -> "LLMSettings":
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
