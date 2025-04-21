from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bubblemaps_bot import logger
from bubblemaps_bot.utils.bubblemaps_metadata import (
    fetch_metadata,
    fetch_metadata_from_all_chains,
)


async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram command to fetch metadata for a token.
    Usage: /meta <token_address> or /meta <chain> <token_address>
    Examples:
        /meta 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
        /meta eth 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if not context.args:
        await update.message.reply_text(
            "Usage: /meta <token_address> or /meta <chain> <token_address>"
        )
        return

    if len(context.args) == 1:
        token = context.args[0]
        result = await fetch_metadata_from_all_chains(token)
        if not result:
            await update.message.reply_text(
                "❌ No metadata found for this token on supported chains."
            )
            return
        chain, data = result
    else:
        chain, token = context.args
        data = await fetch_metadata(token, chain)
        if not data:
            await update.message.reply_text("❌ Error contacting Bubblemaps API.")
            return
        if data.get("status") != "OK":
            await update.message.reply_text(
                f"Some error occurred trying to fetch details about {' '.join(context.args)} from Bubblemaps.\n\
Please retry later."
            )
            logger.error(
                f"❌ Bubblemaps error while trying to fetch details about: {' '.join(context.args)}\n\
Actual error: {data.get('message', 'Unknown error')}"
            )
            return

    score = data["decentralisation_score"]
    cex = data["identified_supply"]["percent_in_cexs"]
    contracts = data["identified_supply"]["percent_in_contracts"]
    dt_update = data["dt_update"]

    text = (
        f"<b>🧠 Bubblemaps Metadata</b>\n\n"
        f"🔗 <b>Chain:</b> {chain.upper()}\n"
        f"🏷️ <b>Token:</b> {token}\n\n"
        f"📊 <b>Decentralisation Score:</b> {score:.2f}\n"
        f"🏦 <b>In CEXs:</b> {cex:.2f}%\n"
        f"💼 <b>In Contracts:</b> {contracts:.2f}%\n"
        f"🕒 <b>Last Updated:</b> {dt_update}"
    )
    await update.message.reply_text(text)


def get_handlers():
    """
    Returns a list of command handlers for the Telegram bot.
    """
    return [CommandHandler("meta", meta_command)]