import logging

from utils.db_connection import db
from utils.sheets_connection import sheet

from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)


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