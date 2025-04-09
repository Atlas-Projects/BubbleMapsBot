from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from bubblemaps_bot.utils.screenshot import capture_bubblemap
from bubblemaps_bot.utils.bubblemaps_map import build_iframe_url

async def mapshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /mapshot <chain> <token_address>")
        return

    chain, token = context.args

    try:
        screenshot = await capture_bubblemap(chain, token)
    except Exception as e:
        await update.message.reply_text(f"❌ Screenshot failed: {e}")
        return

    iframe_url = build_iframe_url(chain, token)
    keyboard = [[InlineKeyboardButton("🌐 View Bubblemap", url=iframe_url)]]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_photo(
        photo=screenshot,
        caption=f"🗺 Bubblemap preview for <code>{token}</code> on {chain.upper()}",
        reply_markup=markup,
        parse_mode="HTML"
    )

def get_handlers():
    return [CommandHandler("mapshot", mapshot_command)]
