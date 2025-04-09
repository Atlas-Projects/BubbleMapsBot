from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata

async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /meta <chain> <token_address>")
        return

    chain, token = context.args
    data = await fetch_metadata(token, chain)

    if not data:
        await update.message.reply_text("❌ Error contacting Bubblemaps API.")
        return

    if data.get("status") != "OK":
        await update.message.reply_text(f"❌ Bubblemaps error: {data.get('message', 'Unknown error')}")
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
    return [CommandHandler("meta", meta_command)]
