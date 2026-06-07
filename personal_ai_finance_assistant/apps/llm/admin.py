from django.contrib import admin

try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from apps.llm.models import LLMModelPreset, LLMProviderConfig, LLMSettings


@admin.register(LLMProviderConfig)
class LLMProviderConfigAdmin(ModelAdmin):
    list_display = ("name", "provider_type", "base_url", "is_active", "created_at")
    list_filter = ("provider_type", "is_active")
    search_fields = ("name", "base_url")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LLMModelPreset)
class LLMModelPresetAdmin(ModelAdmin):
    list_display = ("label", "provider", "model_id", "tier", "priority", "is_active")
    list_filter = ("provider", "tier", "is_active")
    search_fields = ("label", "model_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LLMSettings)
class LLMSettingsAdmin(ModelAdmin):
    list_display = ("active_provider", "active_tier", "custom_model_id", "max_retries", "temperature")
    list_filter = ("active_tier", "use_rotation_for_openrouter_free_models")
    readonly_fields = ("created_at", "updated_at")
