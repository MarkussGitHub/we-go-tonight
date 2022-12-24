import logging

from datetime import datetime

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

def statistics(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    
    if db.get_account(user.id).get("is_staff"):
        now = datetime.now()
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        logger.info(f"{user.first_name} called for statistics at {dt_string}. User ID: {user.id}")
        result_users = db.get_users()
        result_new_users = db.get_new_users()
        result_users_in_group = db.get_users_in_group()
        update.message.reply_text(
            text= f"Here are the statistics as of today:\nTotal users: {result_users.get('Count')}\nNew users: {result_new_users.get('Count')}\nUsers who started the bot and joined the group: {result_users_in_group.get('Count')}",
        )
        logger.info(f"{user.first_name} called statistics. User ID: {user.id}")
        
    else:
        return