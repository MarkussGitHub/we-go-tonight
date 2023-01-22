import json

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ParseMode,
    Update,
    InputMediaPhoto
)
from telegram.ext import (
    CallbackContext
)

from utils.place_formatters import prepare_place_details
from utils.translations import translate as _
from utils.event_formatters import prepare_event_details
from copy import deepcopy

def place_categories(update: Update, context: CallbackContext) -> int:
    """Place type menu"""
    message = update.callback_query
    lang = context.chat_data["lang"]
    message.answer()

    if context.chat_data.get("photos_to_delete"):
        for photo in context.chat_data["photos_to_delete"]:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=photo)
        context.chat_data["photos_to_delete"] = None

    keyboard = [
        [InlineKeyboardButton(f"{_('Food & Drinks', lang)}", callback_data="Food & Drinks")],
        [InlineKeyboardButton(f"{_('Culture Spaces', lang)}", callback_data="Culture Spaces")],
        [InlineKeyboardButton(f"{_('Entertainment', lang)}", callback_data="Entertainment")],
        [InlineKeyboardButton(f"{_('Cinema & Theater', lang)}", callback_data="Cinema & Theater")],
        [InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"start")],
    ]

    message.edit_message_text(
        text=_("Here are the types of Places I can offer to you", lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "PLACES"


def place_sub_categories(update: Update, context: CallbackContext) -> int:
    """Place sub type menu"""
    message = update.callback_query

    selected_place_type = message.data
    context.chat_data["selected_place_type"] = selected_place_type
    lang = context.chat_data["lang"]
    message.answer()

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type]

    keyboard = []

    place_group_copy = deepcopy(place_group)

    for key, value in place_group_copy.items():
        if len(value) == 0:
            del place_group[key]

    for place_sub_type in place_group:
        keyboard.append([InlineKeyboardButton(f"{_(place_sub_type, lang)}", callback_data=f"{selected_place_type}-{place_sub_type}")])

    keyboard.append([InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data="places")])

    message.edit_message_text(
        text=_(f"Here are the types of {selected_place_type} I can offer to you", lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "PLACES"


def place_selection(update: Update, context: CallbackContext) -> int:
    """Place list for selected type"""
    message = update.callback_query

    if context.chat_data.get("photos_to_delete"):
        for photo in context.chat_data["photos_to_delete"]:
            context.bot.delete_message(chat_id=update.effective_chat.id, message_id=photo)
        context.chat_data["photos_to_delete"] = None

    args = message.data.split("-", 2)
    selected_place_type = args[0]
    selected_place_sub_type = args[1]
    context.chat_data["selected_place_sub_type"] = selected_place_sub_type

    lang = context.chat_data["lang"]
    message.answer()

    try:
        page = int(args[2])
    except IndexError:
        page = 1

    keyboard = []

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type][selected_place_sub_type]

    place_group_page = [place for place in place_group if place['page'] == page]

    for place in place_group_page:
        keyboard.append([InlineKeyboardButton(f"{place['place_name']}", callback_data=f"place_details-{page}-{place['place_name']}")])

    for place in place_group:
        if page == 1 and place["page"] == page+1:
            keyboard.append([InlineKeyboardButton("➡️", callback_data=f"{selected_place_type}-{selected_place_sub_type}-{page+1}")])
            break

        if page > 1 and place_group[-1]["page"] >= page+1:
            keyboard.append([
                InlineKeyboardButton("⬅️", callback_data=f"{selected_place_type}-{selected_place_sub_type}-{page-1}"),
                InlineKeyboardButton("➡️", callback_data=f"{selected_place_type}-{selected_place_sub_type}-{page+1}")
            ])
            break

        if page > 1 and not place_group[-1]["page"] >= page+1:
            keyboard.append([InlineKeyboardButton("⬅️", callback_data=f"{selected_place_type}-{selected_place_sub_type}-{page-1}")])
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
    message = update.callback_query
    lang = context.chat_data["lang"]
    args = message.data.split("-", 2)
    selected_place_type = context.chat_data["selected_place_type"]
    selected_place_sub_type = context.chat_data["selected_place_sub_type"]
    page = int(args[1])
    context.chat_data["page"] = page
    place_name = str(args[2])
    message.answer()

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)

    for place in jzon["places"][selected_place_type][selected_place_sub_type]:
        if place["place_name"] == place_name:
            event, location = prepare_place_details(place)
            break

    keyboard = [
        [],
        [],
        [
            InlineKeyboardButton("🧧 "+_("Hosted Events", lang), callback_data=f"event_button-{place_name}-{page}"),
            InlineKeyboardButton("📸 "+_("Photos", lang), callback_data=f"photos-{place_name}"),
        ],
        [],
        [
            InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"{selected_place_type}-{selected_place_sub_type}-{page}"),
        ],
        [
            InlineKeyboardButton(f"📄 {_('Place Menu', lang)}", callback_data="places"),
            InlineKeyboardButton(f"❌ {_('Cancel', lang)}", callback_data="end"),
        ],
    ]

    for place in jzon["places"][selected_place_type][selected_place_sub_type]:
        if place["place_name"] == place_name:
            if "drink_menu" in place or "drink_menu_alc" in place:
                keyboard[1].append(InlineKeyboardButton(text=f"🍹 "+_("Drink Menu", lang), callback_data=f"drinks-{place_name}"))

            if "menu_sub1" in place or "menu_sub2" in place or "menu_sub3" in place:
                keyboard[1].append(InlineKeyboardButton(text=f"🍔 "+_("Food Menu", lang), callback_data=f"menu-{place_name}"))

            if "email" in place or "phone" in place:
                if place["email"] != "" or place["phone"] != "":
                    keyboard[3].append(InlineKeyboardButton(text=f"ℹ️ "+_("Contacts", lang), callback_data=f"contacts-{page}-{place_name}"))  

    if location and location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

    elif location and not location.get("link"):
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', callback_data="placeholder"))    

    message.edit_message_text(
        text=(event),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return "PLACES"


def view_photos(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    args = message.data.split("-", 1)
    selected_place_type = context.chat_data["selected_place_type"]
    selected_place_sub_type = context.chat_data["selected_place_sub_type"]
    place_name = str(args[1])

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type][selected_place_sub_type]

    for place in place_group:
        if place["place_name"] == place_name:
            images = []
            for i in range(1, 5):
                if place.get(f"sub_img_{i}") and place.get(f"sub_img_{i}") != "":
                    images.append(InputMediaPhoto(place["sub_img_{}".format(i)]))
            messages = context.bot.send_media_group(update.effective_chat.id, images)

            msg_ids = [msg.message_id for msg in messages]

            if context.chat_data.get("photos_to_delete"):
                context.chat_data["photos_to_delete"] += (msg_ids)
            else:
                context.chat_data["photos_to_delete"] = msg_ids


def view_menu(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    args = message.data.split("-", 1)
    selected_place_type = context.chat_data["selected_place_type"]
    selected_place_sub_type = context.chat_data["selected_place_sub_type"]
    place_name = str(args[1])
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type][selected_place_sub_type]
    for place in place_group:
        if place["place_name"] == place_name:
            media_group = []
            if place.get("menu_sub1", "") != "":
                media_group.append(InputMediaPhoto(place["menu_sub1"]))
            if place.get("menu_sub2", "") != "":
                media_group.append(InputMediaPhoto(place["menu_sub2"]))
            messages = context.bot.send_media_group(update.effective_chat.id, media_group)

            msg_ids = [msg.message_id for msg in messages]

            if context.chat_data.get("photos_to_delete"):
                context.chat_data["photos_to_delete"] += (msg_ids)
            else:
                context.chat_data["photos_to_delete"] = msg_ids
     
def view_drink_menu(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    args = message.data.split("-", 1)
    selected_place_type = context.chat_data["selected_place_type"]
    selected_place_sub_type = context.chat_data["selected_place_sub_type"]
    place_name = str(args[1])
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type][selected_place_sub_type]
    for place in place_group:
        if place["place_name"] == place_name:
            media_group = []
            if place["drink_menu"] != "":
                media_group.append(InputMediaPhoto(place["drink_menu"]))
            if place["drink_menu_alc"] != "":
                media_group.append(InputMediaPhoto(place["drink_menu_alc"]))
            messages = context.bot.send_media_group(update.effective_chat.id, media_group)

            msg_ids = [msg.message_id for msg in messages]

            if context.chat_data.get("photos_to_delete"):
                context.chat_data["photos_to_delete"] += (msg_ids)
            else:
                context.chat_data["photos_to_delete"] = msg_ids
                
def contacts(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    args = message.data.split("-", 2)
    selected_place_type = context.chat_data["selected_place_type"]
    selected_place_sub_type = context.chat_data["selected_place_sub_type"]
    page = str(args[1])
    place_name = str(args[2])
    lang = context.chat_data["lang"]
    
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
    place_group = jzon["places"][selected_place_type][selected_place_sub_type]

    keyboard =[
        [
            InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"place_details-{page}-{place_name}"),
        ]
    ]
    
    for place in place_group:
        if place["place_name"] == place_name:
            if place["phone"] != "" and place["email"] != "":
                message.edit_message_text(
                    text =f"\nE-mail: +{(place['email'])}\n Phone:{(place['phone'])}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return "PLACES"
            
            if place["phone"] == "" and place["email"] != "":
                message.edit_message_text(
                    text =f"\n*E-mail:* +{(place['email'])}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN,
                )                
                return "PLACES"

            if place["phone"] != "" and place["email"] == "":
                message.edit_message_text(
                    text =f"\n *Phone:* +{(place['phone'])}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode=ParseMode.MARKDOWN,
                )                
                return "PLACES"


def event_button(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    args = message.data.split("-", 2)
    place_name = str(args[1])
    page = int(args[2])
    lang = context.chat_data["lang"]

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)

    month = jzon["events"]["month"]
    place_events = []
    for event_type in month.values():
        for event in event_type:
            if event["location"] == place_name:
                place_events.append(event)

    keyboard = []

    if len(place_events) == 0:
        text = f"{place_name} isn't hosting any events at this moment"
    
    else:
        text = f"{place_name} Events"

    for event in place_events:
        keyboard.append([InlineKeyboardButton(f"{event['event_name']}", callback_data=f"p_details-{event['event_type']}-{event['id']}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"place_details-{page}-{place_name}")])

    message.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return "PLACES"

def place_event_details(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    lang = context.chat_data["lang"]
    args = message.data.split("-", 2)
    selected_event_type = args[1]
    event_id = str(args[2])
    message.answer()

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)

    for event in jzon["events"]["month"][selected_event_type]:
        if event["id"] == event_id:
            event, location = prepare_event_details(event)
            break

    keyboard = [
        [],
        [
            InlineKeyboardButton("⬅️ " + _("Back", lang), callback_data=f"place_details-{context.chat_data['page']}-{location['name']}"),
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

    return "PLACES"