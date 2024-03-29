import logging
from datetime import time

import pytz
import yaml
from telegram.ext import CommandHandler, Updater

from handlers.commands.admin import event_list_manual_update, event_list_updater, statistics
from handlers.commands.advert import denial_handler, push_handler
from handlers.commands.start import conv_handler
from handlers.commands.search import search_handler
from handlers.commands.settings import settings_handler
from handlers.commands.help import help_handler, help_command
from utils.sheets.connection import sheet

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    with open("settings.local.yaml", "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    updater = Updater(config["TOKEN"])
    sheet.get_sheets()

    updater.job_queue.run_daily(event_list_updater,
                                time(hour=4, minute=00, tzinfo=pytz.timezone('Europe/Riga')),
                                days=(0, 1, 2, 3, 4, 5, 6), name="sheet", context=None)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add ConversationHandler to application that will be used for handling updates
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(push_handler)
    dispatcher.add_handler(search_handler)
    dispatcher.add_handler(denial_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_handler)

    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("stats", statistics))
    dispatcher.add_handler(CommandHandler("update", event_list_manual_update))
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
