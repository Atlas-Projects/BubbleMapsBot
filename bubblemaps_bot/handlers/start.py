from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bubblemaps_bot.db.users import add_user_if_not_exists

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await add_user_if_not_exists(update.effective_user.id)
    await update.message.reply_text("👋 Welcome to Bubblemaps Bot!\nUse /help for more info.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a contract address to get its Bubblemap and insights!")

def get_handlers():
    return [CommandHandler("start", start), CommandHandler("help", help_command)]
