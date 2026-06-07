import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.llm.models import LLMModelPreset, LLMProviderConfig, LLMSettings


class Command(BaseCommand):
    help = "Initialize local development data idempotently."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "rexileer")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "0528")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
        User = get_user_model()
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Created superuser {username}"))
        else:
            self.stdout.write(f"Superuser {username} already exists")

        openai_provider, _ = LLMProviderConfig.objects.get_or_create(
            name="OpenAI",
            defaults={"provider_type": LLMProviderConfig.ProviderType.OPENAI, "api_key": ""},
        )
        openrouter_provider, _ = LLMProviderConfig.objects.get_or_create(
            name="OpenRouter",
            defaults={"provider_type": LLMProviderConfig.ProviderType.OPENROUTER, "api_key": ""},
        )
        presets = [
            (openai_provider, "OpenAI cheap placeholder", "gpt-4.1-mini", LLMModelPreset.Tier.FREE_OR_CHEAP, 10),
            (openai_provider, "OpenAI medium placeholder", "gpt-4.1", LLMModelPreset.Tier.MEDIUM, 20),
            (openai_provider, "OpenAI advanced placeholder", "o-series-model", LLMModelPreset.Tier.HEAVY, 30),
            (
                openrouter_provider,
                "OpenRouter free model 1",
                "openrouter/free-model-placeholder-1",
                LLMModelPreset.Tier.FREE_OR_CHEAP,
                10,
            ),
            (
                openrouter_provider,
                "OpenRouter free model 2",
                "openrouter/free-model-placeholder-2",
                LLMModelPreset.Tier.FREE_OR_CHEAP,
                20,
            ),
        ]
        for provider, label, model_id, tier, priority in presets:
            LLMModelPreset.objects.get_or_create(
                provider=provider,
                label=label,
                defaults={"model_id": model_id, "tier": tier, "priority": priority},
            )
        settings = LLMSettings.get_solo()
        if not settings.active_provider:
            settings.active_provider = openrouter_provider
            settings.save(update_fields=["active_provider", "updated_at"])
        self.stdout.write(self.style.SUCCESS("Development defaults are ready"))
