
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext
from bubblemaps_bot.utils.screenshot import capture_bubblemap, build_iframe_url, check_map_availability
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains
import asyncio

async def mapshot_worker(please_wait_msg, update: Update, context: CallbackContext, chain: str, token: str):
    try:
        screenshot = await capture_bubblemap(chain, token)
        iframe_url = build_iframe_url(chain, token)

        is_group = update.message.chat.type in ["group", "supergroup"]
        
        if is_group:
            keyboard = [
                [InlineKeyboardButton("🌐 View in Browser", url=iframe_url)]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🌐 View in Browser", url=iframe_url),
                    InlineKeyboardButton("🫧 View in Telegram", web_app={"url": iframe_url}),
                ]
            ]
        
        markup = InlineKeyboardMarkup(keyboard)

        await please_wait_msg.delete()

        await update.message.reply_photo(
            photo=screenshot,
            caption=f"🗺 Bubblemap preview for <code>{token}</code> on {chain.upper()}",
            reply_markup=markup,
            parse_mode="HTML"
        )
    except Exception as e:
        await please_wait_msg.edit_text(f"❌ Failed to generate mapshot: {e}")

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

    please_wait_msg = await update.message.reply_text("⏳ Generating mapshot...")

    asyncio.create_task(mapshot_worker(please_wait_msg, update, context, chain, token))

def get_handlers():
    return [CommandHandler("mapshot", mapshot_command)]