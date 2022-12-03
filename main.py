# TO-DO: copyright

import logging
import yaml
import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
    ParseMode,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Updater,
    ConversationHandler,
    MessageHandler,
    Filters,
)
from utils.sheets_to_json import save_event_list, extract_event_list
from utils.db_utils import DBManager


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
dbname = config["DB_NAME"]
user = config["DB_USER"]
password = config["DB_PASSWORD"]

db = DBManager(host, dbname, user, password)


def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    referal = context.args[0] if context.args else None
    logger.info(f"{user.first_name}, started the conversation. User ID: {user.id}")
    if db.get_account(user.id) is None:
        db.create_account(user, referal)

    keyboard = [
        [
            InlineKeyboardButton("Events", callback_data="event_type"),
        ]
    ]
    

    # Message for the inline keyboard
    update.message.reply_text(
        text="Feel free to choose an Event or press Help for the list of my commands!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=False
    )
    # Tell ConversationHandler that we're in state `start` now
    return "START_ROUTES"


def start_over(update: Update, context: CallbackContext) -> int:
    """Prompt same text & keyboard as `event_type` does but not as new message"""
    message = update.callback_query
    message.answer()

    keyboard = [
        [InlineKeyboardButton("🎸 Concerts/Parties 🎉", callback_data="Comedy")],
        [InlineKeyboardButton("⛩️ Culture 🗽", callback_data="Culture")],
        [InlineKeyboardButton("🧩 Workshop 🛍️", callback_data="Food")],
        [InlineKeyboardButton("🍱 Food/Drinks 🥂", callback_data="Food")],
        [InlineKeyboardButton("🎨 Art/Literature 📚", callback_data="Sports")],
        [InlineKeyboardButton("🎭 Theatre/Stand up 🎤", callback_data="Any")],
        [InlineKeyboardButton("Any ⁉️", callback_data="Any")],
    ]

    message.edit_message_text(
        text="Hope you will like something else, I am glad to offer you other options",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "START_ROUTES"


def event_type(update: Update, context: CallbackContext) -> int:
    """Event type menu"""
    message = update.callback_query
    message.answer()

    keyboard = [
        [InlineKeyboardButton("🎸 Concerts/Parties 🎉", callback_data="Comedy")],
        [InlineKeyboardButton("⛩️ Culture 🗽", callback_data="Culture")],
        [InlineKeyboardButton("🧩 Workshop 🛍️", callback_data="Food")],
        [InlineKeyboardButton("🍱 Food/Drinks 🥂", callback_data="Food")],
        [InlineKeyboardButton("🎨 Art/Literature 📚", callback_data="Sports")],
        [InlineKeyboardButton("🎭 Theatre/Stand up 🎤", callback_data="Any")],
        [InlineKeyboardButton("Any ⁉️", callback_data="Any")],
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

    if "|" not in selected_event_type:
        counter = 0
    else:
        counter = int(selected_event_type.split("|")[1])
        selected_event_type = selected_event_type.split("|")[0]
        counter = counter+1

    keyboard = [
        [],
        [],
        [
            InlineKeyboardButton("Event Menu", callback_data="event_type"),
            InlineKeyboardButton("Cancel", callback_data="end"),
        ]
    ]

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        event_group = jzon["events"][selected_event_type]

    first_event = (
        f'1️⃣ *{event_group[counter]["event_name"]}*\n\n'
        f'Description:  {event_group[counter]["event_desc"]}\n'
        f'Start Date:  {event_group[counter]["start_date"]}\n\n'
    )
    keyboard[0].append(InlineKeyboardButton("1️⃣", callback_data=f"details|{selected_event_type}|{counter}"))

    if counter+1 <= len(event_group)-1:
        second_event = (
            f'2️⃣ *{event_group[counter+1]["event_name"]}*\n\n'
            f'Description:  {event_group[counter+1]["event_desc"]}\n'
            f'Start Date:  {event_group[counter+1]["start_date"]}\n\n'
        )
        keyboard[0].append(InlineKeyboardButton("2️⃣", callback_data=f"details|{selected_event_type}|{counter+1}"))
    else:
        second_event = ""

    if counter+2 <= len(event_group)-1:
        third_event = (
            f'3️⃣ *{event_group[counter+2]["event_name"]}*\n\n'
            f'Description:  {event_group[counter+2]["event_desc"]}\n'
            f'Start Date:  {event_group[counter+2]["start_date"]}\n\n'
        )
        keyboard[0].append(InlineKeyboardButton("3️⃣", callback_data=f"details|{selected_event_type}|{counter+2}"))
    else:
        third_event = ""

    events_to_display = first_event + second_event + third_event
    events_array = [first_event, second_event, third_event]
    last_in_list = events_array.index(max(events_array))

    if counter != 0:
        keyboard[1].append(InlineKeyboardButton("⬅️", callback_data=f"{selected_event_type}|{counter-4}"))

    if counter+last_in_list != len(event_group)-1:
        keyboard[1].append(InlineKeyboardButton("➡️", callback_data=f"{selected_event_type}|{counter+2}"))

    message.edit_message_text(
        text=(events_to_display),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN,
    )

    return "END_ROUTES"


def event_details(update: Update, context: CallbackContext) -> int:
    message = update.callback_query
    selected_event_type = message.data.split("|")[1]
    counter = int(message.data.split("|")[2])
    message.answer()

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)
        selected_event = jzon["events"][selected_event_type][counter]
    

    keyboard = [
        [
            InlineKeyboardButton("Back", callback_data=f"{selected_event_type}"),
        ],
        [
            InlineKeyboardButton("Event Menu", callback_data="event_type"),
            InlineKeyboardButton("Cancel", callback_data="end"),
        ]
    ]

    message.edit_message_text(
        text=(
            f'[​​​​​​​​​​​]({selected_event["event_Image_URL"]})\n\n'
            f'*{selected_event["event_name"]}*\n\n'
            f'Description:  {selected_event["event_desc"]}\n'
            f'Start Date:  {selected_event["start_date"]}\n'
            f'End Date:  {selected_event["end_date"]}\n'
            f'Telegram: {selected_event["contact_telegram"]}\n'
            f'Phone: {selected_event["contact_number"]}\n'
        ),
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
              f" If it is not approved, you will be notified"),
        reply_markup= ReplyKeyboardRemove(),
    )
    ADMIN_id = 1699557868
    data = db.get_account(update.effective_chat.id)
    db.create_advert(update.message.message_id, data.get("id"))
    update.message.bot.forward_message(
        ADMIN_id,
        update.effective_chat.id,
        update.message.message_id
    )
    advert = (db.get_advert(data.get("id")))
    update.message.bot.send_message(ADMIN_id, advert.get ("owner_id"))
        
    return "PUSH_TO_GROUP"

def approval(update: Update, context: CallbackContext) -> int:
    ADMIN_id = 1699557868
    if update.effective_chat.id == ADMIN_id:
        update.message.reply_text(
                text=(f"Please write the id of the advert you're approving," 
                      f"which is stated under the advert you want to approve"),
                reply_markup= ReplyKeyboardRemove(),
        )
    else:
        update.message.reply_text(
                text=(f"There is no such command \U0001F972 " + 
                      f"Please use /help to see what I can offer you"),
                reply_markup= ReplyKeyboardRemove(),
        )
        
    return "PUSH_TO_GROUP"

def push_to_group(update: Update, context: CallbackContext) -> int:
    advert_owner_id = update.message.text
    advert = db.get_advert(advert_owner_id)
    advert_msg_id = advert.get("advert_msg_id")
    advert_owner = db.get_account_by_owner_id(advert_owner_id)

    update.message.bot.send_message(
        advert_owner.get("telegram_user_id"), 
        text=(f"Your advert has been posted to our group. " 
              f"You're welcome!")
    )
    
    group_id = -1001535413676
    update.message.bot.copy_message(
        group_id,
        advert_owner.get("telegram_user_id"),
        advert_msg_id
    ) 
    
    db.delete_advert(advert.get("id"))

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(config["TOKEN"])

    event_list_data = extract_event_list()
    save_event_list(event_list_data)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Setup conversation handler with the states START and END
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    event_types = "Comedy|Culture|Food|Sports|Any"
    event_types_with_counter = f"{event_types}|[0-9]+"

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "START_ROUTES": [
                CallbackQueryHandler(event_type, pattern="^event_type$"),
                CallbackQueryHandler(help, pattern="^help$"),
                CallbackQueryHandler(event_list, pattern="^" + event_types + "$"),
            ],
            "END_ROUTES": [
                CallbackQueryHandler(event_list, pattern="^" + event_types_with_counter + "$"),
                CallbackQueryHandler(event_details, pattern="^details"),
                # CallbackQueryHandler(view_photos, pattern="^view_photos"),
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


    # Add ConversationHandler to application that will be used for handling updates
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(push_handler)

    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("pushadvert", pushadvert))   
    dispatcher.add_handler(CommandHandler("approve", approval)) 
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
