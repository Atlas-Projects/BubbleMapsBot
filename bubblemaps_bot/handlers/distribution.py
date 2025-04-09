from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler
from bubblemaps_bot.utils.bubblemaps_api import fetch_distribution

ITEMS_PER_PAGE = 5  
async def distribution_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Telegram command to display token distribution in decreasing order with pagination.
    Usage: /distribution <chain> <token>
    Example: /distribution eth 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /distribution <chain> <token_address>")
        return

    chain, token = context.args
    sorted_nodes = await fetch_distribution(token, chain)
    if not sorted_nodes:
        await update.message.reply_text(f"❌ No distribution data found for token {token} on chain {chain}.")
        return

    context.user_data["distribution"] = {
        "chain": chain,
        "token": token,
        "nodes": sorted_nodes,
        "page": 0
    }

    await send_distribution_page(update.message, context)

async def send_distribution_page(message, context: ContextTypes.DEFAULT_TYPE, edit_message_id=None):
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

    text = f"<b>📊 Token Distribution</b>\n\n" \
           f"🔗 <b>Chain:</b> {chain.upper()}\n" \
           f"🏷️ <b>Token:</b> {token}\n" \
           f"📋 <b>Page:</b> {page + 1}/{((total_items - 1) // ITEMS_PER_PAGE) + 1}\n\n"

    for node in current_nodes:
        address = node["address"]
        amount = node.get("amount", 0)
        percentage = node.get("percentage", 0)
        text += f"<code>{address}</code>: {percentage:.2f}% ({amount:,.2f})\n"

    keyboard = []
    if page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"dist_prev_{page}"))
    if end_idx < total_items:
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"dist_next_{page}"))
    keyboard.append(InlineKeyboardButton("Close ❌", callback_data="dist_close"))

    reply_markup = InlineKeyboardMarkup([keyboard] if len(keyboard) > 1 else [keyboard])

    if edit_message_id:
        await context.bot.edit_message_text(
            chat_id=message.chat_id,
            message_id=edit_message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        sent_message = await message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
        context.user_data["distribution"]["message_id"] = sent_message.message_id

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle pagination button clicks.
    """
    query = update.callback_query
    await query.answer()

    data = query.data
    current_data = context.user_data.get("distribution", {})

    if not current_data:
        await query.edit_message_text("❌ Distribution session expired.")
        return

    if data == "dist_close":
        await query.delete_message()
        context.user_data.pop("distribution", None)
        return

    if data.startswith("dist_prev_") or data.startswith("dist_next_"):
        page = int(data.split("_")[-1])
        if data.startswith("dist_prev_"):
            current_data["page"] = page - 1
        else:
            current_data["page"] = page + 1

        await send_distribution_page(
            query.message,
            context,
            edit_message_id=query.message.message_id
        )

def get_handlers():
    """
    Return the handlers for the distribution command and button callbacks.
    """
    return [
        CommandHandler("distribution", distribution_command),
        CallbackQueryHandler(button_handler, pattern="^dist_(prev|next|close)")
    ]