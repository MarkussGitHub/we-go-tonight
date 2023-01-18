import json
from datetime import datetime

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

from utils.event_formatters import add_buttons
from utils.place_formatters import prepare_place_details
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
    """Place list for selected type"""
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
        keyboard.append([InlineKeyboardButton(f"{place['place_name']}", callback_data=f"place_details-{selected_place_type}-{page}-{place['place_name']}")])

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
    message = update.callback_query
    lang = context.chat_data["lang"]
    args = message.data.split("-", 3)
    selected_place_type = args[1]
    page = int(args[2])
    place_name = str(args[3])
    message.answer()

    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)

    for place in jzon["places"][selected_place_type]:
        if place["place_name"] == place_name:
            event, location = prepare_place_details(place)
            break

    keyboard = [
        [],
        [],
        [
            InlineKeyboardButton("📸"+_("View Photos", lang)+" 📸", callback_data=f"photos-{selected_place_type}-{place_name}")
        ],
        [
            InlineKeyboardButton(_("Back", lang), callback_data=f"{selected_place_type}-{page}"),
        ],
        [
            InlineKeyboardButton(f"📄{_('Place Menu', lang)} 📄", callback_data="places"),
            InlineKeyboardButton(f"❌{_('Cancel', lang)} ❌", callback_data="end"),
        ],
    ]
    for place in jzon["places"][selected_place_type]:
        if place["place_name"] == place_name:
            if "drink_menu" in place or "drink_menu_alc" in place:
                keyboard[1].append(InlineKeyboardButton(text=f"🍹"+_("View Drink Menu", lang)+"🍹", callback_data=f"drinks-{selected_place_type}-{place_name}"))
            if "menu_sub1" in place or "menu_sub2" in place or "menu_sub3" in place:
                keyboard[1].append(InlineKeyboardButton(text=f"🍽️"+_("View Food Menu", lang)+" 🍽️", callback_data=f"menu-{selected_place_type}-{place_name}"))
            if "email" in place or "phone" in place:
                if place["email"] != "" or place["phone"] != "":
                    keyboard[2].append(InlineKeyboardButton(text=f"ℹ️"+_("Contacts", lang)+" ℹ️", callback_data=f"contacts-{selected_place_type}-{place_name}"))  
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
    args = message.data.split("-", 3)
    place_name = str(args[2])
    selected_place_type = str(args[1])
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
        place_group = jzon["places"][selected_place_type]
    for place in place_group:
        if place["place_name"] == place_name:
            if place["sub_img_4"] != "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["sub_img_1"]),
                        InputMediaPhoto(place["sub_img_2"]),
                        InputMediaPhoto(place["sub_img_3"]),
                        InputMediaPhoto(place["sub_img_4"]),
                    ]
                )
                return "PLACES"
            if place["sub_img_3"] != "" and place["sub_img_4"] == "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["sub_img_1"]),
                        InputMediaPhoto(place["sub_img_2"]),
                        InputMediaPhoto(place["sub_img_3"]),
                    ]
                )
                return "PLACES"
            
            if place["sub_img_2"] != "" and place["sub_img_3"] == "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["sub_img_1"]),
                        InputMediaPhoto(place["sub_img_2"]),
                    ]
                )
                return "PLACES"
            
            if place["sub_img_1"] != "" and place["sub_img_2"] == "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["sub_img_1"]),
                    ]
                )
                return "PLACES"
                
        
def view_menu(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    args = message.data.split("-", 3)
    place_name = str(args[2])
    selected_place_type = str(args[1])
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
        place_group = jzon["places"][selected_place_type]
    for place in place_group:
        if place["place_name"] == place_name:
            if place["menu_sub2"] == "" and place["menu_sub1"] !="":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["menu_sub1"]),
                    ]
                )
                return "PLACES"
            else:
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["menu_sub1"]),
                        InputMediaPhoto(place["menu_sub2"]),
                    ]
                )
                return "PLACES"
     
def view_drink_menu(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    args = message.data.split("-", 3)
    place_name = str(args[2])
    selected_place_type = str(args[1])
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
        place_group = jzon["places"][selected_place_type]
    for place in place_group:
        if place["place_name"] == place_name:
            if place["drink_menu"] != "" and place["drink_menu_alc"] != "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["drink_menu"]),
                        InputMediaPhoto(place["drink_menu_alc"]),
                    ]
                )
                return "PLACES"   
            if place["drink_menu"] != "" and place["drink_menu_alc"] == "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["drink_menu"]),
                    ]
                )
            if place["drink_menu"] == "" and place["drink_menu_alc"] != "":
                context.bot.send_media_group(
                    update.effective_chat.id,
                    [
                        InputMediaPhoto(place["drink_menu_alc"]),
                    ]
                )
                
def contacts (update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    args = message.data.split("-", 3)
    place_name = str(args[2])
    lang = context.chat_data["lang"]
    selected_place_type = str(args[1])
    
    if "-" not in selected_place_type:
            page = 1
    else:
        try:
            page = int(selected_place_type.split("-")[1])
        except ValueError:
            page = 1
        selected_place_type = selected_place_type.split("-")[0]
    
    with open("data/place_list.json", "r") as f:
        jzon = json.load(f)
        place_group = jzon["places"][selected_place_type]
        
    keyboard =[
        [
            InlineKeyboardButton(_("Back", lang), callback_data=f"place_details-{selected_place_type}-{page}-{place_name}"),
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