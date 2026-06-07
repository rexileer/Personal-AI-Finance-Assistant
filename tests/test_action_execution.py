from decimal import Decimal

import pytest
from apps.bot.models import BotAction
from apps.bot.services.actions import execute_bot_action
from apps.finance.models import Debt, Income, Payment
from django.utils import timezone


@pytest.mark.django_db
def test_bot_action_execution_creates_debt():
    action = BotAction.objects.create(
        telegram_user_id=123,
        action_type=BotAction.ActionType.CREATE_DEBT,
        payload={
            "name": "Credit card",
            "debt_type": "credit_card",
            "current_balance": "185405",
            "next_payment_amount": "12444",
            "next_payment_date": str(timezone.localdate()),
        },
        user_message="add debt",
        user_facing_summary="Create debt",
        confidence=0.95,
    )

    result = execute_bot_action(action)

    assert result.success is True
    assert Debt.objects.filter(name="Credit card", current_balance=Decimal("185405.00")).exists()
    action.refresh_from_db()
    assert action.status == BotAction.Status.EXECUTED
    assert action.executed_at is not None


@pytest.mark.django_db
def test_bot_action_execution_creates_payment_and_reduces_debt():
    debt = Debt.objects.create(
        name="Credit card",
        debt_type=Debt.DebtType.CREDIT_CARD,
        current_balance=Decimal("185405.00"),
    )
    action = BotAction.objects.create(
        telegram_user_id=123,
        action_type=BotAction.ActionType.CREATE_PAYMENT,
        payload={
            "debt_name": "credit card",
            "amount": "10000",
            "paid_at": str(timezone.localdate()),
            "payment_type": "required_payment",
        },
        user_message="paid 10000",
        user_facing_summary="Create payment",
        confidence=0.95,
    )

    result = execute_bot_action(action)

    assert result.success is True
    assert Payment.objects.filter(debt=debt, amount=Decimal("10000.00")).exists()
    debt.refresh_from_db()
    assert debt.current_balance == Decimal("175405.00")


@pytest.mark.django_db
def test_bot_action_execution_creates_income():
    action = BotAction.objects.create(
        telegram_user_id=123,
        action_type=BotAction.ActionType.CREATE_INCOME,
        payload={
            "amount": "12000",
            "received_at": str(timezone.localdate()),
            "source": "BOZON project",
        },
        user_message="income",
        user_facing_summary="Create income",
        confidence=0.95,
    )

    result = execute_bot_action(action)

    assert result.success is True
    assert Income.objects.filter(source="BOZON project", amount=Decimal("12000.00")).exists()
