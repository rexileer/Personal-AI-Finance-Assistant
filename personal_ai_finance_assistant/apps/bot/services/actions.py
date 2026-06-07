from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.bot.models import BotAction
from apps.finance.models import Debt, Expense, Income, Payment


@dataclass(frozen=True)
class ActionExecutionResult:
    success: bool
    message: str


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _find_debt(payload: dict[str, Any]) -> Debt | None:
    debt_id = payload.get("debt_id")
    if debt_id:
        return Debt.objects.filter(pk=debt_id, status=Debt.Status.ACTIVE).first()
    debt_name = (payload.get("debt_name") or payload.get("name") or "").strip()
    if not debt_name:
        return None
    matches = Debt.objects.filter(name__iexact=debt_name, status=Debt.Status.ACTIVE)
    if matches.count() == 1:
        return matches.first()
    contains_matches = Debt.objects.filter(name__icontains=debt_name, status=Debt.Status.ACTIVE)
    if contains_matches.count() == 1:
        return contains_matches.first()
    return None


def execute_bot_action(action: BotAction) -> ActionExecutionResult:
    if action.status != BotAction.Status.PENDING:
        return ActionExecutionResult(False, "Действие уже обработано.")

    try:
        with transaction.atomic():
            action.status = BotAction.Status.CONFIRMED
            action.save(update_fields=["status", "updated_at"])
            message = _execute(action.action_type, action.payload)
            action.status = BotAction.Status.EXECUTED
            action.executed_at = timezone.now()
            action.error_message = ""
            action.save(update_fields=["status", "executed_at", "error_message", "updated_at"])
            return ActionExecutionResult(True, message)
    except Exception as exc:  # noqa: BLE001
        action.status = BotAction.Status.FAILED
        action.error_message = str(exc)
        action.save(update_fields=["status", "error_message", "updated_at"])
        return ActionExecutionResult(False, f"Не удалось выполнить действие: {exc}")


def reject_bot_action(action: BotAction) -> None:
    if action.status == BotAction.Status.PENDING:
        action.status = BotAction.Status.REJECTED
        action.save(update_fields=["status", "updated_at"])


def _execute(action_type: str, payload: dict[str, Any]) -> str:
    handlers = {
        BotAction.ActionType.CREATE_DEBT: _create_debt,
        BotAction.ActionType.UPDATE_DEBT: _update_debt,
        BotAction.ActionType.CLOSE_DEBT: _close_debt,
        BotAction.ActionType.CREATE_PAYMENT: _create_payment,
        BotAction.ActionType.CREATE_INCOME: _create_income,
        BotAction.ActionType.CREATE_EXPENSE: _create_expense,
    }
    handler = handlers.get(action_type)
    if not handler:
        raise ValueError(f"Unsupported executable action type: {action_type}")
    return handler(payload)


def _create_debt(payload: dict[str, Any]) -> str:
    debt = Debt.objects.create(
        name=payload["name"],
        debt_type=payload.get("debt_type", Debt.DebtType.OTHER),
        principal_amount=_decimal(payload["principal_amount"]) if payload.get("principal_amount") else None,
        current_balance=_decimal(payload["current_balance"]),
        next_payment_amount=_decimal(payload["next_payment_amount"]) if payload.get("next_payment_amount") else None,
        next_payment_date=payload.get("next_payment_date") or None,
        interest_rate=_decimal(payload["interest_rate"]) if payload.get("interest_rate") else None,
        currency=payload.get("currency", "RUB"),
        lender_name=payload.get("lender_name", ""),
        description=payload.get("description", ""),
    )
    return f"Долг «{debt.name}» создан."


def _update_debt(payload: dict[str, Any]) -> str:
    debt = _find_debt(payload)
    if not debt:
        raise ValueError("Не найден долг для обновления.")
    for field in [
        "name",
        "debt_type",
        "principal_amount",
        "current_balance",
        "next_payment_amount",
        "next_payment_date",
        "interest_rate",
        "currency",
        "lender_name",
        "description",
        "status",
    ]:
        if field in payload and payload[field] not in ("", None):
            value = payload[field]
            if field in {"principal_amount", "current_balance", "next_payment_amount", "interest_rate"}:
                value = _decimal(value)
            setattr(debt, field, value)
    debt.save()
    return f"Долг «{debt.name}» обновлен."


def _close_debt(payload: dict[str, Any]) -> str:
    debt = _find_debt(payload)
    if not debt:
        raise ValueError("Не найден долг для закрытия.")
    debt.status = Debt.Status.CLOSED
    debt.current_balance = Decimal("0")
    debt.save(update_fields=["status", "current_balance", "updated_at"])
    return f"Долг «{debt.name}» закрыт."


def _create_payment(payload: dict[str, Any]) -> str:
    debt = _find_debt(payload)
    if (payload.get("debt_name") or payload.get("debt_id")) and not debt:
        raise ValueError("Не удалось однозначно найти долг для платежа.")
    payment = Payment.objects.create(
        debt=debt,
        amount=_decimal(payload["amount"]),
        currency=payload.get("currency", "RUB"),
        paid_at=payload.get("paid_at") or timezone.localdate(),
        payment_type=payload.get("payment_type", Payment.PaymentType.REQUIRED_PAYMENT),
        source=payload.get("source", ""),
        description=payload.get("description", ""),
        reduce_debt_balance=payload.get("reduce_debt_balance", True),
    )
    if payment.debt:
        return f"Платеж {payment.amount} {payment.currency} по «{payment.debt.name}» записан."
    return f"Платеж {payment.amount} {payment.currency} записан."


def _create_income(payload: dict[str, Any]) -> str:
    income = Income.objects.create(
        amount=_decimal(payload["amount"]),
        currency=payload.get("currency", "RUB"),
        received_at=payload.get("received_at") or timezone.localdate(),
        source=payload.get("source", "Без источника"),
        description=payload.get("description", ""),
    )
    return f"Доход {income.amount} {income.currency} записан."


def _create_expense(payload: dict[str, Any]) -> str:
    expense = Expense.objects.create(
        amount=_decimal(payload["amount"]),
        currency=payload.get("currency", "RUB"),
        spent_at=payload.get("spent_at") or timezone.localdate(),
        category=payload.get("category", "Прочее"),
        description=payload.get("description", ""),
    )
    return f"Расход {expense.amount} {expense.currency} записан."
