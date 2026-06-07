from typing import Any, Literal

from pydantic import BaseModel, Field

AllowedActionType = Literal[
    "create_debt",
    "update_debt",
    "close_debt",
    "create_payment",
    "create_income",
    "create_expense",
    "show_summary",
    "show_debts",
    "show_payments",
    "show_upcoming_payments",
    "show_income",
    "show_expenses",
    "ask_clarification",
    "no_action",
]


class FinanceAssistantAction(BaseModel):
    action_type: AllowedActionType
    confidence: float = Field(ge=0, le=1)
    requires_confirmation: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
    user_facing_summary: str = ""
    clarification_question: str = ""
