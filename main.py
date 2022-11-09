# TO-DO: copyright

import logging
import yaml

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

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)
# States
START_ROUTES, END_ROUTES = range(2)
# Callback data
event_type, help, Comedy, Culture, Food, Sports, Any = range(7)
# Define a few command handlers. These usually take the two arguments update and
# context.


def start(update: Update, context: CallbackContext) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logger.info(f"User {user.id} started the conversation.")

    keyboard = [
        [
            InlineKeyboardButton("Events", callback_data=str(event_type)),
            InlineKeyboardButton("Help", callback_data=str(help)),
        ]
    ]

    # Message for the inline keyboard
    update.message.reply_text(
        text="Feel free to choose an Event or press Help for the list of my commands!",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    # Tell ConversationHandler that we're in state `start` now
    return START_ROUTES


def start_over(update: Update, context: CallbackContext) -> int:
    """Prompt same text & keyboard as `event_type` does but not as new message"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Comedy", callback_data=str(Comedy)),
            InlineKeyboardButton("Culture", callback_data=str(Culture)),
        ],
        [
            InlineKeyboardButton("Food&Drinks", callback_data=str(Food)),
            InlineKeyboardButton("Sports", callback_data=str(Sports)),
        ],
        [InlineKeyboardButton("Any", callback_data=str(Any))]
    ]

    message.edit_message_text(
        text="Hope you will like something else, I am glad to offer you other options",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return START_ROUTES


def event_type(update: Update, context: CallbackContext) -> int:
    """Event type menu"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Comedy", callback_data=str(Comedy)),
            InlineKeyboardButton("Culture", callback_data=str(Culture)),
        ],
        [
            InlineKeyboardButton("Food&Drinks", callback_data=str(Food)),
            InlineKeyboardButton("Sports", callback_data=str(Sports)),
        ],
        [InlineKeyboardButton("Any", callback_data=str(Any))]
    ]

    message.edit_message_text(
        text="Here are the types of Events I can offer to you or you can choose Any if you are feeling adventurous",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return START_ROUTES


def help(update: Update, context: CallbackContext) -> int:
    """Help with return to start"""
    message = update.callback_query

    keyboard = [[InlineKeyboardButton("Start", callback_data=str(event_type))]]
    message.edit_message_text(
        text="Hey, I am here to help, these are the commands you can write - ",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    return START_ROUTES


def comedy(update: Update, context: CallbackContext) -> int:
    """Comedy option from types"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Event Menu", callback_data=str(event_type)),
            # Recursive to loop through options of Comedy
            InlineKeyboardButton("Next", callback_data=str(Comedy)),
        ],
        [InlineKeyboardButton("Cancel", callback_data=str(help))]
    ]

    message.edit_message_text(
        text = "JSON file subkey Comedy here", 
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    
    # End routes both require start and end of all actions, therefore 2 event_type actions needed
    return END_ROUTES


def culture(update: Update, context: CallbackContext) -> int:
    """Culture option from types"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Event Menu", callback_data=str(event_type)),
            # Recursive to loop through options of Culture
            InlineKeyboardButton("Next", callback_data=str(Culture))
        ],
        [InlineKeyboardButton("Cancel", callback_data=str(help))]
    ]

    message.edit_message_text(
        text="Markuss izvadi JSON te",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return END_ROUTES


def food(update: Update, context: CallbackContext) -> int:
    """Food&Drinks option from types"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Event Menu", callback_data=str(event_type)),
            # Recursive to loop through options of Food
            InlineKeyboardButton("Next", callback_data=str(Food))
        ],
        [InlineKeyboardButton("Cancel", callback_data=str(help))]
    ]

    message.edit_message_text(
        text="Markuss izvadi JSON te", 
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return END_ROUTES


def sports(update: Update, context: CallbackContext) -> int:
    """Sports option from types"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Event Menu", callback_data=str(event_type)),
            # Recursive to loop through options of Sports
            InlineKeyboardButton("Next", callback_data=str(Sports))
        ],
        [InlineKeyboardButton("Cancel", callback_data=str(help))]
    ]

    message.edit_message_text(
        text="Markuss izvadi JSON te", 
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return END_ROUTES    


def any(update: Update, context: CallbackContext) -> int:
    """Any option from types"""
    message = update.callback_query

    keyboard = [
        [
            InlineKeyboardButton("Event menu", callback_data=str(event_type)),
            # Recursive to loop through options of Any
            InlineKeyboardButton("Next", callback_data=str(Any)),
        ],
        [InlineKeyboardButton("Cancel", callback_data=str(help))]
    ]

    message.edit_message_text(
        text="Markuss izvadi JSON te", 
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return END_ROUTES
    

# Reading JSON file


def end(update: Update, context: CallbackContext) -> int:
    """
    Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    Made for the second optiion of completely setting off the bot by pressing cancel
    called at the end of every type of event
    """
    message = update.callback_query
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
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Setup conversation handler with the states START and END
    # Use the pattern parameter to pass CallbackQueries with specific
    # data pattern to the corresponding handlers.
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START_ROUTES: [
                CallbackQueryHandler(event_type, pattern="^" + str(event_type) + "$"),
                CallbackQueryHandler(help, pattern="^" + str(help) + "$"),
                CallbackQueryHandler(comedy, pattern="^" + str(Comedy) + "$"),
                CallbackQueryHandler(culture, pattern="^" + str(Culture) + "$"),
                CallbackQueryHandler(food, pattern="^" + str(Food) + "$"),
                CallbackQueryHandler(sports, pattern="^" + str(Sports) + "$"),
                CallbackQueryHandler(any, pattern="^" + str(Any) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(start_over, pattern="^" + str(event_type) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(help) + "$"),
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
