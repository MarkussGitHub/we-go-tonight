# TO-DO: copyright

import json
import logging
import yaml
import difflib
import pytz

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
from utils.event_formatters import prepare_event_details
from utils.sheet_utils import SheetManager

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
            db.create_account(user, referal)
        edit_msg = False

    else:
        update.message = context.bot_data["message"]
        edit_msg = True

    keyboard = [
        [InlineKeyboardButton("Today", callback_data="today")],
        [InlineKeyboardButton("This week", callback_data="week")],
        [InlineKeyboardButton("This month", callback_data="month")],
    ]

    if edit_msg:
        message = update.callback_query
        message.answer()
        message.edit_message_text(
            text="When would you like to go?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    else:
        update.message.reply_text(
            text="When would you like to go?",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return "START_ROUTES"


def start_over(update: Update, context: CallbackContext) -> int:
    """Prompt same text & keyboard as `event_type` does but not as new message"""
    message = update.callback_query
    message.answer()

    keyboard = [
        [InlineKeyboardButton("🎸 Concerts/Parties 🎉", callback_data="Concerts/Parties")],
        [InlineKeyboardButton("⛩️ Culture 🗽", callback_data="Culture")],
        [InlineKeyboardButton("🧩 Workshop 🛍️", callback_data="Workshop")],
        [InlineKeyboardButton("🍱 Food/Drinks 🥂", callback_data="Food/Drinks")],
        [InlineKeyboardButton("🎨 Art/Literature 📚", callback_data="Art/Literature")],
        [InlineKeyboardButton("🎭 Theatre/Stand up 🎤", callback_data="Theatre/Stand up")],
    ]

    message.edit_message_text(
        text="Hope you will like something else, I am glad to offer you other options",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "START_ROUTES"


def event_type(update: Update, context: CallbackContext) -> int:
    """Event type menu"""
    message = update.callback_query
    if message.data in ["today", "week", "month"]:
        context.user_data["date"] = message.data
    message.answer()

    keyboard = [
        [InlineKeyboardButton("🎸 Concerts/Parties 🎉", callback_data="Concerts/Parties")],
        [InlineKeyboardButton("⛩️ Culture 🗽", callback_data="Culture")],
        [InlineKeyboardButton("🧩 Workshop 🛍️", callback_data="Workshop")],
        [InlineKeyboardButton("🍱 Food/Drinks 🥂", callback_data="Food/Drinks")],
        [InlineKeyboardButton("🎨 Art/Literature 📚", callback_data="Art/Literature")],
        [InlineKeyboardButton("🎭 Theatre/Stand up 🎤", callback_data="Theatre/Stand up")],
    ]

    message.edit_message_text(
        text="Here are the types of Events I can offer to you or you can choose Any if you are feeling adventurous",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "START_ROUTES"


def help(update: Update, context: CallbackContext) -> int:
    """Help with return to start"""
    message = update.callback_query
    message.answer()

    keyboard = [[InlineKeyboardButton("Start", callback_data=str(event_type))]]

    message.edit_message_text(
        text="Hey, I am here to help, these are the commands you can write - ",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return "START_ROUTES"


def event_list(update: Update, context: CallbackContext) -> int:
    """Event list for selected type"""
    message = update.callback_query
    selected_event_type = message.data
    message.answer()

    if "-" not in selected_event_type:
        counter = 0
    else:
        try:
            counter = int(selected_event_type.split("-")[1])
            counter = counter+1
        except ValueError:
            counter = 0
        selected_event_type = selected_event_type.split("-")[0]

    keyboard = [
        [],
        [],
        [
            InlineKeyboardButton("📄 Event Menu", callback_data="event_type"),
            InlineKeyboardButton("❌ Cancel", callback_data="end"),
        ]
    ]

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        event_group = jzon["events"][context.user_data["date"]][selected_event_type]

    try:
        first_event = (
            f'1️⃣ *{event_group[counter]["event_name"]}*\n\n'
            f'Description:  {event_group[counter]["event_desc"]}\n'
            f'Start Date:  {event_group[counter]["start_date"]}\n\n'
        )
        keyboard[0].append(InlineKeyboardButton("1️⃣", callback_data=f"details-{selected_event_type}-{counter}"))
    except IndexError:
        context.bot_data["message"] = message.message

        keyboard = [
            [InlineKeyboardButton("📅 Choose other date", callback_data="start")],
            [
                InlineKeyboardButton("📄 Event Menu", callback_data="event_type"),
                InlineKeyboardButton("❌ Cancel", callback_data="end"),
            ]
        ]

        message.edit_message_text(
            text="Sadly there are no events in this category for selected date 😔",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

        return "START_ROUTES"

    if counter+1 <= len(event_group)-1:
        second_event = (
            f'2️⃣ *{event_group[counter+1]["event_name"]}*\n\n'
            f'Description:  {event_group[counter+1]["event_desc"]}\n'
            f'Start Date:  {event_group[counter+1]["start_date"]}\n\n'
        )
        keyboard[0].append(InlineKeyboardButton("2️⃣", callback_data=f"details-{selected_event_type}-{counter+1}"))
    else:
        second_event = ""

    if counter+2 <= len(event_group)-1:
        third_event = (
            f'3️⃣ *{event_group[counter+2]["event_name"]}*\n\n'
            f'Description:  {event_group[counter+2]["event_desc"]}\n'
            f'Start Date:  {event_group[counter+2]["start_date"]}\n\n'
        )
        keyboard[0].append(InlineKeyboardButton("3️⃣", callback_data=f"details-{selected_event_type}-{counter+2}"))
    else:
        third_event = ""

    events_to_display = first_event + second_event + third_event
    events_array = [first_event, second_event, third_event]
    last_in_list = events_array.index(max(events_array))

    if counter != 0:
        keyboard[1].append(InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}-{counter-4}"))

    if counter+last_in_list != len(event_group)-1:
        keyboard[1].append(InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}-{counter+2}"))

    message.edit_message_text(
        text=(events_to_display),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return "END_ROUTES"


def event_details(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    selected_event_type = message.data.split("-")[1]
    counter = int(message.data.split("-")[2])
    message.answer()

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        selected_event = jzon["events"][context.user_data["date"]][selected_event_type][counter]
    
    event, location = prepare_event_details(selected_event)
    print(selected_event_type)

    keyboard = [
        [],
        [
            InlineKeyboardButton("Back", callback_data=f"{selected_event_type}"),
        ],
        [
            InlineKeyboardButton("📄 Event Menu", callback_data="event_type"),
            InlineKeyboardButton("❌ Cancel", callback_data="end"),
        ]
    ]

    if location:
        keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

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
    message.answer()
    message.edit_message_text(
        text="Cheers! I hope you will use our services again")
    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_markdown(
        text=f"We have the following commands in order - !",
        reply_markup=ReplyKeyboardRemove(),
    )

def search_by_name_start(update: Update, context: CallbackContext) -> None:
    """Search by name for user input"""
    update.message.bot.send_message(
        update.effective_user.id,
        text = "What are you looking for?"
    )
    return "SEARCH"

def get_searched_data(update: Update, context: CallbackContext) -> None:
    """Searching for close matches using user inputed name"""
    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        raw_events = jzon["events"]

    event_names = []
    for date_key, date_value in raw_events.items():
        for ctgry_name, ctgry_value in date_value.items():
            for event in ctgry_value:
                for key, value in event.items():
                    if key == "event_name" and value:
                        event_names.append(value)
                        continue

    result = difflib.get_close_matches(update.message.text, event_names)

    keyboard = [[]]

    if result:
        date_key, ctgry_name, event_to_find = find_event(result, raw_events)
        for event in raw_events[date_key][ctgry_name]:
            if event["event_name"] == event_to_find:
                event, location = prepare_event_details(event)
                break
        
        if location:
            keyboard[0].append(InlineKeyboardButton(text=f'📍 {location["name"]}', url=location["link"]))

        update.message.bot.send_message(
            update.effective_user.id,
            text=(event),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        update.message.bot.send_message(
            update.effective_user.id,
            text="Couldn't find such event",
            parse_mode=ParseMode.MARKDOWN,
        )

    return ConversationHandler.END
            

def find_event(result, raw_events):
    for value1 in result:
        for date_key, date_value in raw_events.items():
            for ctgry_name, ctgry_value in date_value.items():
                for event in ctgry_value:
                    for key, value in event.items():
                        if value == value1:
                            return date_key, ctgry_name, value
                        
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
    ADMIN_id = 1373382367
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
    ADMIN_id = 1373382367
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
                text=(f"Adver with id \"{advert_id}\" does not exist"),
        )
    advert_msg_id = advert.get("advert_msg_id")
    advert_owner = db.get_account_by_owner_id(advert.get("owner_id"))
    update.message.bot.send_message(
        advert_owner.get("telegram_user_id"), 
        text=(f"Your advert has been posted to our group. " 
              "\nYou're welcome!")
    )
    
    group_id = -1001535413676
    update.message.bot.copy_message(
        group_id,
        advert_owner.get("telegram_user_id"),
        advert_msg_id
    ) 
    
    db.delete_advert(advert.get("id"))

    return ConversationHandler.END

def event_list_manual_update(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user

    if db.get_account(user.id).get("is_staff"):
        sheet.get_sheet()
        logger.info(f"{user.first_name} updated event list manually. User ID: {user.id}")
    else:
        return

def event_list_updater(update: Update) -> None:
    sheet.get_sheet()
    return

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
                CallbackQueryHandler(start, pattern="^start$"),
                CallbackQueryHandler(event_type, pattern="^" + event_type_pattern + "$"),
                CallbackQueryHandler(help, pattern="^help$"),
                CallbackQueryHandler(event_list, pattern="^" + event_types + "$"),
                CallbackQueryHandler(end, pattern="^end$"),
            ],
            "END_ROUTES": [
                CallbackQueryHandler(event_list, pattern="^" + event_types_with_counter + "$"),
                CallbackQueryHandler(event_details, pattern="^details"),
                CallbackQueryHandler(start_over, pattern="^event_type$"),
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

    search_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search_by_name_start)],
        states={
            "SEARCH": [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex("^Done$")), get_searched_data, pass_chat_data= True
                ),
            ],
            "END_ROUTES": [
                CallbackQueryHandler(end, pattern="^end$"),
            ],
        },
        fallbacks=[MessageHandler(Filters.regex("^Done$"),start)],
        name="search",
    )

    # Add ConversationHandler to application that will be used for handling updates
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(push_handler)
    dispatcher.add_handler(search_handler)
    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("pushadvert", pushadvert))
    dispatcher.add_handler(CommandHandler("approve", approval))
    dispatcher.add_handler(CommandHandler("search", search_by_name_start))
    dispatcher.add_handler(CommandHandler("update", event_list_manual_update))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
