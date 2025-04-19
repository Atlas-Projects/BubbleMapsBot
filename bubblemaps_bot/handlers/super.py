import asyncio
import logging
from datetime import datetime

from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bubblemaps_bot.utils.bubblemaps_api import (
    fetch_address_details,
    fetch_distribution,
)
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains
from bubblemaps_bot.utils.coingecko_api import get_market_data
from bubblemaps_bot.utils.screenshot import build_iframe_url, capture_bubblemap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 5


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main command to check token across all chains and provide comprehensive analysis.
    Usage: /check <token_address>
    Example: /check 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /check <token_address>")
        return

    token = context.args[0]

    result = await fetch_metadata_from_all_chains(token)
    if not result:
        await update.message.reply_text(
            "❌ No data found for this token on supported chains."
        )
        return

    chain, metadata = result

    context.user_data[update.effective_chat.id] = {}
    context.user_data[update.effective_chat.id]["check"] = {
        "token": token,
        "chain": chain,
        "metadata": metadata,
        "state": "main_menu",
    }

    await send_main_menu(update.message, context)


async def send_main_menu(
    message_query: Message | CallbackQuery | None,
    context: ContextTypes.DEFAULT_TYPE,
    bmap_back: bool = False,
):
    """Send or edit the main menu with metadata and options."""
    if isinstance(message_query, CallbackQuery):
        data = context.user_data[message_query.message.chat.id].get("check", {})
    elif isinstance(message_query, Message):
        data = context.user_data[message_query.chat.id].get("check", {})

    if not data:
        await message_query.reply_text("❌ Session expired.")
        return

    chain = data["chain"]
    token = data["token"]
    meta = data["metadata"]

    score = meta["decentralisation_score"]
    cex = meta["identified_supply"]["percent_in_cexs"]
    contracts = meta["identified_supply"]["percent_in_contracts"]
    dt_update = meta["dt_update"]

    text = (
        f"<b>🧠 Token Analysis</b>\n\n"
        f"🔗 <b>Chain:</b> {chain.upper()}\n"
        f"🏷️ <b>Token:</b> {token}\n\n"
        f"📊 <b>Decentralisation Score:</b> {score:.2f}\n"
        f"🏦 <b>In CEXs:</b> {cex:.2f}%\n"
        f"💼 <b>In Contracts:</b> {contracts:.2f}%\n"
        f"🕒 <b>Last Updated:</b> {dt_update}"
    )

    keyboard = [
        [InlineKeyboardButton("🗺 Generate Mapshot", callback_data="check_mapshot")],
        [InlineKeyboardButton("📊 Distribution", callback_data="check_distribution")],
        [InlineKeyboardButton("ℹ️ More Info", callback_data="check_more_info")],
        [InlineKeyboardButton("❌ Close", callback_data="check_close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(message_query, Message):
        await message_query.reply_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    elif isinstance(message_query, CallbackQuery):
        if not bmap_back:
            await message_query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
        else:
            if isinstance(message_query.message, Message):
                await message_query.delete_message()
                message = message_query.message
                __chat_id = message.chat.id
                __message_id = message.reply_to_message.id
                await context.bot.send_message(
                    chat_id=__chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=__message_id,
                )


async def generate_bubblemap_send(chain: str, token: str, query: CallbackQuery) -> None:
    try:
        screenshot = await capture_bubblemap(chain, token)
        iframe_url = build_iframe_url(chain, token)
        keyboard = [
            [
                InlineKeyboardButton("🌐 View Bubblemap", url=iframe_url),
                InlineKeyboardButton("❌ Close", callback_data="check_close"),
            ],
            [InlineKeyboardButton("⬅️ Go Back", callback_data="check_back_bmap")],
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_media(
            media=InputMediaPhoto(
                media=screenshot,
                caption=f"🗺 Bubblemap for <code>{token}</code> on {chain.upper()}",
                parse_mode=ParseMode.HTML,
                filename=f"output_bmap_{chain}_{token}.png",
            ),
            reply_markup=markup,
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Mapshot failed: {e}")


async def send_mapshot(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send bubblemap screenshot."""
    data = context.user_data[query.message.chat.id].get("check", {})
    chain = data["chain"]
    token = data["token"]

    await query.edit_message_text("⏳ Please wait while a bubblemap is generated...")
    asyncio.create_task(generate_bubblemap_send(chain=chain, token=token, query=query))


async def send_distribution_page(
    message_query: Message | CallbackQuery | None,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send or edit distribution page with address selection options."""
    if isinstance(message_query, Message):
        data = context.user_data[message_query.chat.id].get("check", {})
    elif isinstance(message_query, CallbackQuery):
        data = context.user_data[message_query.message.chat.id].get("check", {})

    if not data.get("distribution"):
        sorted_nodes = await fetch_distribution(data["token"], data["chain"])
        if not sorted_nodes:
            if isinstance(message_query, Message):
                await message_query.edit_text("❌ No distribution data found.")
            elif isinstance(message_query, CallbackQuery):
                await message_query.edit_message_text("❌ No distribution data found.")
            return
        data["distribution"] = {"nodes": sorted_nodes, "page": 0}

    chain = data["chain"]
    token = data["token"]
    sorted_nodes = data["distribution"]["nodes"]
    page = data["distribution"]["page"]

    total_items = len(sorted_nodes)
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
    current_nodes = sorted_nodes[start_idx:end_idx]

    text = (
        f"<b>📊 Token Distribution</b>\n"
        f"🔗 <b>Chain:</b> {chain.upper()}\n"
        f"🏷️ <b>Token:</b> {token}\n"
        f"📋 <b>Page:</b> {page + 1}/{((total_items - 1) // ITEMS_PER_PAGE) + 1}\n\n"
    )

    keyboard = []
    for idx, node in enumerate(current_nodes, start=1):
        address = node["address"]
        percentage = node.get("percentage", 0)
        text += f"{idx}. <code>{address}</code>: {percentage:.2f}%\n"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔍 {address[:6]}...", callback_data=f"check_addr_inline_{address}"
                ),
                InlineKeyboardButton(
                    f"📩 {address[-4:]}", callback_data=f"check_addr_new_{address}"
                ),
            ]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Prev", callback_data=f"check_dist_prev_{page}")
        )
    if end_idx < total_items:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"check_dist_next_{page}")
        )

    keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="check_back")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if isinstance(message_query, CallbackQuery):
        await message_query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
    elif isinstance(message_query, Message):
        await message_query.edit_text(
            text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )


async def send_address_details_inline(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, address: str
) -> None:
    """Display address details in the same message with a back button."""
    data = context.user_data[query.message.chat.id].get("check", {})
    chain = data["chain"]
    token = data["token"]

    addr_data = await fetch_address_details(token, chain, address)
    if not addr_data:
        await query.edit_message_text(f"❌ No details found for address {address}.")
        return

    name = addr_data.get("name", "Unknown")
    amount = addr_data.get("amount", 0)
    percentage = addr_data.get("percentage", 0)
    is_contract = "Yes" if addr_data.get("is_contract", False) else "No"
    transaction_count = addr_data.get("transaction_count", 0)
    transfer_count = addr_data.get("transfer_count", 0)

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

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="check_dist_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
    )


async def send_address_details_new(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, address: str
) -> None:
    """Send address details as a new message without buttons."""
    data = context.user_data[query.message.chat.id].get("check", {})
    chain = data["chain"]
    token = data["token"]

    addr_data = await fetch_address_details(token, chain, address)
    if not addr_data:
        await query.edit_message_text(f"❌ No details found for address {address}.")
        return

    name = addr_data.get("name", "Unknown")
    amount = addr_data.get("amount", 0)
    percentage = addr_data.get("percentage", 0)
    is_contract = "Yes" if addr_data.get("is_contract", False) else "No"
    transaction_count = addr_data.get("transaction_count", 0)
    transfer_count = addr_data.get("transfer_count", 0)

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

    if isinstance(query.message, Message):
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text=text,
            parse_mode=ParseMode.HTML,
            reply_to_message_id=query.message.reply_to_message.id,
        )


async def send_market_info(
    query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Fetch and display additional market information from CoinGecko."""
    data = context.user_data[query.message.chat.id].get("check", {})
    if not data:
        await query.edit_message_text("❌ Session expired.")
        return

    chain = data["chain"]
    token = data["token"]

    try:
        await query.edit_message_text("⏳ Fetching market information...")
    except Exception as e:
        logger.error(f"Failed to edit message to show loading: {e}")
        text = f"❌ Error initiating market information fetch for token {token} on {chain.upper()}."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="check_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )
        return

    try:
        market_data = await get_market_data(chain, token)
        if not market_data:
            logger.warning(f"No market data found for {chain}/{token}")
            text = f"❌ No information found on CoinGecko for token {token} on {chain.upper()}."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="check_back")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
            )
            return

        name = market_data.get("name", "Unknown")
        symbol = market_data.get("symbol", "Unknown").upper()
        current_price = (
            market_data.get("market_data", {})
            .get("current_price", {})
            .get("usd", "N/A")
        )
        market_cap = (
            market_data.get("market_data", {}).get("market_cap", {}).get("usd", "N/A")
        )
        market_cap_rank = market_data.get("market_data", {}).get(
            "market_cap_rank", "N/A"
        )
        total_volume = (
            market_data.get("market_data", {}).get("total_volume", {}).get("usd", "N/A")
        )
        price_change_24h = market_data.get("market_data", {}).get(
            "price_change_percentage_24h", "N/A"
        )
        total_supply = market_data.get("market_data", {}).get("total_supply", "N/A")
        circulating_supply = market_data.get("market_data", {}).get(
            "circulating_supply", "N/A"
        )
        ath = market_data.get("market_data", {}).get("ath", {}).get("usd", "N/A")
        ath_date = (
            market_data.get("market_data", {}).get("ath_date", {}).get("usd", "N/A")
        )
        if ath_date != "N/A":
            ath_date = datetime.strptime(ath_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime(
                "%Y-%m-%d"
            )
        last_updated = market_data.get("last_updated", "N/A")
        if last_updated != "N/A":
            last_updated = datetime.strptime(
                last_updated, "%Y-%m-%dT%H:%M:%S.%fZ"
            ).strftime("%Y-%m-%d %H:%M:%S")

        text = (
            f"<b>📈 Market Information</b>\n\n"
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

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="check_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )

    except Exception as e:
        logger.error(f"Error in send_market_info for {chain}/{token}: {e}")
        text = f"❌ Error fetching market information for token {token} on {chain.upper()}."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="check_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    check_data = context.user_data[update.effective_chat.id].get("check", {})
    if not check_data:
        await query.edit_message_text("❌ Session expired.")
        return

    if data == "check_close":
        await query.delete_message()
        if check_data.get(
            "message_id"
        ) is None or query.message.message_id == check_data.get("message_id"):
            context.user_data[update.effective_chat.id].pop("check", None)
        return

    elif data == "check_mapshot":
        await send_mapshot(query, context)
        return

    elif data == "check_distribution":
        check_data["state"] = "distribution"
        await send_distribution_page(query, context)
        return

    elif data == "check_more_info":
        check_data["state"] = "market_info"
        await send_market_info(query, context)
        return

    elif data.startswith("check_dist_prev_") or data.startswith("check_dist_next_"):
        page = int(data.split("_")[-1])
        check_data["distribution"]["page"] = (
            page - 1 if data.startswith("check_dist_prev_") else page + 1
        )
        await send_distribution_page(query, context)
        return

    elif data.startswith("check_addr_inline_"):
        address = data.replace("check_addr_inline_", "")
        check_data["state"] = "address_inline"
        await send_address_details_inline(query, context, address)
        return

    elif data.startswith("check_addr_new_"):
        address = data.replace("check_addr_new_", "")
        await send_address_details_new(query, context, address)
        return

    elif data in ["check_back", "check_dist_back", "check_back_bmap"]:
        if check_data["state"] == "address_inline":
            check_data["state"] = "distribution"
            await send_distribution_page(query, context)
        elif check_data["state"] == "market_info":
            check_data["state"] = "main_menu"
            await send_main_menu(query, context)
        else:
            check_data["state"] = "main_menu"
            if "distribution" in check_data:
                check_data.pop("distribution")
            if data == "check_back_bmap":
                await send_main_menu(query, context, bmap_back=True)
            else:
                await send_main_menu(query, context)
        return


def get_handlers():
    """Return handlers for the check command and its callbacks."""
    return [
        CommandHandler("check", check_command),
        CallbackQueryHandler(button_handler, pattern="^check_"),
    ]
