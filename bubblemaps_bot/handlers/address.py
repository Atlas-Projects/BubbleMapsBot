from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bubblemaps_bot.utils.bubblemaps_api import fetch_address_details
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains


async def address_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram command to fetch details of a specific address for a token.
    Usage: /address <token_address> <address> or /address <chain> <token_address> <address>
    Examples:
        /address 0x19de6b897ed14a376dda0fe53a5420d2ac828a28 0x1ae3739e17d8500f2b2d80086ed092596a116e0b
        /address eth 0x19de6b897ed14a376dda0fe53a5420d2ac828a28 0x1ae3739e17d8500f2b2d80086ed092596a116e0b
    """
    if len(context.args) not in [2, 3]:
        await update.message.reply_text(
            "Usage: /address <token_address> <address> or /address <chain> <token_address> <address>"
        )
        return

    if len(context.args) == 2:
        token, address = context.args
        result = await fetch_metadata_from_all_chains(token)
        if not result:
            await update.message.reply_text(
                "❌ Token not found on any supported chains."
            )
            return
        chain, _ = result
    else:
        chain, token, address = context.args

    data = await fetch_address_details(token, chain, address)
    if not data:
        await update.message.reply_text(
            f"❌ No details found for address {address} on chain {chain.upper()} for token {token}."
        )
        return

    name = data.get("name", "Unknown")
    amount = data.get("amount", 0)
    percentage = data.get("percentage", 0)
    is_contract = "Yes" if data.get("is_contract", False) else "No"
    transaction_count = data.get("transaction_count", 0)
    transfer_count = data.get("transfer_count", 0)

    text = (
        f"<b>📍 Address Details</b>\n\n"
        f"🔗 <b>Chain:</b> {chain.upper()}\n"
        f"🏷️ <b>Token:</b> {token}\n"
        f"📍 <b>Address:</b> {address}\n\n"
        f"🏷️ <b>Name:</b> {name}\n"
        f"💰 <b>Amount:</b> {amount:,.2f}\n"
        f"📊 <b>Percentage:</b> {percentage:.4f}%\n"
        f"📜 <b>Is Contract:</b> {is_contract}\n"
        f"🔄 <b>Transaction Count:</b> {transaction_count}\n"
        f"📤 <b>Transfer Count:</b> {transfer_count}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


def get_handlers():
    return [CommandHandler("address", address_command)]
