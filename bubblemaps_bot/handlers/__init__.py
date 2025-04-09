
from telegram.ext import BaseHandler

from bubblemaps_bot.handlers import start, metadata, map, mapshot

def get_all_handlers() -> list[BaseHandler]:
    handlers = []

    handlers.extend(start.get_handlers())
    handlers.extend(metadata.get_handlers())
    handlers.extend(map.get_handlers())
    handlers.extend(mapshot.get_handlers())
    return handlers
