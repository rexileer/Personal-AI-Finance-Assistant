import asyncio

from django.core.management.base import BaseCommand

from apps.bot.telegram import run_bot


class Command(BaseCommand):
    help = "Run Telegram bot polling."

    def handle(self, *args, **options):
        asyncio.run(run_bot())
