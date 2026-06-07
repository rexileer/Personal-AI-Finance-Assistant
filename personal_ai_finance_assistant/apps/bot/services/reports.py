from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from apps.finance.models import Debt, Expense, Income, Payment


def money(value: Decimal | int | float | None, currency: str = "RUB") -> str:
    amount = value or Decimal("0")
    return f"{amount:,.2f} {currency}".replace(",", " ")


def month_bounds():
    today = timezone.localdate()
    start = today.replace(day=1)
    return today, start


def sum_field(queryset, field: str = "amount") -> Decimal:
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0")


def summary_text() -> str:
    today, month_start = month_bounds()
    active_debt = sum_field(Debt.objects.filter(status=Debt.Status.ACTIVE), "current_balance")
    income = sum_field(Income.objects.filter(received_at__gte=month_start, received_at__lte=today))
    expenses = sum_field(Expense.objects.filter(spent_at__gte=month_start, spent_at__lte=today))
    paid = sum_field(Payment.objects.filter(paid_at__gte=month_start, paid_at__lte=today))
    nearest = (
        Debt.objects.filter(status=Debt.Status.ACTIVE, next_payment_date__isnull=False)
        .order_by("next_payment_date")
        .first()
    )
    overdue = Debt.objects.filter(status=Debt.Status.ACTIVE, next_payment_date__lt=today).count()
    nearest_text = "нет"
    if nearest:
        nearest_text = f"{nearest.name}: {money(nearest.next_payment_amount)} до {nearest.next_payment_date}"
    return "\n".join(
        [
            "Сводка:",
            f"Активный долг: {money(active_debt)}",
            f"Доходы за месяц: {money(income)}",
            f"Расходы за месяц: {money(expenses)}",
            f"Оплачено за месяц: {money(paid)}",
            f"Ближайший платеж: {nearest_text}",
            f"Просроченных платежей: {overdue}",
        ]
    )


def debts_text() -> str:
    debts = Debt.objects.filter(status=Debt.Status.ACTIVE).order_by("next_payment_date", "name")
    if not debts:
        return "Активных долгов нет."
    lines = ["Активные долги:"]
    for debt in debts:
        lines.append(
            f"- {debt.name}: баланс {money(debt.current_balance, debt.currency)}, "
            f"платеж {money(debt.next_payment_amount, debt.currency)} "
            f"до {debt.next_payment_date or 'не указано'}, "
            f"статус {debt.get_status_display()}"
        )
    return "\n".join(lines)


def payments_text(limit: int = 10) -> str:
    payments = Payment.objects.select_related("debt").order_by("-paid_at", "-created_at")[:limit]
    if not payments:
        return "Платежей пока нет."
    lines = ["Последние платежи:"]
    for payment in payments:
        target = payment.debt.name if payment.debt else payment.description or "без долга"
        lines.append(f"- {payment.paid_at}: {money(payment.amount, payment.currency)} - {target}")
    return "\n".join(lines)


def upcoming_text(days: int = 30) -> str:
    today = timezone.localdate()
    end = today + timedelta(days=days)
    debts = Debt.objects.filter(status=Debt.Status.ACTIVE, next_payment_date__gte=today, next_payment_date__lte=end)
    if not debts:
        return f"Платежей в ближайшие {days} дней нет."
    lines = [f"Платежи в ближайшие {days} дней:"]
    for debt in debts.order_by("next_payment_date", "name"):
        lines.append(f"- {debt.next_payment_date}: {debt.name} - {money(debt.next_payment_amount, debt.currency)}")
    return "\n".join(lines)


def income_text(limit: int = 10) -> str:
    today, month_start = month_bounds()
    monthly = sum_field(Income.objects.filter(received_at__gte=month_start, received_at__lte=today))
    entries = Income.objects.order_by("-received_at", "-created_at")[:limit]
    lines = [f"Доходы за месяц: {money(monthly)}"]
    for entry in entries:
        lines.append(f"- {entry.received_at}: {money(entry.amount, entry.currency)} - {entry.source}")
    return "\n".join(lines)


def expenses_text(limit: int = 10) -> str:
    today, month_start = month_bounds()
    monthly = sum_field(Expense.objects.filter(spent_at__gte=month_start, spent_at__lte=today))
    entries = Expense.objects.order_by("-spent_at", "-created_at")[:limit]
    lines = [f"Расходы за месяц: {money(monthly)}"]
    for entry in entries:
        lines.append(f"- {entry.spent_at}: {money(entry.amount, entry.currency)} - {entry.category}")
    return "\n".join(lines)
