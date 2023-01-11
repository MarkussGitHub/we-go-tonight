from copy import deepcopy

from telegram import InlineKeyboardButton
from utils.event_formatters import escape_characters

def prepare_place_details(raw_place):
    
    key_name_mapping = {
        "place_name": "Place name",
        "place_adress": "Location",
        "price_category": "Price",
    }

    KEYS_TO_SKIP = [
        "place_type",
        "sub_img_1",
        "sub_img_2",
        "sub_img_3",
        "sub_img_4",
        "main_image",
        "place_adress_link",
        "phone",
        "email",
        "menu_sub1",
        "menu_sub2",
        "menu_sub3",
        "drink_menu",
        "drink_menu_alc",
        "booking",
        "page",
    ]
    
    raw_place_copy = deepcopy(raw_place)
    for key, value in raw_place.items():
        if value == '':
            del raw_place_copy[key]

    place = (
        f'[​​​​​​​​​​​]({raw_place_copy.get("main_image", "")})'
        f'*{raw_place_copy["place_name"]}*\n\n'
    )
    location = {}

    if raw_place_copy.get("place_name"):
        del raw_place_copy["place_name"]
    if raw_place_copy.get("main_image"):
        del raw_place_copy["main_image"]

    for key, value in raw_place_copy.items():
        if key in KEYS_TO_SKIP:
            continue
        if key == "place_desc":
            place += f"{escape_characters(value)}\n"
            continue
        if key == "place_category":
            place += f"{escape_characters(value)}\n"
        if key == "place_adress":
            location["name"] = value
            place += f'{key_name_mapping[key]}: {value}\n'
            continue
        if key == "place_adress_link":
            location["link"] = value
            continue
        place += f'{key_name_mapping[key]}: {value}\n'

    return place, location

