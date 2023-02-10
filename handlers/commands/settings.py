import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler, 
    Filters,
    MessageHandler
)

from utils.db.connection import db
from utils.translations import translate as _
from handlers.wrappers import ignore_old_messages, valid_user

logger = logging.getLogger(__name__)


@ignore_old_messages
def settings(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Language", callback_data="edit_language")]
    ]

    context.bot.send_message(
        update.effective_chat.id,
        text="Settings: ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "SELECTED"

def edit_language(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧", callback_data="new-en"),
            InlineKeyboardButton("🇱🇻", callback_data="new-lv"),
            InlineKeyboardButton("🇷🇺", callback_data="new-ru"),
        ]
    ]

    context.bot.send_message(
        update.effective_chat.id,
        text="Please select your preferred language",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return "SELECTED"

def save_language(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    lang = message.data.split("-")[1]
    if db.get_account(update.effective_user.id):
        db.update_selected_lang(update.effective_user.id, lang)

    else:
        db.create_account(update.effective_user)
        db.update_selected_lang(update.effective_user.id, lang)

    lang_mapping = {
        "en": "🇬🇧",
        "lv": "🇱🇻",
        "ru": "🇷🇺"
    }

    context.chat_data["lang"] = lang

    context.bot.send_message(
        update.effective_user.id,
        text=f"You have selected {lang_mapping.get(lang)} as your preferred language, you can always change it using /settings command.",
    )

    return ConversationHandler.END

settings_handler = ConversationHandler(
    entry_points=[CommandHandler("settings", settings)],
    states={
        "SETTINGS": [CallbackQueryHandler(settings, pattern="^settings$"),],
        "SELECTED": [
            CallbackQueryHandler(edit_language, pattern="^edit_language$"),
            CallbackQueryHandler(save_language, pattern="^new-(lv$|en$|ru$)"),
        ]
    },
    fallbacks=[MessageHandler(Filters.regex("^Done$"),settings)],
    name="settings",
    allow_reentry=True
)