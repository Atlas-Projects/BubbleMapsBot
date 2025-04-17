import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
)
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bubblemaps_bot.utils.bubblemaps_api import (
    fetch_address_details,
    fetch_distribution,
)
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains
from bubblemaps_bot.utils.screenshot import build_iframe_url, capture_bubblemap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 5


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main command to check token across all chains and provide comprehensive analysis.
    Usage: /check <token_address>
    Example: /check 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /check <token_address>")
        return

    token = context.args[0]

    # Check metadata across all chains
    result = await fetch_metadata_from_all_chains(token)
    if not result:
        await update.message.reply_text(
            "❌ No data found for this token on supported chains."
        )
        return

    chain, metadata = result

    # Store data in user context
    context.user_data["check"] = {
        "token": token,
        "chain": chain,
        "metadata": metadata,
        "state": "main_menu",
    }

    await send_main_menu(update.message, context)


async def send_main_menu(
    message: Message, context: ContextTypes.DEFAULT_TYPE, edit_message_id=None
):
    """Send or edit the main menu with metadata and options."""
    data = context.user_data.get("check", {})
    if not data:
        await message.reply_text("❌ Session expired.")
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
        [InlineKeyboardButton("❌ Close", callback_data="check_close")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit_message_id:
        __chat_id = message.chat.id
        __message_id = message.reply_to_message.id
        await message.delete()
        __sent_message = await context.bot.send_message(
            chat_id=__chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            reply_to_message_id=__message_id,
        )
        context.user_data["check"]["message_id"] = __sent_message.message_id
    else:
        sent_message = await message.reply_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
        context.user_data["check"]["message_id"] = sent_message.message_id


async def send_mapshot(message: Message, context: ContextTypes.DEFAULT_TYPE):
    """Generate and send bubblemap screenshot."""
    data = context.user_data.get("check", {})
    chain = data["chain"]
    token = data["token"]

    await message.edit_text("⏳ Please wait while a bubblemap is generated...")

    try:
        screenshot = await capture_bubblemap(chain, token)
        iframe_url = build_iframe_url(chain, token)
        keyboard = [
            [
                InlineKeyboardButton("🌐 View Bubblemap", url=iframe_url),
                InlineKeyboardButton("❌ Close", callback_data="check_close"),
            ],
            [InlineKeyboardButton("⬅️ Go Back", callback_data="check_back")],
        ]
        markup = InlineKeyboardMarkup(keyboard)

        __chat_id = message.chat.id
        __message_id = message.reply_to_message.id
        await message.delete()
        __sent_message = await context.bot.send_photo(
            chat_id=__chat_id,
            photo=screenshot,
            caption=f"🗺 Bubblemap for <code>{token}</code> on {chain.upper()}",
            parse_mode="HTML",
            reply_markup=markup,
            reply_to_message_id=__message_id,
        )
        context.user_data["check"]["message_id"] = __sent_message.message_id
    except Exception as e:
        await message.edit_text(f"❌ Mapshot failed: {e}")


async def send_distribution_page(
    message, context: ContextTypes.DEFAULT_TYPE, edit_message_id=None
):
    """Send or edit distribution page with address selection options."""
    data = context.user_data.get("check", {})
    if not data.get("distribution"):
        sorted_nodes = await fetch_distribution(data["token"], data["chain"])
        if not sorted_nodes:
            await message.reply_text("❌ No distribution data found.")
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
    for node in current_nodes:
        address = node["address"]
        percentage = node.get("percentage", 0)
        amount = node.get("amount", 0)
        text += f"<code>{address}</code>: {percentage:.2f}% ({amount:,.2f})\n"
        # Two buttons per address
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
    nav_buttons.append(InlineKeyboardButton("🔙 Back", callback_data="check_back"))
    keyboard.append(nav_buttons)

    reply_markup = InlineKeyboardMarkup(keyboard)

    if edit_message_id:
        await context.bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=edit_message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        sent_message = await message.reply_text(
            text, reply_markup=reply_markup, parse_mode="HTML"
        )
        data["distribution"]["message_id"] = sent_message.message_id


async def send_address_details_inline(
    message, context: ContextTypes.DEFAULT_TYPE, address: str, edit_message_id=None
):
    """Display address details in the same message with a back button."""
    data = context.user_data.get("check", {})
    chain = data["chain"]
    token = data["token"]

    addr_data = await fetch_address_details(token, chain, address)
    if not addr_data:
        await message.reply_text(f"❌ No details found for address {address}.")
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

    if edit_message_id:
        await context.bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=edit_message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    else:
        await message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")


async def send_address_details_new(
    message, context: ContextTypes.DEFAULT_TYPE, address: str
):
    """Send address details as a new message without buttons."""
    data = context.user_data.get("check", {})
    chain = data["chain"]
    token = data["token"]

    addr_data = await fetch_address_details(token, chain, address)
    if not addr_data:
        await message.reply_text(f"❌ No details found for address {address}.")
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

    await message.reply_text(text, parse_mode="HTML")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    check_data = context.user_data.get("check", {})
    if not check_data:
        await query.edit_message_text("❌ Session expired.")
        return

    message = query.message

    if data == "check_close":
        await query.delete_message()
        # context.user_data.pop("check", None)
        if check_data.get(
            "message_id"
        ) is None or query.message.message_id == check_data.get("message_id"):
            context.user_data.pop("check", None)
        return

    elif data == "check_mapshot":
        await send_mapshot(message, context)
        return

    elif data == "check_distribution":
        check_data["state"] = "distribution"
        await send_distribution_page(
            message, context, edit_message_id=check_data["message_id"]
        )
        return

    elif data.startswith("check_dist_prev_") or data.startswith("check_dist_next_"):
        page = int(data.split("_")[-1])
        check_data["distribution"]["page"] = (
            page - 1 if data.startswith("check_dist_prev_") else page + 1
        )
        await send_distribution_page(
            message, context, edit_message_id=check_data["message_id"]
        )
        return

    elif data.startswith("check_addr_inline_"):
        address = data.replace("check_addr_inline_", "")
        check_data["state"] = "address_inline"
        await send_address_details_inline(
            message, context, address, edit_message_id=check_data["message_id"]
        )
        return

    elif data.startswith("check_addr_new_"):
        address = data.replace("check_addr_new_", "")
        await send_address_details_new(message, context, address)
        return

    elif data in ["check_back", "check_dist_back"]:
        if check_data["state"] == "address_inline":
            check_data["state"] = "distribution"
            await send_distribution_page(
                message, context, edit_message_id=check_data["message_id"]
            )
        else:
            check_data["state"] = "main_menu"
            if "distribution" in check_data:
                check_data.pop("distribution")
            await send_main_menu(
                message, context, edit_message_id=check_data["message_id"]
            )
        return


def get_handlers():
    """Return handlers for the check command and its callbacks."""
    return [
        CommandHandler("check", check_command),
        CallbackQueryHandler(button_handler, pattern="^check_"),
    ]
