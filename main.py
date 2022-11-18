# TO-DO: copyright

import logging
import yaml
import json

from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardRemove, 
    Update,
)
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler, 
    Updater,
)
from utils.sheets_to_json import save_event_list, extract_event_list

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info(f"User {user.id} started the conversation.")

    keyboard = [
        [
            InlineKeyboardButton("Events", callback_data="event_type"),
            InlineKeyboardButton("Help", callback_data="help"),
        ]
    ]

    # Message for the inline keyboard
    update.message.reply_text(
        text="Feel free to choose an Event or press Help for the list of my commands!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    # Tell ConversationHandler that we're in state `start` now
    return "START_ROUTES"


def start_over(update: Update, context: CallbackContext) -> int:
    """Prompt same text & keyboard as `event_type` does but not as new message"""
    message = update.callback_query
    message.answer()

    keyboard = [
        [
            InlineKeyboardButton("Comedy", callback_data="Comedy"),
            InlineKeyboardButton("Culture", callback_data="Culture"),
        ],
        [
            InlineKeyboardButton("Food&Drinks", callback_data="Food"),
            InlineKeyboardButton("Sports", callback_data="Sports"),
        ],
        [InlineKeyboardButton("Any", callback_data="Any")]
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
        [
            InlineKeyboardButton("Comedy", callback_data=f"Comedy"),
            InlineKeyboardButton("Culture", callback_data="Culture"),
        ],
        [
            InlineKeyboardButton("Food&Drinks", callback_data="Food"),
            InlineKeyboardButton("Sports", callback_data="Sports"),
        ],
        [InlineKeyboardButton("Any", callback_data="Any")]
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
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return "START_ROUTES"


def event_list(update: Update, context: CallbackContext) -> int:
    """Event list for selected type"""
    
    message = update.callback_query
    selected_event = message.data
    message.answer()
    if "|" not in selected_event:
        counter = 0
    else:
        counter = int(selected_event.split("|")[1])
        selected_event = selected_event.split("|")[0]
        counter = counter+1

    keyboard = [
        [
            InlineKeyboardButton("Next", callback_data=f"{selected_event}|{counter}"),
        ],
        [
            InlineKeyboardButton("Event Menu", callback_data="event_type"),
            InlineKeyboardButton("Cancel", callback_data="end"),
        ]
    ]
    if counter != 0:
        keyboard[0].insert(0, InlineKeyboardButton("Back", callback_data=f"{selected_event}"),)

    with open("data/event_list.json", "r") as f:
        jzon = json.load(f)

    try:
        message.edit_message_text(
            text = (
                f'{jzon["events"][selected_event][counter]["event_name"]}\n\n'
                f'Description:  {jzon["events"][selected_event][counter]["event_desc"]}\n'
                f'Start Date:  {jzon["events"][selected_event][counter]["start_date"]}\n'
                f'End Date:  {jzon["events"][selected_event][counter]["end_date"]}\n'
                f'Telegram:  {jzon["events"][selected_event][counter]["contact_telegram"]}\n'
                f'Phone:  {jzon["events"][selected_event][counter]["contact_number"]}\n'
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except IndexError:
        keyboard = [
            [InlineKeyboardButton("Back", callback_data=f"{selected_event}")],
            [
                InlineKeyboardButton("Event Menu", callback_data="event_type"),
                InlineKeyboardButton("Cancel", callback_data="end"),
            ]
        ]
        message.edit_message_text(
            text = "Sorry, there are no more events for this type",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    # End routes both require start and end of all actions, therefore 2 event_type actions needed
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
    message.edit_message_text(text="Cheers! I hope you will use our services again")
    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_markdown(
        text=fr"We have the following commands in order - !",
        reply_markup=ReplyKeyboardRemove(),
    )


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    with open("settings.local.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    updater = Updater(config["TOKEN"])

    event_list_data = extract_event_list()
    save_event_list(event_list_data)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Setup conversation handler with the states START and END
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    event_types = "Comedy|Culture|Food|Sports|Any"
    event_typs_with_counter = f"{event_types}|[0-9]+"
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            "START_ROUTES": [
                CallbackQueryHandler(event_type, pattern="^event_type$"),
                CallbackQueryHandler(help, pattern="^help$"),
                CallbackQueryHandler(event_list, pattern="^" + event_types + "$"),
            ],
            "END_ROUTES": [
                CallbackQueryHandler(event_list, pattern="^" + event_typs_with_counter + "$"),
                CallbackQueryHandler(start_over, pattern="^event_type$"),
                CallbackQueryHandler(end, pattern="^end$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    # Add ConversationHandler to application that will be used for handling updates
    dispatcher.add_handler(conv_handler)
    
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()



if __name__ == '__main__':
    main()
