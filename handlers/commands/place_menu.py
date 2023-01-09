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

from utils.event_formatters import add_buttons, prepare_event_details
from utils.translations import translate as _


def place_categories(update: Update, context: CallbackContext) -> int:
    """Place type menu"""
    message = update.callback_query
    lang = context.chat_data["lang"]
    message.answer()

    keyboard = [
        [InlineKeyboardButton(f"{_('Bar', lang)}", callback_data="Bar")],
        [InlineKeyboardButton(f"{_('Restaurant', lang)}", callback_data="Restaurant")],
        [InlineKeyboardButton(f"{_('Cafe', lang)}", callback_data="Cafe")],
        [InlineKeyboardButton(f"{_('Club', lang)}", callback_data="Club")],
        [InlineKeyboardButton(f"{_('Unique', lang)}", callback_data="Unique")],
        [InlineKeyboardButton(f"{_('Cinema', lang)}", callback_data="Cinema")],
        [InlineKeyboardButton(f"{_('Concert venue', lang)}", callback_data="Concert venue")],
        [InlineKeyboardButton(f"{_('Gallery', lang)}", callback_data="Gallery")],
    ]

    message.edit_message_text(
        text=_("Here are the types of Places I can offer to you", lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "PLACES"


def place_selection(update: Update, context: CallbackContext) -> int:
    """Event list for selected type"""
    message = update.callback_query
    selected_place_type = message.data
    lang = context.chat_data["lang"]
    message.answer()

    if "-" not in selected_place_type:
        page = 1
    else:
        try:
            page = int(selected_place_type.split("-")[1])
        except ValueError:
            page = 1
        selected_place_type = selected_place_type.split("-")[0]

    keyboard = []

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
        place_group = jzon["places"][selected_place_type]

    place_group_page = [place for place in place_group if place['page'] == page]

    for place in place_group_page:
        keyboard.append([InlineKeyboardButton(f"{place['place_name']}", callback_data=f"details-{selected_place_type}-{page}-{place['place_name']}")])

    for place in place_group:
        if page == 1 and place["page"] == page+1:
            keyboard.append([InlineKeyboardButton("➡️", callback_data=f"{selected_place_type}-{page+1}")])
            break

        if page > 1 and place_group[-1]["page"] >= page+1:
            keyboard.append([
                InlineKeyboardButton("⬅️", callback_data=f"{selected_place_type}-{page-1}"),
                InlineKeyboardButton("➡️", callback_data=f"{selected_place_type}-{page+1}")
            ])
            break

        if page > 1 and not place_group[-1]["page"] >= page+1:
            keyboard.append([InlineKeyboardButton("⬅️", callback_data=f"{selected_place_type}-{page-1}")])
            break

    keyboard.append([
            InlineKeyboardButton(f"📄 {_('Place Menu', lang)}", callback_data="places"),
            InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
        ])

    message.edit_message_text(
        text=selected_place_type,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    return "PLACES"


def place_details(update: Update, context: CallbackContext) -> int:
    """Place details"""
