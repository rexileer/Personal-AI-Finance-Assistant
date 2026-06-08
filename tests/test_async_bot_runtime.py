from datetime import date

import pytest
from apps.llm.schemas import FinanceAssistantAction
from apps.llm.services import parse_finance_message


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_parse_finance_message_without_provider_is_safe_in_async_context():
    action = await parse_finance_message("Добавь расход 100 на кофе", date(2026, 6, 8))

    assert isinstance(action, FinanceAssistantAction)
    assert action.action_type == "ask_clarification"
    assert "LLM" in action.clarification_question
