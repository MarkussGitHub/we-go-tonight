import logging

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update
)
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler,
)

from utils.db.connection import db
from utils.translations import translate as _
from handlers.wrappers import ignore_old_messages, valid_user
from handlers.commands.event_menu import event_categories, event_selection, event_details
from handlers.commands.place_menu import place_categories, place_sub_categories, place_selection, place_details, view_photos, view_menu, view_drink_menu, contacts, event_button, place_event_details

logger = logging.getLogger(__name__)

@ignore_old_messages
@valid_user
def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    user = update.effective_user

    # If started using /start
    if update.message:
        logger.info(f"{user.first_name}, started the conversation. User ID: {user.id}")

        if db.get_account(user.id)["lang"] is None:
            return edit_language(update, context)

    # If started over
    elif context.chat_data.get("message"):
        update.message = context.chat_data["message"]

    # If user has no language selected
    if not context.chat_data.get("lang"):
        context.chat_data["lang"] = db.get_account(user["id"])["lang"]
    lang = context.chat_data["lang"]

    keyboard = [
        [InlineKeyboardButton(_("Events", lang), callback_data="events")],
        [InlineKeyboardButton(_("Places", lang), callback_data="places")],
    ]


    if update.callback_query and update.callback_query.data == "start":
        message = update.callback_query
        message.answer()
        message.edit_message_text(
            text=_("View places or events", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        context.bot.send_message(
            chat_id=user.id,
            text=_("View places or events", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return "START"


def select_date(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    lang = context.chat_data["lang"]

    keyboard = [
        [InlineKeyboardButton(_("Today", lang), callback_data="today")],
        [InlineKeyboardButton(_("This week", lang), callback_data="week")],
        [InlineKeyboardButton(_("This month", lang), callback_data="month")],
        [InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"start")],
    ]

    # If started over
    if update.callback_query:
        message = update.callback_query
        message.answer()
        message.edit_message_text(
            text=_("When would you like to go?", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    # If started using /start
    else:
        context.bot.send_message(
            chat_id=user.id,
            text=_("When would you like to go?", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return "EVENTS"


def edit_language(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧", callback_data="en"),
            InlineKeyboardButton("🇱🇻", callback_data="lv"),
            InlineKeyboardButton("🇷🇺", callback_data="ru"),
        ]
    ]
    update.message.reply_text(
        text="Please select your preferred language",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return "LANGUAGE"


def language_selected(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    lang = update.callback_query.data
    update.callback_query.answer()
    db.update_selected_lang(user.id, lang)
    context.chat_data["lang"] = lang

    lang_mapping = {
        "en": "🇬🇧",
        "lv": "🇱🇻",
        "ru": "🇷🇺"
    }

    context.bot.send_message(
        chat_id=user.id,
        text=f"You have selected {lang_mapping.get(lang)} as your preferred language, you can always change it using /settings command.",
    )

    return start(update, context)

def end(update: Update, context: CallbackContext) -> int:
    """
    Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    Made for the second optiion of completely setting off the bot by pressing cancel
    called at the end of every type of event
    """
    message = update.callback_query
    lang = context.chat_data["lang"]
    message.answer()
    message.edit_message_text(
        text=_("I hope you will use our services again", lang))
    return ConversationHandler.END

event_types = "(Concerts/Parties|Culture|Workshop|Food/Drinks|Art/Literature|Theatre/Stand up|"")(-[0-9]+)?$"
event_type_pattern = "event_type|today|week|month"

place_types = "((Food & Drinks)|(Culture Spaces)|Entertainment|(Cinema & Theater))"
place_sub_type_pattern = "((Food & Drinks)|(Culture Spaces)|Entertainment|(Cinema & Theater))-"

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        "START": [
            CallbackQueryHandler(start, pattern="^start$"),
            CallbackQueryHandler(select_date, pattern="^events$"),
            CallbackQueryHandler(place_categories, pattern="^places$"),
        ],
        "EVENTS": [
            CallbackQueryHandler(start, pattern="^start$"),
            CallbackQueryHandler(select_date, pattern="^events$"),
            CallbackQueryHandler(event_categories, pattern="^" + event_type_pattern + "$"),
            CallbackQueryHandler(event_selection, pattern="^" + event_types + "$"),
            CallbackQueryHandler(event_details, pattern="^details"),
            CallbackQueryHandler(end, pattern="^end$"),
        ],
        "PLACES": [
            CallbackQueryHandler(start, pattern="^start$"),
            CallbackQueryHandler(place_categories, pattern="^places$"),
            CallbackQueryHandler(place_sub_categories, pattern="^" + place_types + "$"),
            CallbackQueryHandler(place_selection, pattern="^" + place_sub_type_pattern),
            CallbackQueryHandler(place_details, pattern="^place_details"),
            CallbackQueryHandler(view_photos, pattern="^photos"),
            CallbackQueryHandler(place_event_details, pattern="^p_details"),
            CallbackQueryHandler(view_menu, pattern="^menu"),       
            CallbackQueryHandler(view_drink_menu, pattern="^drinks"),   
            CallbackQueryHandler(contacts, pattern="^contacts"),   
            CallbackQueryHandler(event_button, pattern="^event_button"),   
            CallbackQueryHandler(end, pattern="^end$"),
        ],
        "LANGUAGE": [
            CallbackQueryHandler(language_selected, pattern="^lv$|^en$|^ru$")
        ],
        "END_ROUTES": [
            CallbackQueryHandler(end, pattern="^end$"),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
    name="user_interactions",
)