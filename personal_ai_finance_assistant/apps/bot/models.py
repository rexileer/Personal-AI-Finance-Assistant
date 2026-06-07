from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class BotMessage(models.Model):
    class Direction(models.TextChoices):
        INCOMING = "incoming", _("Incoming")
        OUTGOING = "outgoing", _("Outgoing")

    telegram_user_id = models.BigIntegerField(_("Telegram user ID"))
    direction = models.CharField(_("direction"), max_length=16, choices=Direction.choices)
    text = models.TextField(_("text"))
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Bot message")
        verbose_name_plural = _("Bot messages")

    def __str__(self) -> str:
        return f"{self.direction} {self.telegram_user_id}: {self.text[:50]}"


class BotAction(TimeStampedModel):
    class ActionType(models.TextChoices):
        CREATE_DEBT = "create_debt", _("Create debt")
        UPDATE_DEBT = "update_debt", _("Update debt")
        CLOSE_DEBT = "close_debt", _("Close debt")
        CREATE_PAYMENT = "create_payment", _("Create payment")
        CREATE_INCOME = "create_income", _("Create income")
        CREATE_EXPENSE = "create_expense", _("Create expense")
        SHOW_SUMMARY = "show_summary", _("Show summary")
        SHOW_DEBTS = "show_debts", _("Show debts")
        SHOW_PAYMENTS = "show_payments", _("Show payments")
        SHOW_UPCOMING_PAYMENTS = "show_upcoming_payments", _("Show upcoming payments")
        SHOW_INCOME = "show_income", _("Show income")
        SHOW_EXPENSES = "show_expenses", _("Show expenses")
        ASK_CLARIFICATION = "ask_clarification", _("Ask clarification")
        NO_ACTION = "no_action", _("No action")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        REJECTED = "rejected", _("Rejected")
        EXECUTED = "executed", _("Executed")
        FAILED = "failed", _("Failed")

    telegram_user_id = models.BigIntegerField(_("Telegram user ID"))
    action_type = models.CharField(_("action type"), max_length=32, choices=ActionType.choices)
    status = models.CharField(_("status"), max_length=16, choices=Status.choices, default=Status.PENDING)
    payload = models.JSONField(_("payload"), default=dict, blank=True)
    llm_raw_response = models.TextField(_("LLM raw response"), blank=True)
    user_message = models.TextField(_("user message"), blank=True)
    user_facing_summary = models.TextField(_("user-facing summary"), blank=True)
    error_message = models.TextField(_("error message"), blank=True)
    confidence = models.FloatField(_("confidence"), default=0)
    executed_at = models.DateTimeField(_("executed at"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Bot action")
        verbose_name_plural = _("Bot actions")

    def __str__(self) -> str:
        return f"{self.action_type} ({self.status})"
