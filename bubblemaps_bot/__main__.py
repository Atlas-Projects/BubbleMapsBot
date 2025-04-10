import asyncio
from telegram import Update
from bubblemaps_bot import application, DROP_UPDATES, WEBHOOK, WEBHOOK_CERT_PATH, WEBHOOK_PORT, WEBHOOK_URL, log
from bubblemaps_bot.db.session import init_db
from bubblemaps_bot.handlers import get_all_handlers
from bubblemaps_bot.utils.screenshot import init_browser, close_browser

async def startup():
    """Initialize the bot and browser."""
    await init_db()
    await init_browser()
    bot_user = await application.bot.get_me()
    log.info(f"[BUBBLEMAPS] Running as @{bot_user.username}")

async def shutdown():
    """Clean up by closing the browser."""
    await close_browser()

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(startup())

    for handler in get_all_handlers():
        application.add_handler(handler)

    try:
        if WEBHOOK:
            loop.run_until_complete(
                application.run_webhook(
                    listen='0.0.0.0',
                    port=WEBHOOK_PORT or 443,
                    url_path=application.bot.token,
                    webhook_url=WEBHOOK_URL + application.bot.token,
                    cert=WEBHOOK_CERT_PATH,
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=DROP_UPDATES
                )
            )
        else:
            loop.run_until_complete(
                application.run_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=DROP_UPDATES
                )
            )
    except KeyboardInterrupt:
        log.info("[BUBBLEMAPS] Bot stopped by user")
    finally:
        # Ensure shutdown tasks run when the bot stops
        loop.run_until_complete(shutdown())
        loop.close()

if __name__ == "__main__":
    main()