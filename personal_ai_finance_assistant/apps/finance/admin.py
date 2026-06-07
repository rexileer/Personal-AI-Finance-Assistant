from django.contrib import admin

try:
    from unfold.admin import ModelAdmin
except ImportError:  # pragma: no cover
    from django.contrib.admin import ModelAdmin

from apps.finance.models import Debt, Expense, Income, Payment


@admin.register(Debt)
class DebtAdmin(ModelAdmin):
    list_display = ("name", "debt_type", "current_balance", "next_payment_amount", "next_payment_date", "status")
    list_filter = ("debt_type", "status", "currency", "next_payment_date")
    search_fields = ("name", "lender_name", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("paid_at", "amount", "currency", "debt", "payment_type", "source")
    list_filter = ("payment_type", "currency", "paid_at")
    search_fields = ("debt__name", "source", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Income)
class IncomeAdmin(ModelAdmin):
    list_display = ("received_at", "amount", "currency", "source")
    list_filter = ("currency", "received_at")
    search_fields = ("source", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display = ("spent_at", "amount", "currency", "category")
    list_filter = ("currency", "spent_at", "category")
    search_fields = ("category", "description")
    readonly_fields = ("created_at", "updated_at")
