import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import textlines as TL

TOKEN = "7623890164:AAGjbXji5sklmFccgwd3Z30xZRFNS0ZkDU4"

bot = telebot.TeleBot(TOKEN)

# Клавиатура
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.row(KeyboardButton("📖 О колледже"))
menu_keyboard.row(KeyboardButton("🎓 Профессии"))
menu_keyboard.row(KeyboardButton("📍 Расположение"))
menu_keyboard.row(KeyboardButton("☎️ Контакты"))
menu_keyboard.row(KeyboardButton("🌐 Посетить Сайт"))
menu_keyboard.row(KeyboardButton("🧭 Профориентация"))

# Словари для хранения данных пользователей
user_answers = {}
active_users = set()
user_current_menu = {}

# Команда /start
@bot.message_handler(commands=["start"])
def start_handler(message: Message):
    bot.send_message(message.chat.id, "Привет! Выберите интересующий вас раздел:", reply_markup=menu_keyboard)

# Обработчик кнопок главного меню
@bot.message_handler(func=lambda message: message.text in ["📖 О колледже", "🎓 Профессии", "📍 Расположение", "☎️ Контакты","🌐 Посетить Сайт", "🧭 Профориентация"])
def menu_handler(message: Message):
    user_id = message.chat.id
    text = message.text
    
    if text == "📖 О колледже":
        show_college_submenu(user_id)
    elif text == "🎓 Профессии":
        bot.send_message(user_id, TL.professions, parse_mode='Markdown')
    elif text == "📍 Расположение":
        bot.send_message(user_id, "Улица Мустафы Озтюрка, 5а\n Бостандыкский район, Алматы.\n 📍 [Открыть в картах](https://go.2gis.com/HfMFb)", parse_mode="Markdown", disable_web_page_preview=True)
    elif text == "☎️ Контакты":
        bot.send_message(user_id, TL.contact, parse_mode='Markdown', disable_web_page_preview=True)
    elif text == "🌐 Посетить Сайт":
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("🌐 Открыть сайт", web_app=WebAppInfo(url="https://cmab.edu.kz")))
        keyboard.row(KeyboardButton("🔙 Назад"))
        bot.send_message(user_id, "Нажмите кнопку ниже, чтобы открыть сайт:", reply_markup=keyboard)

    elif text == "🧭 Профориентация":
        start_career_test(user_id)

# Подменю для кнопки "О колледже"
def show_college_submenu(user_id):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(KeyboardButton("📅 Дата основания и история колледжа"))
    keyboard.row(KeyboardButton("👩‍🏫 Рабочие и специалисты по дисциплинам"))
    keyboard.row(KeyboardButton("🎉 Мероприятия и внеучебная активность"))
    keyboard.row(KeyboardButton("🤖 Активности на уроках и активное использование нейросетей"))
    keyboard.row(KeyboardButton("🔙 Назад"))
    
    bot.send_message(user_id, "Выберите, что вас интересует о колледже:", reply_markup=keyboard)
    user_current_menu[user_id] = 'college'

# Запуск профориентационного теста
def start_career_test(user_id):
    active_users.add(user_id)
    user_answers[user_id] = []
    ask_career_question(user_id, 0)
    

# Задание вопроса в тесте
def ask_career_question(user_id: int, index: int):
    if index < len(TL.career_questions):
        question, options = TL.career_questions[index]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        for option in options:
            keyboard.add(KeyboardButton(option))
        bot.send_message(user_id, question, reply_markup=keyboard)
    else:
        finish_career_test(user_id)

# Завершение теста
def finish_career_test(user_id: int):
    result = TL.career_results.get(tuple(user_answers.get(user_id, [])), "Не удалось определить профессию, попробуйте снова!")
    bot.send_message(user_id, result, reply_markup=menu_keyboard)
    
    # Убираем пользователя из активных
    active_users.discard(user_id)
    
    # Удаляем ответы и меню только если они существуют
    user_answers.pop(user_id, None)
    
    # Проверка наличия пользователя в меню перед удалением
    if user_id in user_current_menu:
        del user_current_menu[user_id]


# Обработчик ответов на вопросы теста
@bot.message_handler(func=lambda message: message.chat.id in active_users)
def career_answer_handler(message: Message):
    user_id = message.chat.id
    if user_id not in user_answers:
        return
    user_answers[user_id].append(message.text)
    ask_career_question(user_id, len(user_answers[user_id]))

# Обработчик кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_handler(message: Message):
    user_id = message.chat.id
    current_menu = user_current_menu.get(user_id)

    if current_menu == 'college':
        bot.send_message(user_id, "Выберите интересующий вас раздел:", reply_markup=menu_keyboard)
        del user_current_menu[user_id]
    else:
        bot.send_message(user_id, "Невозможно вернуться назад.", reply_markup=menu_keyboard)

# Обработчик кнопок из подменю "О колледже"
@bot.message_handler(func=lambda message: message.text in ["📅 Дата основания и история колледжа", "👩‍🏫 Рабочие и специалисты по дисциплинам", "🎉 Мероприятия и внеучебная активность", "🤖 Активности на уроках и активное использование нейросетей"])
def college_submenu_handler(message: Message):
    user_id = message.chat.id
    text = message.text
    responses = {
        "📅 Дата основания и история колледжа": TL.college_history,
        "👩‍🏫 Рабочие и специалисты по дисциплинам": TL.college_specialists,
        "🎉 Мероприятия и внеучебная активность": TL.college_activities,
        "🤖 Активности на уроках и активное использование нейросетей": TL.college_tech_activities,
    }
    bot.send_message(user_id, responses.get(text, "Информация недоступна."))

if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
