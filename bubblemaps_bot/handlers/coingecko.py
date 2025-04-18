import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from bubblemaps_bot.utils.coingecko_api import get_market_data
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command to fetch and display market information for a token.
    Usage: /coin <token_address>
    Example: /coin 0xa0b73e1ff0b80914ab6fe0444e65848c4c34450b
    """
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /coin <token_address>")
        return

    token_address = context.args[0]

    result = await fetch_metadata_from_all_chains(token_address)
    if not result:
        await update.message.reply_text(
            "❌ No data found for this token on supported chains."
        )
        return

    chain, _ = result

    market_data = await get_market_data(chain, token_address)
    if not market_data:
        await update.message.reply_text("❌ Failed to fetch market information.")
        return

    name = market_data.get("name", "Unknown")
    symbol = market_data.get("symbol", "Unknown").upper()
    current_price = market_data.get("market_data", {}).get("current_price", {}).get("usd", "N/A")
    market_cap = market_data.get("market_data", {}).get("market_cap", {}).get("usd", "N/A")
    market_cap_rank = market_data.get("market_data", {}).get("market_cap_rank", "N/A")
    total_volume = market_data.get("market_data", {}).get("total_volume", {}).get("usd", "N/A")
    price_change_24h = market_data.get("market_data", {}).get("price_change_percentage_24h", "N/A")
    total_supply = market_data.get("market_data", {}).get("total_supply", "N/A")
    circulating_supply = market_data.get("market_data", {}).get("circulating_supply", "N/A")
    ath = market_data.get("market_data", {}).get("ath", {}).get("usd", "N/A")
    ath_date = market_data.get("market_data", {}).get("ath_date", {}).get("usd", "N/A")
    if ath_date != "N/A":
        ath_date = datetime.strptime(ath_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
    last_updated = market_data.get("last_updated", "N/A")
    if last_updated != "N/A":
        last_updated = datetime.strptime(last_updated, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")

    text = (
        f"<b>📈 Market Information</b>\n\n"
        f"🔗 <b>Chain:</b> {chain.upper()}\n"
        f"🏷️ <b>Token:</b> {token_address}\n\n"
        f"🏷️ <b>Name:</b> {name}\n"
        f"🔣 <b>Symbol:</b> {symbol}\n"
        f"💰 <b>Current Price (USD):</b> ${current_price:,.4f}\n"
        f"📊 <b>Market Cap (USD):</b> ${market_cap:,.2f}\n"
        f"🏅 <b>Market Cap Rank:</b> {market_cap_rank}\n"
        f"🔄 <b>24h Volume (USD):</b> ${total_volume:,.2f}\n"
        f"📉 <b>24h Price Change:</b> {price_change_24h:.2f}%\n"
        f"🔢 <b>Total Supply:</b> {total_supply:,.2f}\n"
        f"💸 <b>Circulating Supply:</b> {circulating_supply:,.2f}\n"
        f"🌟 <b>All-Time High (USD):</b> ${ath:,.4f}\n"
        f"📅 <b>ATH Date:</b> {ath_date}\n"
        f"🕒 <b>Last Updated:</b> {last_updated}"
    )

    await update.message.reply_text(text, parse_mode="HTML")

def get_handlers():
    """Return handlers for the coin command."""
    return [
        CommandHandler("coin", coin_command),
    ]