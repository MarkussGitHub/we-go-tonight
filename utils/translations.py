translations = {
    "ru": {
        "When would you like to go?": "Когда бы Вы хотели пойти?",
        "Today": "Сегодня",
        "This week": "На этой неделе",
        "This month": "В этом месяце",
        "Here are the types of Events I can offer to you": "Вот какие категории могу вам предложить",
        "Concerts/Parties": "Концерты/Праздники",
        "Culture": "Культура",
        "Workshop": "Мастерская",
        "Food/Drinks": "Еда/Напитки",
        "Art/Literature": "Исскуство/Литература",
        "Theatre/Stand up": "Театр/Стенд Ап",
        "Event Menu": "Меню событий",
        "Cancel": "Отмена",
        "Sadly there are no events in this category for selected date": "К сожалению нет событий по этой категории в выбраной дате",
        "Choose other date": "Выбрать другую дату",
        "Back": "Назад",
        "I hope you will use our services again": "Надеюсь увидеть Вас снова",
        "What event or place are you looking for?": "Какое мероприятие или место Вы ищете?",
        "Here are events that i could find": "Вот события, которые я смог найти",
        "Please select your preferred language": "Пожалуйста, выберите предпочитаемый язык",
        "Description": "Описание",
        "Video Tutorial": "Видео обучение"
    },
    "lv": {
        "When would you like to go?": "Kad jūs vēlaties doties?",
        "Today": "Šodien",
        "This week": "Šonedēļ",
        "This month": "Šomēness",
        "Here are the types of Events I can offer to you": "Šīs ir kategorijas, kuras varu tev piedāvāt",
        "Concerts/Parties": "Koncerti/Ballītes",
        "Culture": "Kultūra",
        "Workshop": "Darbnīca",
        "Food/Drinks": "Ēdieni/Dzērieni",
        "Art/Literature": "Māksla/Literatūra",
        "Theatre/Stand up": "Teātris/Stand Up",
        "Event Menu": "Pasākumu izvēlne",
        "Cancel": "Atcelt",
        "Sadly there are no events in this category for selected date": "Diemžēl nav notikumu šajā kategorijā, izvēlētajos datumos",
        "Choose other date": "Izvēlēties citu datumu",
        "Back": "Atpakaļ",
        "I hope you will use our services again": "Gaidīšu jūs atpakaļ",
        "What event or place are you looking for?": "Kādu pasākumu vai vietu jūs meklējat?",
        "Here are events that i could find": "Šeit ir notikumi, kurus es varēju atrast",
        "Please select your preferred language": "Lūdzu, izvēlietes vēlamo valodu",
        "Description": "Apraksts",
        "Video Tutorial": "Video pamācība"
    }
}

def translate(text, lang):
    return text if lang == "en" else translations.get(lang, {}).get(text, "")
