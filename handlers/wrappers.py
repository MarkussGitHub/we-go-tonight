from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext
from utils.db_connection import db


def ignore_old_messages(func):
    def wrapper(update: Update, context: CallbackContext):
        message_date = update.message.date if update.message else update.callback_query.message.date
        message_date = message_date.strftime("%Y-%m-%d %H:%M:%S")
        current_date = datetime.utcnow()-timedelta(minutes=1)
        current_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        if message_date >= current_date:
            return func(update, context)
    return wrapper


def valid_user(func):
    def wrapper(update: Update, context: CallbackContext):
        group_id = -1001617590404
        checker = context.bot.getChatMember(group_id, update.effective_chat.id)
        user = update.effective_chat

        if not db.get_account(user.id):
            referal = context.args[0] if context.args else None
            db.create_account(user, referal)

        if checker["status"] == "left":
            context.bot.send_message(
                update.effective_chat.id,
                text = "Please join our telegram group to use the bot, we offer a lot there as well!\nhttps://t.me/wegotonightinriga"
            )
            return
        
        elif not db.get_account(user["id"])["joined_group"]:
            db.update_joined_group(update.effective_chat.id, True)

        return func(update, context)
    return wrapper
