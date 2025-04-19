from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from bubblemaps_bot.db.users import add_user_if_not_exists


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user_if_not_exists(update.effective_user.id)
    await update.message.reply_text(
        "👋 Welcome to Bubblemaps Bot!\nUse /help for more info."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    DETAILED_HELP_TEXT = """The following commands are available to be used:
<code>/check address</code> - View details about a token
<code>/mapshot address</code> - Get an interactive Bubblemap
<code>/meta token_address</code> or <code>/meta chain token_address</code> - Get metadata about a specific token
<code>/distribution token</code> - Get distribution information about a token
<code>/coin address</code> - Price and market data from CoinGecko
<code>/address chain token_address address</code> - Fetch details of a specific address for a token
<code>/clear</code> - Clear the Valkey cache

Please follow the format to use any desired command."""

    await update.message.reply_text(
        text=DETAILED_HELP_TEXT,
        parse_mode=ParseMode.HTML,
    )


def get_handlers():
    return [CommandHandler("start", start), CommandHandler("help", help_command)]
