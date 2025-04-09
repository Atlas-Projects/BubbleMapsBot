
from telegram.ext import BaseHandler

from bubblemaps_bot.handlers import start, metadata, mapshot, address

def get_all_handlers() -> list[BaseHandler]:
    handlers = []

    handlers.extend(start.get_handlers())
    handlers.extend(metadata.get_handlers())
    handlers.extend(mapshot.get_handlers())
    handlers.extend(address.get_handlers())
    return handlers
