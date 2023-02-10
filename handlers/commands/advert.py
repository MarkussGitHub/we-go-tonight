import logging

from telegram import Update
from telegram.ext import (
    CallbackContext, 
    CommandHandler, 
    ConversationHandler,
    Filters, 
    MessageHandler
)

from utils.db.connection import db
from handlers.wrappers import valid_user, ignore_old_messages
logger = logging.getLogger(__name__)

# @valid_user
@ignore_old_messages
def pushadvert(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"User {user.id} wrote pushadvert.")
    update.message.reply_text(
        text=(f"You started the pushadvert command, write an advertisment that can be posted in the group chat of WeGoTonight"),
    )
    return "PUSH"


def push(update: Update, context: CallbackContext) -> int:
    logger.info(f"User sent an advert. {update.effective_chat.id}")
    update.message.reply_text(
        text=(f"Sent for approval to the admin, if it is approved, it will be posted in the group."
              f"\nIf it is not approved, you will be notified"),
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
    
    group_id = -1001792279795
    update.message.bot.copy_message(
        group_id,
        advert_owner.get("telegram_user_id"),
        advert_msg_id
    )
    
    db.delete_advert(advert.get("id"))

    return ConversationHandler.END

def denial(update: Update, context: CallbackContext) -> int:
    ADMIN_id = 1373382367
    if update.effective_chat.id == ADMIN_id:
        update.message.reply_text(
                text=(f"Please write the id of the advert you're denying," 
                      f"\nwhich is stated under the advert you want to deny"),
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
