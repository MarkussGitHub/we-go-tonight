import json
import logging

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ParseMode,
    Update
)
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler, 
    Filters,
    MessageHandler
)
from thefuzz import process

from utils.db.connection import db
from utils.event_formatters import find_event, prepare_event_details
from utils.translations import translate as _
from handlers.wrappers import ignore_old_messages, valid_user

logger = logging.getLogger(__name__)


# @valid_user
@ignore_old_messages
def search_by_name_start(update: Update, context: CallbackContext) -> None:
    """Search by name for user input"""
    if not context.chat_data.get("lang"):
        context.chat_data["lang"] = db.get_account(update.effective_user.id).get("lang")
    lang = context.chat_data["lang"] if context.chat_data["lang"] else "en"
    update.message.bot.send_message(
        update.effective_user.id,
        text=_("What event or place are you looking for?", lang)
    )
    return "SEARCH"


def get_searched_data(update: Update, context: CallbackContext) -> None:
    """Searching for close matches using user inputed name"""
    location = {}
    lang = context.chat_data["lang"]
    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        raw_events = jzon["events"]

    event_names = []
    for date_key, date_value in raw_events.items():
        for ctgry_name, ctgry_value in date_value.items():
            for event in ctgry_value:
                for key, value in event.items():
                    if key == "event_name" and value not in event_names:
                        event_names.append(value)
                        continue

    res = process.extractBests(update.message.text, event_names, limit=5, score_cutoff=50)
    keyboard = [[]]

    if len(res) == 1:
        date_key, ctgry_name, event_to_find = find_event(res[0][0], raw_events)
        for event in raw_events[date_key][ctgry_name]:
            if event["event_name"] == event_to_find:
                event, location = prepare_event_details(event)
                break
        
        if location and location.get("link"):
            keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

        elif location and not location.get("link"):
            keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', callback_data="placeholder"))

        update.message.bot.send_message(
            update.effective_user.id,
            text=(event),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

    elif len(res) > 1:
        context.chat_data["found_events"] = []
        for option in res:
            date_key, ctgry_name, event_to_find = find_event(option[0], raw_events)
            for event in raw_events[date_key][ctgry_name]:
                if event["event_name"] == event_to_find:
                    context.chat_data["found_events"].append(event)
                    break
            keyboard.append([InlineKeyboardButton(event_to_find, callback_data=f"searchdetails-{event_to_find}")])

        update.message.bot.send_message(
            update.effective_user.id,
            text=_("Here are events that i could find", lang),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )
        return "END_ROUTES"

    else:
        update.message.bot.send_message(
            update.effective_user.id,
            text="Couldn't find such event",
            parse_mode=ParseMode.MARKDOWN,
        )

    return ConversationHandler.END


def event_details_from_search(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    event_name = message.data.split("-", 1)[1]
    message.answer()
    for event in context.chat_data["found_events"]:
        if event["event_name"] == event_name:
            event, location = prepare_event_details(event)
            break

    keyboard = [[]]

    if location and location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

    elif location and not location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', callback_data="placeholder"))

    message.edit_message_text(
        text=(event),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return ConversationHandler.END


search_handler = ConversationHandler(
    entry_points=[CommandHandler("search", search_by_name_start)],
    states={
        "SEARCH": [
            MessageHandler(
                Filters.text & ~(Filters.command | Filters.regex("^Done$")), get_searched_data, pass_chat_data= True
            ),
        ],
        "END_ROUTES": [
            CallbackQueryHandler(event_details_from_search, pattern="^searchdetails"),
        ],
    },
    fallbacks=[MessageHandler(Filters.regex("^Done$"),search_by_name_start)],
    name="search",
    allow_reentry=True
)