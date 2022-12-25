import logging

from telegram import (
    Update,
    InlineKeyboardButton, 
    InlineKeyboardMarkup
    )
from telegram.ext import (
    CallbackContext, 
    CallbackQueryHandler,
    CommandHandler, 
    ConversationHandler
)

from utils.translations import translate as _
from utils.db_connection import db

logger = logging.getLogger(__name__)


def help_command(update: Update, context: CallbackContext) -> None:
    
    if update.effective_chat:
        user = {
            "id": update.effective_user.id
        }
        lang = db.get_account(user.get("id")).get("lang")
        
        if db.get_account(user.get("id")).get("lang") is None:
            db.update_selected_lang(user.get("id"), lang)
        
        keyboard = [
                [InlineKeyboardButton(_("Description", lang), callback_data="desc")]
        ]
        
        group_id = -1001617590404
        checker = context.bot.getChatMember(group_id, update.effective_chat.id)
        if checker["status"] == "left":
            context.bot.send_message(
                update.effective_chat.id,
                text = "Please join our telegram group to use the bot, we offer a lot there as well!\nhttps://t.me/wegotonightinriga"
            )
            return

        else:
            db.update_joined_group(update.effective_chat.id, True)

        if not context.chat_data.get("lang"):
            acc = db.get_account(update.effective_chat.id)
            context.chat_data["lang"] = acc.get("lang", "en") if acc is not None else "en"

        if context.chat_data["lang"] == "en":
            help_text = ("⚙️ The Command /settings\n"
                        "will help you to choose the navigation language.\n\n"
                        "❓ The Command /help\n"
                        "will display this instruction once again, as well as a short video on all bot functions.\n\n"
                        "🗒 The Command /events\n"
                        "will navigate you through upcoming or ongoing events, just choose a time period, event type and click an event you like.\n\n"
                        "🔎 The Command /search\n"
                        "will help you find places by their names.\n\n"
                        "The button with 📍 emoji will guide you the location of the chosen event."
            )
        
        elif context.chat_data["lang"] == "ru":
            help_text = ("⚙️ Команда /settings\n"
                        "поможет выбрать удобный язык интерфейса твоего бота.\n\n"
                        "❓ Команда /help\n"
                        "покажет тебе эту инструкцию еще раз, а также короткое видео о работе всех команд.\n\n"
                        "🗒 Команда /events\n"
                        "загрузит события в интересующий тебя период времени, просто выбери дату, тип события и понравившейся эвент.\n\n"
                        "🔎 Команда /search\n"
                        "поможет найти места или события по названию.\n\n"
                        "Кнопка со значком 📍 покажет местонахождения выбранного места."
            )

        elif context.chat_data["lang"] == "lv":
            help_text = ("⚙️ Komanda /settings\n"
                        "palīdzēs Jums izvēlēties ērtu saskarnes valodu jūsu botam.\n\n"
                        "❓ Komanda /help\n"
                        "vēlreiz parādīs šo instrukciju, kā arī īsu video par visu bota funkcionalitāti.\n\n"
                        "🗒 Komanda /events\n"
                        "ielādēs notikumus Jūs interesējošajā laika periodā, vienkārši atlasiet datumu, notikuma veidu un notikumu, kurš jums patīk.\n\n"
                        "🔎 Komanda /search\n"
                        "palīdzēs atrast vietas vai notikumus pēc nosaukuma.\n\n"
                        "Poga ar zīmi 📍 parādīs izvēlētā notikuma atrašanās vietu."
            )

        update.message.reply_text(
            text = help_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return "DESC"

def description(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        update.effective_user.id,
        text = ("Hey! This is our WeGoTonight Bot in Riga!.\n"
        "I'll help you quickly and conveniently build memorable"
        " plans on a date of interest to you."
        "\nWhat can your bot of leisure do?\n"
        "• Makes it possible to make the most fun and interesting plans for any taste!\n"
        "• Displays what activities take place in different Riga institutions\n"
        "• Shows you where your favorite place is and how to get there quickly\n"
        "• Inform you about the coolest parties of the week.\n"
        "Subscribe to our channel to learn about the upcoming events first! Ask questions,"
        " and share your impressions of favorite institutions in our community\n"
        "To learn more about upcoming events, go to our Instagram page! Announcements,"
        " collections, and just beautiful places in Riga are waiting for your attention!") 
    )

help_handler = ConversationHandler(
    entry_points=[CommandHandler("start", help)],
    states={
        "DESC": [
            CallbackQueryHandler(description, pattern="^desc$|^lv$|^en$|^ru$"),
        ],
    },
    fallbacks=[CommandHandler("start", help)],
    name="help_handler",
)
