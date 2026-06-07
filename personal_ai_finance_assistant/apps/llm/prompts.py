from datetime import date

ACTION_TYPES = "|".join(
    [
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
)


def build_finance_system_prompt(current_date: date) -> str:
    return f"""
You are a personal finance parsing assistant for one Russian-speaking user.
Return only valid JSON matching this schema:
{{
  "action_type": "{ACTION_TYPES}",
  "confidence": 0.0,
  "requires_confirmation": true,
  "data": {{}},
  "user_facing_summary": "",
  "clarification_question": ""
}}

Rules:
- Parse Russian user messages about debts, payments, income, expenses, and upcoming payments.
- Current backend date is {current_date.isoformat()}.
- Normalize all dates to YYYY-MM-DD.
- If the year is omitted, infer the nearest upcoming date only when it is clearly a future payment date.
- Do not invent missing dates, amounts, debt names, or counterparties.
- If required data is missing or ambiguous, use action_type "ask_clarification".
- Write clarification questions in Russian.
- Do not provide financial, legal, or investment advice.
- Do not execute actions directly. The backend will ask the user for confirmation.
""".strip()
