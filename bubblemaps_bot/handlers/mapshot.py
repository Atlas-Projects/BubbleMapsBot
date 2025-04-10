from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from bubblemaps_bot.utils.screenshot import capture_bubblemap, build_iframe_url, check_map_availability
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains
import asyncio

async def mapshot_worker(chat_id: int, context: CallbackContext, chain: str, token: str):
    try:
        screenshot = await capture_bubblemap(chain, token)
        iframe_url = build_iframe_url(chain, token)

        keyboard = [[InlineKeyboardButton("🌐 View Bubblemap", url=iframe_url)]]
        markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_photo(
            chat_id=chat_id,
            photo=screenshot,
            caption=f"🗺 Bubblemap preview for <code>{token}</code> on {chain.upper()}",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Failed to generate mapshot: {e}")

async def mapshot_command(update: Update, context: CallbackContext):
    if not context.args or len(context.args) > 2:
        await update.message.reply_text("Usage: /mapshot <token_address> or /mapshot <chain> <token_address>")
        return

    if len(context.args) == 1:
        token = context.args[0]
        result = await fetch_metadata_from_all_chains(token)
        if not result:
            await update.message.reply_text("❌ Token not found on any supported chains.")
            return
        chain, _ = result
    else:
        chain, token = context.args

    available = await check_map_availability(chain, token)
    if not available:
        await update.message.reply_text(f"❌ No Bubblemap available for this token on {chain.upper()}.")
        return

    await update.message.reply_text("Generating mapshot... I’ll send it here when ready!")
    asyncio.create_task(mapshot_worker(update.effective_chat.id, context, chain, token))

def get_handlers():
    return [CommandHandler("mapshot", mapshot_command)]
