from decimal import Decimal

import pytest
from apps.finance.models import Debt, Payment
from django.utils import timezone


@pytest.mark.django_db
def test_debt_can_be_created_with_active_status():
    debt = Debt.objects.create(
        name="Credit card",
        debt_type=Debt.DebtType.CREDIT_CARD,
        current_balance=Decimal("185405.00"),
        next_payment_amount=Decimal("12444.00"),
        next_payment_date=timezone.localdate(),
    )

    assert debt.status == Debt.Status.ACTIVE
    assert debt.currency == "RUB"
    assert debt.current_balance == Decimal("185405.00")


@pytest.mark.django_db
def test_payment_linked_to_debt_reduces_current_balance():
    debt = Debt.objects.create(
        name="Credit card",
        debt_type=Debt.DebtType.CREDIT_CARD,
        current_balance=Decimal("185405.00"),
    )

    Payment.objects.create(
        debt=debt,
        amount=Decimal("10000.00"),
        paid_at=timezone.localdate(),
        payment_type=Payment.PaymentType.REQUIRED_PAYMENT,
    )

    debt.refresh_from_db()
    assert debt.current_balance == Decimal("175405.00")
