# TO-DO: copyright

import json
import logging
import yaml
import pytz
from thefuzz import process

from datetime import datetime, timedelta, time
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    ParseMode,
    ReplyKeyboardRemove, 
    Update
)
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler, 
    Filters,
    MessageHandler, 
    Updater
)
from utils.db_utils import DBManager
from utils.event_formatters import prepare_event_details, find_event
from utils.sheet_utils import SheetManager
from utils.translations import translate as _

with open("settings.local.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

host = config["DB_HOST"]
port = config["DB_PORT"]
dbname = config["DB_NAME"]
user = config["DB_USER"]
password = config["DB_PASSWORD"]
client_id = config["GOOGLE_CLIENT_ID"]
client_secret = config["GOOGLE_CLIENT_SECRET"]


db = DBManager(host, dbname, user, password, port)
sheet = SheetManager(client_id, client_secret)

def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    group_id = -1001617590404
    checker = context.bot.getChatMember(group_id, update.effective_chat.id)
    if checker["status"] == "left":
        context.bot.send_message(
            update.effective_chat.id,
            text = "Please join our telegram group to use the bot, we offer a lot there as well!\nhttps://t.me/wegotonightinriga"
        )
        return

    else:
        db.update_joined_group(update.effective_chat.id, True)

    edit_msg = True
    if update.callback_query:
        lang = update.callback_query.data
        user = {
            "id": update.callback_query.message.chat_id
        }
        if db.get_account(user.get("id")).get("lang") is None:
            db.update_selected_lang(user.get("id"), lang)

        lang_mapping = {
            "en": "🇬🇧",
            "lv": "🇱🇻",
            "ru": "🇷🇺"
        }

        context.bot.send_message(
            update.effective_user.id,
            text=f"You have selected {lang_mapping.get(lang)} as your preferred language, you can always change it using /settings command.",
        )

        if not context.chat_data.get("lang"):
            context.chat_data["lang"] = db.get_account(user["id"])["lang"]
        lang = context.chat_data["lang"]

        group_id = -1001617590404
        checker = context.bot.getChatMember(group_id, update.effective_chat.id)

        if checker["status"] == "left":
            context.bot.send_message(
                update.effective_chat.id,
                text = "Please join our telegram group to use the bot, we offer a lot there as well!\nhttps://t.me/wegotonightinriga"
            )
            return
        
        elif not db.get_joined_group_status(update.effective_chat.id):
            db.update_joined_group(update.effective_chat.id, True)

        keyboard = [
            [InlineKeyboardButton(_("Today", lang), callback_data="today")],
            [InlineKeyboardButton(_("This week", lang), callback_data="week")],
            [InlineKeyboardButton(_("This month", lang), callback_data="month")],
        ]

        context.bot.send_message(
            update.effective_user.id,
            text=_("When would you like to go?", context.chat_data["lang"]),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return "START_ROUTES"

    if update.message:
        message_date = update.message.date.strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.utcnow()-timedelta(minutes=1)
        current_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        if message_date < current_date:
            return
        
        user = update.message.from_user
        logger.info(f"{user.first_name}, started the conversation. User ID: {user.id}")

        referal = context.args[0] if context.args else None
        if db.get_account(user.id) is None:
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
            db.create_account(user, referal)

            return "START_ROUTES"
        edit_msg = False

    elif context.chat_data.get("message"):
        update.message = context.chat_data["message"]

    if not context.chat_data.get("lang"):
        context.chat_data["lang"] = db.get_account(user["id"])["lang"]
    lang = context.chat_data["lang"]
    keyboard = [
        [InlineKeyboardButton(_("Today", lang), callback_data="today")],
        [InlineKeyboardButton(_("This week", lang), callback_data="week")],
        [InlineKeyboardButton(_("This month", lang), callback_data="month")],
    ]

    if edit_msg:
        message = update.callback_query
        message.answer()
        message.edit_message_text(
            text=_("When would you like to go?", context.chat_data["lang"]),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    else:
        update.message.reply_text(
            text=_("When would you like to go?", context.chat_data["lang"]),
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


def add_buttons(
    counter, 
    keyboard, 
    increment, 
    event_group, 
    selected_event_type
):
    if counter != 0 and counter+increment != len(event_group):
        keyboard[-1:1] = [
            [
                InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{counter-7}"),
                InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{counter+increment}")
            ]
        ]

    if counter != 0 and counter+increment >= len(event_group):
        keyboard[-1:1] = [[InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{counter-7}")]]

    if counter == 0 and counter+increment < len(event_group):
        keyboard[-1:1] = [[InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{counter+increment}")]]

    return keyboard, counter


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

def search_by_name_start(update: Update, context: CallbackContext) -> None:
    """Search by name for user input"""
    group_id = -1001617590404
    checker = update.message.bot.getChatMember(group_id, update.effective_chat.id)
    
    if checker["status"] == "left":
        update.message.bot.send_message(
        update.effective_chat.id,
        text = "Please join our telegram group to use the bot, we offer a lot there as well!\nhttps://t.me/wegotonightinriga")
        
        return
    else:
        if not context.chat_data.get("lang"):
            context.chat_data["lang"] = db.get_account(update.effective_user.id)["lang"]
        lang = context.chat_data["lang"]
        update.message.bot.send_message(
            update.effective_user.id,
            text=_("What are you looking for?", lang)
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


def pushadvert(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"User {user.id} wrote pushadvert.")
    update.message.reply_text(
        text=(f"You started the pushadvert command, write an advertisment that can be posted in the group chat of WeGoTonight"),
        reply_markup=ReplyKeyboardRemove(),
    )
    return "PUSH"


def push(update: Update, context: CallbackContext) -> int:
    logger.info(f"User sent an advert. {update.effective_chat.id}")
    update.message.reply_text(
        text=(f"Sent for approval to the admin, if it is approved, it will be posted in the group."
              f"\nIf it is not approved, you will be notified"),
        reply_markup= ReplyKeyboardRemove(),
    )
    ADMIN_id = 1699557868
    data = db.get_account(update.effective_chat.id)
    advert_id = db.create_advert(update.message.message_id, data.get("id"))
    update.message.bot.forward_message(
        ADMIN_id,
        update.effective_chat.id,
        update.message.message_id
    )
    update.message.bot.send_message(ADMIN_id, advert_id)
        
    return ConversationHandler.END

def approval(update: Update, context: CallbackContext) -> int:
    ADMIN_id = 1699557868
    if update.effective_chat.id == ADMIN_id:
        update.message.reply_text(
                text=(f"Please write the id of the advert you're approving," 
                      f"\nwhich is stated under the advert you want to approve"),
                reply_markup= ReplyKeyboardRemove(),
        )

    return "PUSH_TO_GROUP"

def push_to_group(update: Update, context: CallbackContext) -> int:
    advert_id = update.message.text
    advert = db.get_advert(advert_id)
    if not advert:
        update.message.reply_text(
                text=(f"Advert with id \"{advert_id}\" does not exist"),
        )

        return ConversationHandler.END
    advert_msg_id = advert.get("advert_msg_id")
    advert_owner = db.get_account_by_owner_id(advert.get("owner_id"))
    update.message.bot.send_message(
        advert_owner.get("telegram_user_id"), 
        text=(f"Your advert has been posted to our group. " 
              "\nYou're welcome!")
    )
    
    group_id = -1001617590404
    update.message.bot.copy_message(
        group_id,
        advert_owner.get("telegram_user_id"),
        advert_msg_id
    )
    
    db.delete_advert(advert.get("id"))

    return ConversationHandler.END

def denial(update: Update, context: CallbackContext) -> int:
    ADMIN_id = 1699557868
    if update.effective_chat.id == ADMIN_id:
        update.message.reply_text(
                text=(f"Please write the id of the advert you're denying," 
                      f"\nwhich is stated under the advert you want to deny"),
                reply_markup= ReplyKeyboardRemove(),
        )

    return "DENY"

def denial_exact_ad(update: Update, context: CallbackContext) -> int:
    advert_id = update.message.text
    advert = db.get_advert(advert_id)
    if not advert:
        update.message.reply_text(
                text=(f"Advert with id \"{advert_id}\" does not exist"),
        )

        return ConversationHandler.END
    else:
        advert_owner = db.get_account_by_owner_id(advert.get("owner_id"))
        update.message.bot.send_message(
            advert_owner.get("telegram_user_id"), 
            text=(f"Your advert has been denied, you can find the reason in the next message. " 
                "\nPlease contact us if you think something isn't right wegotonight.dev@gmail.com!")
        )
        db.delete_advert(advert.get("id"))
        context.user_data["chat_id"] = advert_owner.get("telegram_user_id")
        update.message.reply_text(
                text=(f"Please write the reason of denial"),
        )
    return "REASON"

def denial_reason(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    update.message.bot.send_message(
        context.user_data["chat_id"],
        text
    )
    return ConversationHandler.END


def event_list_manual_update(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user

    if db.get_account(user.id).get("is_staff"):
        sheet.get_sheet()
        update.message.reply_text(
            text="Event list updated successfully!",
        )
        logger.info(f"{user.first_name} updated event list manually. User ID: {user.id}")
    else:
        return

def event_list_updater(update: Update) -> None:
    sheet.get_sheet()
    return

def settings(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Language", callback_data="edit_language")]
    ]

    context.bot.send_message(
        update.effective_chat.id,
        text="Settings: ",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "SELECTED"

def edit_language(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧", callback_data="new-en"),
            InlineKeyboardButton("🇱🇻", callback_data="new-lv"),
            InlineKeyboardButton("🇷🇺", callback_data="new-ru"),
        ]
    ]

    context.bot.send_message(
        update.effective_chat.id,
        text="Please select your preferred language",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return "SELECTED"

def save_language(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    message.answer()
    lang = message.data.split("-")[1]
    if db.get_account(update.effective_user.id):
        db.update_selected_lang(update.effective_user.id, lang)

    else:
        db.create_account(update.effective_user)
        db.update_selected_lang(update.effective_user.id, lang)

    lang_mapping = {
        "en": "🇬🇧",
        "lv": "🇱🇻",
        "ru": "🇷🇺"
    }

    context.chat_data["lang"] = lang

    context.bot.send_message(
        update.effective_user.id,
        text=f"You have selected {lang_mapping.get(lang)} as your preferred language, you can always change it using /settings command.",
    )

    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config["TOKEN"])
    sheet.get_sheet()

    updater.job_queue.run_daily(event_list_updater,
                                time(hour=4, minute=00, tzinfo=pytz.timezone('Europe/Riga')),
                                days=(0, 1, 2, 3, 4, 5, 6), name="sheet", context=None)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Setup conversation handler with the states START and END
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
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
    push_handler = ConversationHandler(
        entry_points=[CommandHandler("pushadvert", pushadvert), CommandHandler("approve", approval)],
                    
        states={
            "PUSH": [
                MessageHandler(
                    Filters.photo | Filters.text & ~(Filters.command | Filters.regex("^Done$")), push, pass_chat_data= True
                ),
            ],
            "PUSH_TO_GROUP": [
                MessageHandler(
                    Filters.photo | Filters.text & ~(Filters.command | Filters.regex("^Done$")), push_to_group, pass_chat_data= True
                ),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done$"),push)],
        name="push_advert",
    )
    denial_handler = ConversationHandler(
        entry_points=[CommandHandler("deny", denial)],
                    
        states={
            "DENY": [
                MessageHandler(
                    Filters.photo | Filters.text & ~(Filters.command | Filters.regex("^Done$")), denial_exact_ad, pass_chat_data= True
                ),
            ],
            "REASON":[
                MessageHandler(
                    Filters.photo | Filters.text & ~(Filters.command | Filters.regex("^Done$")), denial_reason, pass_chat_data= True
                ),
            ]
        },
        fallbacks=[MessageHandler(Filters.regex("^Cancel$"),denial)],
        name="deny_advert",
    )
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
                CallbackQueryHandler(end, pattern="^end$"),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done$"),start)],
        name="search",
        allow_reentry=True
    )
    settings_handler = ConversationHandler(
        entry_points=[CommandHandler("settings", settings)],
        states={
            "SETTINGS": [CallbackQueryHandler(settings, pattern="^settings$"),],
            "SELECTED": [
                CallbackQueryHandler(edit_language, pattern="^edit_language$"),
                CallbackQueryHandler(save_language, pattern="^new-(lv$|en$|ru$)"),
            ],
            "END_ROUTES": [CallbackQueryHandler(end, pattern="^end$"),],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done$"),start)],
        name="settings",
        allow_reentry=True
    )


    # Add ConversationHandler to application that will be used for handling updates
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(push_handler)
    dispatcher.add_handler(search_handler)
    dispatcher.add_handler(denial_handler)
    dispatcher.add_handler(settings_handler)
    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("update", event_list_manual_update))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
