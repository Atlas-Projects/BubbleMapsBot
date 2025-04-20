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
Example: <code>/check 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>

<code>/mapshot address</code> or <code>/mapshot chain address</code> - Get an interactive Bubblemap
Examples:
<code>/mapshot 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>
<code>/mapshot eth 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>

<code>/meta token_address</code> or <code>/meta chain token_address</code> - Get metadata about a specific token
Examples: 
<code>/meta 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>
<code>/meta eth 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>

<code>/distribution token_address</code> or <code>/distribution chain token_address</code> - Get distribution information about a token
Examples:
<code>/distribution 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>
<code>/distribution eth 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>

<code>/coin address</code> - Price and market data from CoinGecko
Example: <code>/coin 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b</code>

<code>/address token_address address</code> or <code>/address chain token_address address</code> - Fetch details of a specific address for a token
Examples:
<code>/address 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b 0xa023f08c70a23abc7edfc5b6b5e171d78dfc947e</code>
<code>/address eth 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b 0xa023f08c70a23abc7edfc5b6b5e171d78dfc947e</code>

<code>/clear</code> - Clear the Valkey cache

Please follow the format to use any desired command."""

    await update.message.reply_text(
        text=DETAILED_HELP_TEXT,
        parse_mode=ParseMode.HTML,
    )


def get_handlers():
    return [CommandHandler("start", start), CommandHandler("help", help_command)]