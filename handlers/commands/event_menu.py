import json
import logging
from datetime import datetime, timedelta

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
    ConversationHandler
)

from utils.db_connection import db
from utils.event_formatters import add_buttons, prepare_event_details
from utils.translations import translate as _
from handlers.wrappers import ignore_old_messages, valid_user

logger = logging.getLogger(__name__)


@ignore_old_messages
@valid_user
def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    user = update.effective_user  

    # If language was selected
    if update.callback_query and update.callback_query.data in ["en", "lv", "ru"]:
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

    # If started using /start
    if update.message:
        logger.info(f"{user.first_name}, started the conversation. User ID: {user.id}")

        if db.get_account(user.id)["lang"] is None:
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

            return "START_ROUTES"

    # If started over
    elif context.chat_data.get("message"):
        update.message = context.chat_data["message"]

    # If user has no language selected
    if not context.chat_data.get("lang"):
        context.chat_data["lang"] = db.get_account(user["id"])["lang"]
    lang = context.chat_data["lang"]

    keyboard = [
        [InlineKeyboardButton(_("Today", lang), callback_data="today")],
        [InlineKeyboardButton(_("This week", lang), callback_data="week")],
        [InlineKeyboardButton(_("This month", lang), callback_data="month")],
    ]

    # If started over
    if update.callback_query and update.callback_query.data == "start":
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

    return "START_ROUTES"


def event_type(update: Update, context: CallbackContext) -> int:
    """Event type menu"""
    message = update.callback_query
    lang = context.chat_data["lang"]
    if message.data in ["today", "week", "month"]:
        context.user_data["date"] = message.data
    message.answer()

    keyboard = [
        [InlineKeyboardButton(f"🎸 {_('Concerts/Parties', lang)} 🎉", callback_data="Concerts/Parties")],
        [InlineKeyboardButton(f"⛩️ {_('Culture', lang)} 🗽", callback_data="Culture")],
        [InlineKeyboardButton(f"🧩 {_('Workshop', lang)} 🛍️", callback_data="Workshop")],
        [InlineKeyboardButton(f"🍱 {_('Food/Drinks', lang)} 🥂", callback_data="Food/Drinks")],
        [InlineKeyboardButton(f"🎨 {_('Art/Literature', lang)} 📚", callback_data="Art/Literature")],
        [InlineKeyboardButton(f"🎭 {_('Theatre/Stand up', lang)} 🎤", callback_data="Theatre/Stand up")],
    ]

    message.edit_message_text(
        text=_("Here are the types of Events I can offer to you", lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "START_ROUTES"


def event_list(update: Update, context: CallbackContext) -> int:
    """Event list for selected type"""
    message = update.callback_query
    selected_event_type = message.data
    lang = context.chat_data["lang"]
    message.answer()

    if "-" not in selected_event_type:
        counter = 0
    else:
        try:
            counter = int(selected_event_type.split("-")[1])
        except ValueError:
            counter = 0
        selected_event_type = selected_event_type.split("-")[0]

    keyboard = [[]]

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        event_group = jzon["events"][context.user_data["date"]][selected_event_type]

    try:
        date = event_group[counter]["start_date"].split(" ")[0]
        keyboard.insert(-1, [InlineKeyboardButton(f"📅 {date}", callback_data="placeholder")])
        keyboard.insert(-1, [InlineKeyboardButton(event_group[counter]["event_name"], callback_data=f"details-{selected_event_type}-{counter}-{counter}")])
    except IndexError:
        context.chat_data["message"] = message.message

        keyboard = [
            [InlineKeyboardButton(f"📅 {_('Choose other date', lang)}", callback_data="start")],
            [
                InlineKeyboardButton(f"📄 {_('Event Menu', lang)}", callback_data="event_type"),
                InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
            ]
        ]

        message.edit_message_text(
            text=_("Sadly there are no events in this category for selected date", lang) + "😔",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

        return "START_ROUTES"

    last_date = date

    for increment in range(1, 10):
        if len(keyboard) >= 10:
            keyboard, counter = add_buttons(counter, keyboard, increment, event_group, selected_event_type)
            break
        try:
            current_date = event_group[counter+increment]["start_date"].split(" ")[0]
            if datetime.strptime(last_date, "%d/%m/%Y") < datetime.strptime(current_date, "%d/%m/%Y"):
                keyboard.insert(-1, [InlineKeyboardButton(f"📅 {current_date}", callback_data=f"placeholder")])
                last_date = current_date
            if len(keyboard) == 10:
                keyboard[-1:1] = [[InlineKeyboardButton(event_group[counter+increment]["event_name"], callback_data=f"details-{selected_event_type}-{counter+increment}-{counter}")]]
            else:
                keyboard.insert(-1, [InlineKeyboardButton(event_group[counter+increment]["event_name"], callback_data=f"details-{selected_event_type}-{counter+increment}-{counter}")])
        except IndexError:
            keyboard, counter = add_buttons(counter, keyboard, increment, event_group, selected_event_type)
            break
        if increment == 9:
            keyboard, counter = add_buttons(counter, keyboard, increment, event_group, selected_event_type)

    event_type_emoji_mapping = {
        "Concerts/Parties": f"🎸 {_('Concerts/Parties', lang)} 🎉",
        "Culture": f"⛩️ {_('Culture', lang)} 🗽",
        "Workshop": f"🧩 {_('Workshop', lang)} 🛍️",
        "Food/Drinks": f"🍱 {_('Food/Drinks', lang)} 🥂",
        "Art/Literature": f"🎨 {_('Art/Literature', lang)} 📚",
        "Theatre/Stand up": f"🎭 {_('Theatre/Stand up', lang)} 🎤",
    }

    keyboard.insert(-1, [
            InlineKeyboardButton(f"📄 {_('Event Menu', lang)}", callback_data="event_type"),
            InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
        ])

    message.edit_message_text(
        text=event_type_emoji_mapping.get(selected_event_type),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    return "END_ROUTES"


def event_details(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    lang = context.chat_data["lang"]
    selected_event_type = message.data.split("-")[1]
    counter = int(message.data.split("-")[2])
    page_counter = int(message.data.split("-")[3])
    message.answer()

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        selected_event = jzon["events"][context.user_data["date"]][selected_event_type][counter]
    
    event, location = prepare_event_details(selected_event)

    keyboard = [
        [],
        [
            InlineKeyboardButton(_("Back", lang), callback_data=f"{selected_event_type}-{page_counter}"),
        ],
        [
            InlineKeyboardButton(f"📄 {_('Event Menu', lang)}", callback_data="event_type"),
            InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
        ],
    ]

    if location and location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

    elif location and not location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', callback_data="placeholder"))

    message.edit_message_text(
        text=(event),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return "END_ROUTES"


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


event_types = "Concerts/Parties|Culture|Workshop|Food/Drinks|Art/Literature|Theatre/Stand up|"""
event_types_with_counter = f"{event_types}-[0-9]+"
event_type_pattern = "event_type|today|week|month"

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        "START_ROUTES": [
            CallbackQueryHandler(start, pattern="^start$|^lv$|^en$|^ru$"),
            CallbackQueryHandler(event_type, pattern="^" + event_type_pattern + "$"),
            CallbackQueryHandler(event_list, pattern="^" + event_types + "$"),
            CallbackQueryHandler(end, pattern="^end$"),
        ],
        "END_ROUTES": [
            CallbackQueryHandler(event_list, pattern="^" + event_types_with_counter + "$"),
            CallbackQueryHandler(event_details, pattern="^details"),
            CallbackQueryHandler(event_type, pattern="^event_type$"),
            CallbackQueryHandler(end, pattern="^end$"),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
    name="user_interactions",
)