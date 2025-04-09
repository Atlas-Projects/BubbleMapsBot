import asyncio
from telegram import Update
from bubblemaps_bot import application, DROP_UPDATES, WEBHOOK, WEBHOOK_CERT_PATH, WEBHOOK_PORT, WEBHOOK_URL, log
from bubblemaps_bot.db.session import init_db
from bubblemaps_bot.handlers import get_all_handlers

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(init_db())
    
    bot_user = loop.run_until_complete(application.bot.get_me())
    log.info(f"[BUBBLEMAPS] Running as @{bot_user.username}")

    for handler in get_all_handlers():
        application.add_handler(handler)

    if WEBHOOK:
        application.run_webhook(
            listen='0.0.0.0',
            port=WEBHOOK_PORT or 443,
            url_path=application.bot.token,
            webhook_url=WEBHOOK_URL + application.bot.token,
            cert=WEBHOOK_CERT_PATH,
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=DROP_UPDATES
        )
    else:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=DROP_UPDATES
        )

if __name__ == "__main__":
    main()
