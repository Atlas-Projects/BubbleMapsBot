from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from bubblemaps_bot.utils.bubblemaps_api import (
    fetch_distribution,
    fetch_address_details,
)
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains

ITEMS_PER_PAGE = 5


async def distribution_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram command to display token distribution in decreasing order with pagination.
    Usage: /distribution <token_address> or /distribution <chain> <token_address>
    Examples:
        /distribution 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
        /distribution eth 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if len(context.args) not in [1, 2]:
        await update.message.reply_text(
            "Usage: /distribution <token_address> or /distribution <chain> <token_address>"
        )
        return

    if len(context.args) == 1:
        token = context.args[0]
        result = await fetch_metadata_from_all_chains(token)
        if not result:
            await update.message.reply_text(
                "❌ Token not found on any supported chains."
            )
            return
        chain, _ = result
    else:
        chain, token = context.args

    sorted_nodes = await fetch_distribution(token, chain)
    if not sorted_nodes:
        await update.message.reply_text(
            f"❌ No distribution data found for token {token} on chain {chain.upper()}."
        )
        return

    context.user_data["distribution"] = {
        "chain": chain,
        "token": token,
        "nodes": sorted_nodes,
        "page": 0,
        "state": "distribution",
    }

    await send_distribution_page(update.message, context)


async def send_distribution_page(
    message, context: ContextTypes.DEFAULT_TYPE, edit_message_id=None
):
    """
    Send or edit a message with a page of distribution data and pagination keyboard.
    """
    data = context.user_data.get("distribution", {})
    if not data:
        await message.reply_text("❌ No distribution data available.")
        return

    chain = data["chain"]
    token = data["token"]
    sorted_nodes = data["nodes"]
    page = data["page"]

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
        amount = node.get("amount", 0)
        text += f"{idx}. <code>{address}</code>: {percentage:.2f}% ({amount:,.2f})\n"
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔍 {address[:6]}...", callback_data=f"dist_addr_inline_{address}"
                ),
                InlineKeyboardButton(
                    f"📩 {address[-4:]}", callback_data=f"dist_addr_new_{address}"
                ),
            ]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Previous", callback_data=f"dist_prev_{page}")
        )
    if end_idx < total_items:
        nav_buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"dist_next_{page}")
        )

    keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("Close ❌", callback_data="dist_close")])

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
        context.user_data["distribution"]["message_id"] = sent_message.message_id


async def send_address_details_inline(
    query: Update, context: ContextTypes.DEFAULT_TYPE, address: str
):
    """
    Display address details in the same message with a back button.
    """
    data = context.user_data.get("distribution", {})
    if not data:
        await query.edit_message_text("❌ Session expired.")
        return

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

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="dist_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=text, reply_markup=reply_markup, parse_mode="HTML"
    )


async def send_address_details_new(
    query: Update, context: ContextTypes.DEFAULT_TYPE, address: str
):
    """
    Send address details as a new message without buttons.
    """
    data = context.user_data.get("distribution", {})
    if not data:
        await query.edit_message_text("❌ Session expired.")
        return

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

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=text,
        parse_mode="HTML",
        reply_to_message_id=query.message.message_id,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle pagination and address details button clicks.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    current_data = context.user_data.get("distribution", {})
    if not current_data:
        await query.edit_message_text(
            "❌ Distribution session expired.\n\
Please re-send the /distribution command to check the various distribution related information."
        )
        return

    if data == "dist_close":
        await query.delete_message()
        context.user_data.pop("distribution", None)
        return

    elif data.startswith("dist_prev_") or data.startswith("dist_next_"):
        page = int(data.split("_")[-1])
        current_data["page"] = page - 1 if data.startswith("dist_prev_") else page + 1
        await send_distribution_page(
            query.message, context, edit_message_id=query.message.message_id
        )
        return

    elif data.startswith("dist_addr_inline_"):
        address = data.replace("dist_addr_inline_", "")
        current_data["state"] = "address_inline"
        await send_address_details_inline(query, context, address)
        return

    elif data.startswith("dist_addr_new_"):
        address = data.replace("dist_addr_new_", "")
        await send_address_details_new(query, context, address)
        return

    elif data == "dist_back":
        current_data["state"] = "distribution"
        await send_distribution_page(
            query.message, context, edit_message_id=query.message.message_id
        )
        return


def get_handlers():
    """
    Return the handlers for the distribution command and button callbacks.
    """
    return [
        CommandHandler("distribution", distribution_command),
        CallbackQueryHandler(
            button_handler, pattern="^dist_(prev|next|close|addr_inline|addr_new|back)"
        ),
    ]
