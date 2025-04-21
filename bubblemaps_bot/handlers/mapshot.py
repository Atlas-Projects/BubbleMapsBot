import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType
from telegram.ext import CallbackContext, CommandHandler

from bubblemaps_bot import logger
from bubblemaps_bot.utils.bubblemaps_metadata import fetch_metadata_from_all_chains
from bubblemaps_bot.utils.screenshot import (
    build_iframe_url,
    capture_bubblemap,
    check_map_availability,
)


async def mapshot_worker(
    please_wait_msg, update: Update, context: CallbackContext, chain: str, token: str
):
    """
    Worker function to generate and send a Bubblemap screenshot for a given chain and token.
    Args:
        please_wait_msg: Message indicating processing status.
        update: Telegram update object.
        context: Telegram callback context.
        chain: Blockchain network identifier (e.g., 'eth').
        token: Token address.
    """
    try:
        screenshot = await capture_bubblemap(chain, token)
        iframe_url = build_iframe_url(chain, token)

        is_group = update.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]

        if is_group:
            keyboard = [[InlineKeyboardButton("🌐 View in Browser", url=iframe_url)]]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("🌐 View in Browser", url=iframe_url),
                    InlineKeyboardButton(
                        "🫧 View in Telegram", web_app={"url": iframe_url}
                    ),
                ]
            ]

        markup = InlineKeyboardMarkup(keyboard)

        await please_wait_msg.delete()

        await update.message.reply_photo(
            photo=screenshot,
            caption=f"🗺 Bubblemap preview for <code>{token}</code> on {chain.upper()}",
            reply_markup=markup,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to generate mapshot for {chain}:{token}: {e}")
        await please_wait_msg.edit_text("❌ Failed to generate mapshot.")


async def mapshot_command(update: Update, context: CallbackContext):
    """
    Telegram command to generate a Bubblemap screenshot for a token.
    Usage: /mapshot <token_address> or /mapshot <chain> <token_address>
    Examples:
        /mapshot 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
        /mapshot eth 0x19de6b897ed14a376dda0fe53a5420d2ac828a28
    """
    if not context.args or len(context.args) > 2:
        await update.message.reply_text(
            "Usage: /mapshot <token_address> or /mapshot <chain> <token_address>"
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

    available = await check_map_availability(chain, token)
    if not available:
        await update.message.reply_text(
            f"❌ No Bubblemap available for this token on {chain.upper()}."
        )
        return

    please_wait_msg = await update.message.reply_text("⏳ Generating mapshot...")

    asyncio.create_task(mapshot_worker(please_wait_msg, update, context, chain, token))


def get_handlers():
    """
    Returns a list of command handlers for the Telegram bot.
    """
    return [CommandHandler("mapshot", mapshot_command)]