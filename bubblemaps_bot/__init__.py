import sys
import logging
from logging.config import fileConfig
from pathlib import Path
from typing import Final, Optional

from telegram.constants import ParseMode
from telegram.ext import Application, Defaults

from bubblemaps_bot.utils.yaml import load_config

fileConfig('logging.ini')
log = logging.getLogger('[BUBBLEMAPS]')

base_config = load_config("config.yaml")
telegram_config = base_config["telegram"]

BOT_TOKEN: Final[str] = telegram_config["bot_token"]
DROP_UPDATES: Final[bool] = telegram_config.get("drop_updates", True)
WEBHOOK: Final[bool] = telegram_config.get("webhook", False)
WEBHOOK_URL: Final[str] = telegram_config.get("webhook_url", "")
WEBHOOK_PORT: Final[int] = telegram_config.get("webhook_port", 443)
WEBHOOK_CERT_PATH: Final[Optional[str]] = telegram_config.get("webhook_cert_path")
BOT_API_URL: Final[str] = telegram_config.get(
    "bot_api_url") or "https://api.telegram.org/bot"
BOT_API_FILE_URL: Final[str] = telegram_config.get(
    "bot_api_file_url") or "https://api.telegram.org/file/bot"

application_defaults = Defaults(
    parse_mode=ParseMode.HTML,
    # disable_web_page_preview=True,
    do_quote=True,
    allow_sending_without_reply=True,
)

builder = Application.builder()
builder.token(token=BOT_TOKEN)
builder.base_file_url(base_file_url=BOT_API_FILE_URL)
builder.base_url(base_url=BOT_API_URL)
builder.connect_timeout(connect_timeout=10)
builder.read_timeout(read_timeout=10)
builder.defaults(defaults=application_defaults)
application = builder.build()