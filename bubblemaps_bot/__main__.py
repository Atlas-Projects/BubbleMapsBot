import asyncio
from telegram import Update, BotCommand
from telegram.ext import Application

from bubblemaps_bot import (
    DROP_UPDATES,
    WEBHOOK,
    WEBHOOK_CERT_PATH,
    WEBHOOK_PORT,
    WEBHOOK_URL,
    builder,
    log,
)
from bubblemaps_bot.db.session import init_db
from bubblemaps_bot.handlers import get_all_handlers
from bubblemaps_bot.utils.screenshot import init_browser
from bubblemaps_bot.utils.valkey import shutdown_valkey

builder.post_shutdown(shutdown_valkey)
application = builder.build()

async def startup():
    """Initialize the bot, browser, and set bot commands."""
    await init_db()
    await init_browser()
    bot_user = await application.bot.get_me()
    log.info(f"[BUBBLEMAPS] Running as @{bot_user.username}")

    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("help", "Show available commands"),
        BotCommand("check", "View token details"),
        BotCommand("mapshot", "Get an interactive Bubblemap"),
        BotCommand("meta", "Get token metadata"),
        BotCommand("distribution", "Get token distribution info"),
        BotCommand("coin", "Price and market data"),
        BotCommand("address", "Fetch address details for a token"),
        BotCommand("clear", "Clear the Valkey cache"),
    ]

    try:
        await application.bot.set_my_commands(commands)
        log.info("[BUBBLEMAPS] Bot commands set successfully")
    except Exception as e:
        log.error(f"[BUBBLEMAPS] Failed to set bot commands: {e}")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(startup())

    for handler in get_all_handlers():
        application.add_handler(handler)

    try:
        if WEBHOOK:
            application.run_webhook(
                listen="0.0.0.0",
                port=WEBHOOK_PORT or 443,
                url_path=application.bot.token,
                webhook_url=WEBHOOK_URL + application.bot.token,
                cert=WEBHOOK_CERT_PATH,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=DROP_UPDATES,
            )
        else:
            application.run_polling(
                allowed_updates=Update.ALL_TYPES, drop_pending_updates=DROP_UPDATES
            )
    except KeyboardInterrupt:
        log.info("[BUBBLEMAPS] Bot stopped by user")

if __name__ == "__main__":
    main()