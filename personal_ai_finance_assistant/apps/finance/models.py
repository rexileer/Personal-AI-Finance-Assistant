from decimal import Decimal

from django.db import models, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class Debt(TimeStampedModel):
    class DebtType(models.TextChoices):
        CREDIT_CARD = "credit_card", _("Credit card")
        LOAN = "loan", _("Loan")
        INSTALLMENT = "installment", _("Installment")
        PERSONAL_DEBT = "personal_debt", _("Personal debt")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        CLOSED = "closed", _("Closed")
        ARCHIVED = "archived", _("Archived")

    name = models.CharField(_("name"), max_length=255)
    debt_type = models.CharField(_("debt type"), max_length=32, choices=DebtType.choices, default=DebtType.OTHER)
    principal_amount = models.DecimalField(
        _("principal amount"), max_digits=14, decimal_places=2, null=True, blank=True
    )
    current_balance = models.DecimalField(_("current balance"), max_digits=14, decimal_places=2)
    next_payment_amount = models.DecimalField(
        _("next payment amount"), max_digits=14, decimal_places=2, null=True, blank=True
    )
    next_payment_date = models.DateField(_("next payment date"), null=True, blank=True)
    interest_rate = models.DecimalField(_("interest rate"), max_digits=6, decimal_places=2, null=True, blank=True)
    currency = models.CharField(_("currency"), max_length=3, default="RUB")
    lender_name = models.CharField(_("lender name"), max_length=255, blank=True)
    description = models.TextField(_("description"), blank=True)
    status = models.CharField(_("status"), max_length=16, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["next_payment_date", "name"]
        verbose_name = _("Debt")
        verbose_name_plural = _("Debts")

    def __str__(self) -> str:
        return self.name


class Payment(TimeStampedModel):
    class PaymentType(models.TextChoices):
        REQUIRED_PAYMENT = "required_payment", _("Required payment")
        EARLY_REPAYMENT = "early_repayment", _("Early repayment")
        INTEREST = "interest", _("Interest")
        FEE = "fee", _("Fee")
        OTHER = "other", _("Other")

    debt = models.ForeignKey(Debt, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    amount = models.DecimalField(_("amount"), max_digits=14, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=3, default="RUB")
    paid_at = models.DateField(_("paid at"))
    payment_type = models.CharField(
        _("payment type"), max_length=32, choices=PaymentType.choices, default=PaymentType.REQUIRED_PAYMENT
    )
    source = models.CharField(_("source"), max_length=255, blank=True)
    description = models.TextField(_("description"), blank=True)
    reduce_debt_balance = models.BooleanField(_("reduce debt balance"), default=True)

    class Meta:
        ordering = ["-paid_at", "-created_at"]
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency} on {self.paid_at}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        with transaction.atomic():
            super().save(*args, **kwargs)
            if is_new and self.debt_id and self.reduce_debt_balance:
                Debt.objects.filter(pk=self.debt_id).update(current_balance=F("current_balance") - Decimal(self.amount))


class Income(TimeStampedModel):
    amount = models.DecimalField(_("amount"), max_digits=14, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=3, default="RUB")
    received_at = models.DateField(_("received at"))
    source = models.CharField(_("source"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        ordering = ["-received_at", "-created_at"]
        verbose_name = _("Income")
        verbose_name_plural = _("Income")

    def __str__(self) -> str:
        return f"{self.source}: {self.amount} {self.currency}"


class Expense(TimeStampedModel):
    amount = models.DecimalField(_("amount"), max_digits=14, decimal_places=2)
    currency = models.CharField(_("currency"), max_length=3, default="RUB")
    spent_at = models.DateField(_("spent at"))
    category = models.CharField(_("category"), max_length=255)
    description = models.TextField(_("description"), blank=True)

    class Meta:
        ordering = ["-spent_at", "-created_at"]
        verbose_name = _("Expense")
        verbose_name_plural = _("Expenses")

    def __str__(self) -> str:
        return f"{self.category}: {self.amount} {self.currency}"
