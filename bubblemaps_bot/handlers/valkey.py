from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from bubblemaps_bot import SUDO_USERS
from bubblemaps_bot.utils.valkey import valkey


async def clear_cache_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in SUDO_USERS:
        return

    if not valkey:
        await update.message.reply_text("⚠️ Valkey is not enabled or not connected.")
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Yes", callback_data="confirm_clear_cache"),
                InlineKeyboardButton("❌ No", callback_data="cancel_clear_cache"),
            ]
        ]
    )
    await update.message.reply_text(
        "Are you sure you want to clear the Valkey cache?", reply_markup=keyboard
    )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "confirm_clear_cache":
        if user_id in SUDO_USERS:
            if valkey:
                try:
                    await valkey.flushdb()
                    await query.edit_message_text("✅ Valkey cache has been cleared.")
                except Exception as e:
                    await query.edit_message_text(f"❌ Failed to clear cache: {e}")
            else:
                await query.edit_message_text("⚠️ Valkey is not enabled.")
        else:
            await query.edit_message_text(
                "🚫 You are not authorized to perform this action."
            )

    elif query.data == "cancel_clear_cache":
        await query.edit_message_text("❎ Cancelled cache clear.")

    elif query.data == "noop":
        pass


def get_handlers():
    return [
        CommandHandler("clear", clear_cache_command),
        CallbackQueryHandler(handle_callback_query),
    ]
