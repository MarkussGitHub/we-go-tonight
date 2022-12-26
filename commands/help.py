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
    user = {
            "id": update.effective_user.id
        }
    lang = db.get_account(user.get("id")).get("lang")
    
    keyboard = [
        [InlineKeyboardButton(_("Video Tutorial", lang)+ " 📷", callback_data="tutorial")],
        [InlineKeyboardButton(_("Cancel", lang), callback_data="end")]
    ]

    if context.chat_data["lang"] == "en":
        desc_text = (
            "Hey! This is our WeGoTonight Bot in Riga! 🤖\n\n"
            "I'll help you quickly and conveniently build memorable"
            " plans on a date of interest to you.\n\n"
            "What can your bot of leisure do?\n\n"
            "• 🗓️ Makes it possible to make the most fun and interesting plans for any taste!\n"
            "• 🗽 Displays what activities take place in different Riga institutions\n"
            "• 🧭 Shows you where your favorite place is and how to get there quickly\n"
            "• 💃 Inform you about the coolest parties of the week.\n\n"
            "Subscribe to our channel to learn about the upcoming events first! Ask questions,"
            " and share your impressions of favorite institutions in our community.\n\n"
            "To learn more about upcoming events, go to our Instagram page! Announcements,"
            " selections, and just beautiful places 📍 in Riga are waiting for your attention!"
        )
        
    elif context.chat_data["lang"] == "ru":
        desc_text = (
            "Привет! Это наш бот WeGoTonight! 🤖\n\n"
            "Я помогу тебе быстро и практично найти"
            " планы на день, то, что интересно тебе.\n\n"
            "Что может делать твой бот досуга?\n\n"
            "• 🗓️ Даёт возможность создания самых весёлых и интересных планов на любой вкус!\n"
            "• 🗽 Отображает, какие мероприятия проходят в различных заведениях Риги\n"
            "• 🧭 Покажет, где находится понравившееся заведение и как быстрей туда добраться\n"
            "• 💃 Проинформирует о самых крутых вечеринках недели.\n\n"
            "Подписывайся на наш канал, чтобы узнавать о предстоящих мероприятиях самым первым! Задавай вопросы,"
            " а так же делись впечатлениями о любимых заведениях в нашем community\n\n"
            "Чтобы узнать еще больше информации о предстоящих мероприятиях,  переходи на нашу Инстаграм страницу! Анонсы,"
            " подборки и просто красивые места 📍 Риги ждут твоего внимания!"
    )

    elif context.chat_data["lang"] == "lv":
        desc_text = (
            "Čau! Šis ir mūsu WeGoTonight bots Rīgā! 🤖\n\n"
            "Palīdzēšu tev ātri un parocīgi izvlēties"
            " plānus vakaram, datumā, kurš tev interesē.\n\n"
            "Ko es varu tev piedāvāt?\n\n"
            "• 🗓️ Nezino ko darīt? Atradīšu visinteresantākos notikumus jebkuram!!\n"
            "• 🗽 Parādīšu kādi pasākumi notiek dažādās Rīgas iestādēs.\n"
            "• 🧭 Parādīšu tev tavu jaunizvēlēto iestādi, kā arī kā līdz viņai nokļūt!\n"
            "• 💃 Atradīšu tev labākos nedēļas tusiņus.\n\n"
            "Paraksties uz mūsu kanālu, lai pirmais saņemtu ziņas! Uzdod jautājumus,"
            " un dalies pieredzē ar savām mīļākajām vietām mūsu lokā\n\n"
            "Lai uzzinātu par topošajiem pasākumiem, nāc pie mums uz arī uz Instagram! Paziņojumi,"
            " izlases un vienkārši skaistas 📍 Rīgas vietas gaida tevi!"
    )
    context.bot.send_photo(
        update.effective_user.id,
        "https://imgur.com/a/P87xKm7",
        caption = desc_text,
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    
    return "TUT"

def tutorial(update: Update, context: CallbackContext) -> None:
    user = {
            "id": update.effective_user.id
        }
    lang = db.get_account(user.get("id")).get("lang")
    
    keyboard = [
        [InlineKeyboardButton(_("Back", lang), callback_data="desc")],
        [InlineKeyboardButton(_("Cancel", lang), callback_data="end")]
    ]
    
    context.bot.send_video(
        update._effective_user.id,
        video = "https://i.imgur.com/yAfMpz9.mp4",
        reply_markup = InlineKeyboardMarkup(keyboard)
    )
    
    return "DESC"

def cancel(update: Update, context: CallbackContext) -> None:
    """
    Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    Made for the second optiion of completely setting off the bot by pressing cancel
    called at the end of every type of event
    """
    message = update.callback_query
    lang = context.chat_data["lang"]
    message.answer()
    context.bot.send_message(
        update.effective_chat.id,
        text=_("I hope you will use our services again", lang)
    )
    
    return ConversationHandler.END
    
    
help_handler = ConversationHandler(
    entry_points=[CommandHandler("help", help_command)],
    states={
        "DESC": [
            CallbackQueryHandler(description, pattern="^desc$"),
            CallbackQueryHandler(cancel, pattern="^end$")
        ],
        "TUT":[
            CallbackQueryHandler(tutorial, pattern="^tutorial$"),
            CallbackQueryHandler(cancel, pattern="^end$")
        ]
    },
    fallbacks=[CommandHandler("help", help_command)],
    name="help_handler",
)
