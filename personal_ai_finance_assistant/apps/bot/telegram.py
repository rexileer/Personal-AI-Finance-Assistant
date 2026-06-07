from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from django.conf import settings
from django.utils import timezone

from apps.bot.models import BotAction, BotMessage
from apps.bot.security import DENIED_MESSAGE_RU, is_allowed_telegram_user
from apps.bot.services.actions import execute_bot_action, reject_bot_action
from apps.bot.services.reports import debts_text, expenses_text, income_text, payments_text, summary_text, upcoming_text
from apps.llm.services import parse_finance_message

logger = logging.getLogger(__name__)
router = Router()


HELP_TEXT = """
Я помогу вести долги, платежи, доходы и расходы.

Команды:
/summary - сводка
/debts - активные долги
/payments - последние платежи
/upcoming - ближайшие платежи
/income - доходы
/expenses - расходы
/cancel - отменить последнее ожидающее действие

Примеры:
Добавь долг по кредитке 185405, заплатить надо 12444 5 июня
Я оплатил 10000 по кредитке
Добавь доход 12000 за проект БОЗОН
Запиши расход 2500 на еду
Что нужно оплатить в ближайшие 7 дней?
""".strip()


def _allowed(message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else 0
    return is_allowed_telegram_user(user_id)


async def _reply(message: Message, text: str, **kwargs) -> None:
    user_id = message.from_user.id if message.from_user else 0
    BotMessage.objects.create(telegram_user_id=user_id, direction=BotMessage.Direction.OUTGOING, text=text)
    await message.answer(text, **kwargs)


@router.message(Command("start"))
async def start(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, "Готов помогать с личными финансами. Напишите /help для примеров.")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, HELP_TEXT)


@router.message(Command("summary"))
async def summary(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, summary_text())


@router.message(Command("debts"))
async def debts(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, debts_text())


@router.message(Command("payments"))
async def payments(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, payments_text())


@router.message(Command("upcoming"))
async def upcoming(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, upcoming_text())


@router.message(Command("income"))
async def income(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, income_text())


@router.message(Command("expenses"))
async def expenses(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    await _reply(message, expenses_text())


@router.message(Command("cancel"))
async def cancel(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    user_id = message.from_user.id if message.from_user else 0
    action = BotAction.objects.filter(telegram_user_id=user_id, status=BotAction.Status.PENDING).first()
    if action:
        reject_bot_action(action)
        await _reply(message, "Окей, действие отменено.")
    else:
        await _reply(message, "Нет ожидающих действий.")


@router.message(F.text)
async def natural_language_message(message: Message) -> None:
    if not _allowed(message):
        await message.answer(DENIED_MESSAGE_RU)
        return
    user_id = message.from_user.id if message.from_user else 0
    text = message.text or ""
    BotMessage.objects.create(telegram_user_id=user_id, direction=BotMessage.Direction.INCOMING, text=text)
    try:
        parsed = await parse_finance_message(text, timezone.localdate())
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to parse message")
        await _reply(message, f"Не удалось разобрать сообщение: {exc}")
        return

    if parsed.action_type in {"ask_clarification", "no_action"} or parsed.confidence < 0.6:
        question = parsed.clarification_question or "Уточните, пожалуйста, сумму, дату или название долга."
        await _reply(message, question)
        return

    if parsed.action_type.startswith("show_"):
        await _reply(message, _report_for_action(parsed.action_type))
        return

    action = BotAction.objects.create(
        telegram_user_id=user_id,
        action_type=parsed.action_type,
        payload=parsed.data,
        user_message=text,
        user_facing_summary=parsed.user_facing_summary,
        confidence=parsed.confidence,
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_action:{action.id}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"reject_action:{action.id}"),
            ]
        ]
    )
    await _reply(message, parsed.user_facing_summary or "Подтвердить действие?", reply_markup=keyboard)


@router.callback_query(F.data.startswith("confirm_action:"))
async def confirm_action(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not is_allowed_telegram_user(user_id):
        await callback.answer(DENIED_MESSAGE_RU, show_alert=True)
        return
    action_id = int((callback.data or "").split(":", 1)[1])
    action = BotAction.objects.filter(pk=action_id, telegram_user_id=user_id).first()
    if not action:
        await callback.message.answer("Действие не найдено.")
        return
    result = execute_bot_action(action)
    await callback.message.answer(result.message)
    await callback.answer()


@router.callback_query(F.data.startswith("reject_action:"))
async def reject_action(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    if not is_allowed_telegram_user(user_id):
        await callback.answer(DENIED_MESSAGE_RU, show_alert=True)
        return
    action_id = int((callback.data or "").split(":", 1)[1])
    action = BotAction.objects.filter(pk=action_id, telegram_user_id=user_id).first()
    if action:
        reject_bot_action(action)
    await callback.message.answer("Окей, действие отменено.")
    await callback.answer()


def _report_for_action(action_type: str) -> str:
    return {
        "show_summary": summary_text,
        "show_debts": debts_text,
        "show_payments": payments_text,
        "show_upcoming_payments": upcoming_text,
        "show_income": income_text,
        "show_expenses": expenses_text,
    }[action_type]()


async def run_bot() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)
    await dispatcher.start_polling(bot)
