import logging

from utils.db_connection import db
from utils.sheets_connection import sheet

from telegram import Update
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)


def restricted_access(func):
    def wrapper(update: Update, context: CallbackContext):
        user = update.effective_user
        if db.get_account(user.id).get("is_staff"):
            func(update, context)
    return wrapper


@restricted_access
def event_list_manual_update(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    sheet.get_sheets()
    update.message.reply_text(
        text="Event and Places lists updated successfully!",
    )
    logger.info(f"{user.first_name} updated lists manually. User ID: {user.id}")


def event_list_updater(update: Update) -> None:
    sheet.get_sheets()
    return


@restricted_access
def statistics(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    logger.info(f"{user.first_name} requested statistics. User ID: {user.id}")
    result_users = db.get_users()
    result_new_users = db.get_new_users()
    result_users_in_group = db.get_users_in_group()
    update.message.reply_text(
        text= f"Here are the statistics as of today:\nTotal users: {result_users.get('Count')}\nNew users: {result_new_users.get('Count')}\nUsers who started the bot and joined the group: {result_users_in_group.get('Count')}",
    )