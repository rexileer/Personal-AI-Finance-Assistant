from apps.bot.security import is_allowed_telegram_user
from django.test import override_settings


@override_settings(ALLOWED_TELEGRAM_USER_IDS={123, 456})
def test_allowed_telegram_user_returns_true_for_configured_id():
    assert is_allowed_telegram_user(123) is True


@override_settings(ALLOWED_TELEGRAM_USER_IDS={123, 456})
def test_allowed_telegram_user_returns_false_for_unknown_id():
    assert is_allowed_telegram_user(789) is False
