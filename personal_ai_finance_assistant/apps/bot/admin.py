from django.contrib import admin

try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from apps.bot.models import BotAction, BotMessage


@admin.register(BotMessage)
class BotMessageAdmin(ModelAdmin):
    list_display = ("created_at", "telegram_user_id", "direction", "short_text")
    list_filter = ("direction", "created_at")
    search_fields = ("telegram_user_id", "text")
    readonly_fields = ("created_at",)

    @admin.display(description="Text")
    def short_text(self, obj):
        return obj.text[:80]


@admin.register(BotAction)
class BotActionAdmin(ModelAdmin):
    list_display = ("created_at", "telegram_user_id", "action_type", "status", "confidence", "executed_at")
    list_filter = ("action_type", "status", "created_at", "executed_at")
    search_fields = ("telegram_user_id", "user_message", "user_facing_summary", "error_message")
    readonly_fields = ("created_at", "updated_at", "executed_at")
