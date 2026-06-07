from apps.llm.schemas import FinanceAssistantAction
from pydantic import ValidationError


def test_finance_assistant_action_schema_accepts_valid_action():
    action = FinanceAssistantAction.model_validate(
        {
            "action_type": "create_expense",
            "confidence": 0.9,
            "requires_confirmation": True,
            "data": {"amount": "2500", "category": "food"},
            "user_facing_summary": "Записать расход 2500 RUB на еду.",
            "clarification_question": "",
        }
    )

    assert action.action_type == "create_expense"
    assert action.confidence == 0.9


def test_finance_assistant_action_schema_rejects_unknown_action():
    try:
        FinanceAssistantAction.model_validate(
            {
                "action_type": "delete_everything",
                "confidence": 0.9,
                "requires_confirmation": True,
                "data": {},
                "user_facing_summary": "",
                "clarification_question": "",
            }
        )
    except ValidationError as exc:
        assert "action_type" in str(exc)
    else:
        raise AssertionError("Unknown action should be rejected")
