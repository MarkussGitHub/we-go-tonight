import json
from datetime import datetime

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ParseMode,
    Update
)
from telegram.ext import (
    CallbackContext
)

from utils.event_formatters import prepare_event_details
from utils.translations import translate as _


def event_categories(update: Update, context: CallbackContext) -> int:
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
    return "EVENTS"


def event_selection(update: Update, context: CallbackContext) -> int:
    """Event list for selected type"""
    message = update.callback_query
    selected_event_type = message.data
    lang = context.chat_data["lang"]
    message.answer()

    if "-" not in selected_event_type:
        page = 1
    else:
        try:
            page = int(selected_event_type.split("-")[1])
        except ValueError:
            page = 1
        selected_event_type = selected_event_type.split("-")[0]

    keyboard = []

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        event_group = jzon["events"][context.user_data["date"]][selected_event_type]

    event_group_page = [event for event in event_group if event['page'] == page]

    if not event_group_page:
        context.chat_data["message"] = message.message

        keyboard = [
            [InlineKeyboardButton(f"📅 {_('Choose other date', lang)}", callback_data="events")],
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

        return "EVENTS"

    else:
        prev_date = datetime.min
        for event in event_group_page:
            start_date = datetime.strptime(event["start_date"], "%d/%m/%Y %H:%M")
            if prev_date.date() < start_date.date():
                prev_date = start_date
                keyboard.append([InlineKeyboardButton(f"📅 {prev_date.date()}", callback_data=f"placeholder")])
            keyboard.append([InlineKeyboardButton(f"{event['event_name']}", callback_data=f"details-{selected_event_type}-{page}-{event['id']}")])

    event_type_emoji_mapping = {
        "Concerts/Parties": f"🎸 {_('Concerts/Parties', lang)} 🎉",
        "Culture": f"⛩️ {_('Culture', lang)} 🗽",
        "Workshop": f"🧩 {_('Workshop', lang)} 🛍️",
        "Food/Drinks": f"🍱 {_('Food/Drinks', lang)} 🥂",
        "Art/Literature": f"🎨 {_('Art/Literature', lang)} 📚",
        "Theatre/Stand up": f"🎭 {_('Theatre/Stand up', lang)} 🎤",
    }
    for event in event_group:
        if page == 1:
            keyboard.append([InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{page+1}")])
            break

        if page > 1 and event_group[-1]["page"] >= page+1:
            keyboard.append([
                InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{page-1}"),
                InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{page+1}")
            ])
            break

        if page > 1 and not event_group[-1]["page"] >= page+1:
            keyboard.append([InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{page-1}")])
            break

    keyboard.append([
            InlineKeyboardButton(f"📄 {_('Event Menu', lang)}", callback_data="event_type"),
            InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
        ])

    message.edit_message_text(
        text=event_type_emoji_mapping.get(selected_event_type),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    return "EVENTS"


def event_details(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    lang = context.chat_data["lang"]
    args = message.data.split("-", 3)
    selected_event_type = args[1]
    page = int(args[2])
    event_id = str(args[3])
    message.answer()

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)

    for event in jzon["events"][context.user_data["date"]][selected_event_type]:
        if event["id"] == event_id:
            event, location = prepare_event_details(event)
            break

    keyboard = [
        [],
        [
            InlineKeyboardButton(_("Back", lang), callback_data=f"{selected_event_type}-{page}"),
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

    return "EVENTS"