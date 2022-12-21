
from gettext import translation
# set current language

user_choice = "lv"

text = "When would you like to go?"

translations = {
    "ru": {
        "When would you like to go?": "Когда бы вы хотели пойти?",
    },
    "lv": {
        "When would you like to go?": "Kad jūs vēlaties doties?",
    }
}

print(translations.get(user_choice).get(text))
