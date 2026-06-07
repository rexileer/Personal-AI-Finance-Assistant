from django.conf import settings

DENIED_MESSAGE_RU = "Нет доступа к этому боту."


def is_allowed_telegram_user(telegram_user_id: int) -> bool:
    allowed_ids = getattr(settings, "ALLOWED_TELEGRAM_USER_IDS", set())
    return int(telegram_user_id) in allowed_ids
