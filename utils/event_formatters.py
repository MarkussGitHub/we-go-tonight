from copy import deepcopy

def prepare_event_details(raw_event):
    key_name_mapping = {
        "event_desc": "Event description",
        "location": "Location",
        "location_link": "Location link",
        "start_date": "Start date",
        "end_date": "End date",
        "contact_telegram": "Contact telegram",
        "contact_number": "Contact number",
        "contact_mail": "Contact mail",
    }

    KEYS_TO_SKIP = [
        "hyperlink_text",
        "booking_availability",
        "start_time",
        "end_time",
        "event_type",
        "availability_left",
    ]

    raw_event_copy = deepcopy(raw_event)
    for key, value in raw_event.items():
        if value == '':
            del raw_event_copy[key]

    event = (
        f'[​​​​​​​​​​​]({raw_event_copy.get("event_Image_URL", "")})'
        f'*{raw_event_copy["event_name"]}*\n\n'
    )
    location = {}

    if raw_event_copy.get("event_name"):
        del raw_event_copy["event_name"]
    if raw_event_copy.get("event_Image_URL"):
        del raw_event_copy["event_Image_URL"]

    for key, value in raw_event_copy.items():
        if key in KEYS_TO_SKIP:
            continue
        if key == "hyperlink":
            event += f'[{raw_event_copy["hyperlink_text"]}]({value})\n'
            continue
        if key == "start_date":
            event += f'{key_name_mapping[key]}: {value} {raw_event_copy.get("start_time", "")}\n'
            continue
        if key == "end_date":
            event += f'{key_name_mapping[key]}: {value} {raw_event_copy.get("end_time", "")}\n'
            continue
        if key == "location":
            location["name"] = value
            continue
        if key == "location_link":
            location["link"] = value
            continue
        event += f'{key_name_mapping[key]}: {value}\n'

    return event, location