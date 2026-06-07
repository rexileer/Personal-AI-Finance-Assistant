from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from apps.finance.models import Debt, Expense, Income, Payment


def _sum(queryset, field: str = "amount") -> Decimal:
    return queryset.aggregate(total=Sum(field))["total"] or Decimal("0")


def analytics_dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    active_debts = Debt.objects.filter(status=Debt.Status.ACTIVE)
    upcoming_7_end = today + timedelta(days=7)
    upcoming_30_end = today + timedelta(days=30)
    payments_month = Payment.objects.filter(paid_at__gte=month_start, paid_at__lte=today)
    income_month = Income.objects.filter(received_at__gte=month_start, received_at__lte=today)
    expenses_month = Expense.objects.filter(spent_at__gte=month_start, spent_at__lte=today)
    context = {
        "title": "Finance analytics",
        "total_active_debt": _sum(active_debts, "current_balance"),
        "active_debt_count": active_debts.count(),
        "total_paid_month": _sum(payments_month),
        "total_income_month": _sum(income_month),
        "total_expenses_month": _sum(expenses_month),
        "net_cashflow_month": _sum(income_month) - _sum(expenses_month) - _sum(payments_month),
        "upcoming_7": active_debts.filter(
            next_payment_date__gte=today,
            next_payment_date__lte=upcoming_7_end,
        ).order_by("next_payment_date"),
        "upcoming_30": active_debts.filter(
            next_payment_date__gte=today,
            next_payment_date__lte=upcoming_30_end,
        ).order_by("next_payment_date"),
        "overdue": active_debts.filter(next_payment_date__lt=today).order_by("next_payment_date"),
        "debt_distribution": (
            active_debts.values("debt_type").annotate(total=Sum("current_balance")).order_by("debt_type")
        ),
        "monthly_payments": payments_month.select_related("debt").order_by("-paid_at"),
    }
    return render(request, "admin/analytics/dashboard.html", context)
