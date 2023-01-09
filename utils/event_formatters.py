from copy import deepcopy

from telegram import InlineKeyboardButton


def escape_characters(text: str) -> str:
    for symbol in ["_", "*", "`", "["]:
        text = text.replace(symbol, f"\{symbol}")

    return text

def prepare_event_details(raw_event):
    key_name_mapping = {
        "location": "Location",
        "location_link": "Location link",
        "start_date": "Start date",
        "end_date": "End date",
        "contact_telegram": "Contact telegram",
        "contact_number": "Contact number",
        "contact_mail": "Contact mail",
    }

    KEYS_TO_SKIP = [
        "open_during",
        "event_name",
        "hyperlink_text",
        "booking_availability",
        "event_type",
        "availability_left",
        "id",
        "page",
    ]

    raw_event_copy = deepcopy(raw_event)
    for key, value in raw_event.items():
        if value == '':
            del raw_event_copy[key]

    event = (
        f'[​​​​​​​​​​​]({raw_event_copy.get("event_Image_URL", "")})'
        f'*{raw_event_copy["full_event_name"]}*\n\n'
    )
    location = {}

    if raw_event_copy.get("full_event_name"):
        del raw_event_copy["full_event_name"]
    if raw_event_copy.get("event_Image_URL"):
        del raw_event_copy["event_Image_URL"]

    for key, value in raw_event_copy.items():
        if key in KEYS_TO_SKIP:
            continue
        if key == "hyperlink":
            event += f'[More info here.]({value})\n'
            continue
        if key == "start_date":
            event += f'{key_name_mapping[key]}: {value}\n'
            continue
        if key == "end_date":
            event += f'{key_name_mapping[key]}: {value}\n'
            continue
        if key == "location":
            location["name"] = value
            continue
        if key == "location_link":
            location["link"] = value
            continue
        if key == "event_desc":
            event += f"{escape_characters(value)}\n"
            continue
        event += f'{key_name_mapping[key]}: {value}\n'

    return event, location


def find_event(result, raw_events):
    for date_key, date_value in raw_events.items():
        for ctgry_name, ctgry_value in date_value.items():
            for event in ctgry_value:
                for key, value in event.items():
                    if value == result:
                        return date_key, ctgry_name, value

def add_buttons(
    counter, 
    keyboard, 
    increment, 
    event_group, 
    selected_event_type,
    page_size
):
    previous_page = counter - page_size
    next_page = counter + page_size

    if previous_page >= 0:
        # Add a "previous" button
        keyboard[-1:1] = [[InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{previous_page}")]]
    if next_page < len(event_group):
        # Add a "next" button
        keyboard[-1:1] = [[InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{next_page}")]]
    if previous_page >= 0 and next_page < len(event_group):
        # Add both "previous" and "next" buttons
        keyboard[-1:1] = [
            [
                InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{previous_page}"),
                InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{next_page}")
            ]
        ]

    return keyboard, counter