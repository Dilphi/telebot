import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import textlines as TL
import sqlite3

TOKEN = "7623890164:AAGjbXji5sklmFccgwd3Z30xZRFNS0ZkDU4"

bot = telebot.TeleBot(TOKEN)

# Подключение к базе данных и создание таблицы, если её нет
def init_db():
    conn = sqlite3.connect("career_results.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS career_results (
                      user_id INTEGER PRIMARY KEY,
                      username TEXT,
                      profession TEXT,
                      phone TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Функция для сохранения результатов в базу данных
def save_result(user_id, username, profession, phone=None):
    conn = sqlite3.connect("career_results.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO career_results (user_id, username, profession, phone) VALUES (?, ?, ?, ?)",
                   (user_id, username if username else "Не указан", profession, phone))
    conn.commit()
    conn.close()

# Функция для сохранения номера телефона
def save_phone_number(user_id, phone_number):
    conn = sqlite3.connect("career_results.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT phone FROM career_results WHERE user_id = ?", (user_id,))
    existing_phone = cursor.fetchone()

    if existing_phone:
        cursor.execute("UPDATE career_results SET phone = ? WHERE user_id = ?", (phone_number, user_id))
    else:
        cursor.execute("INSERT INTO career_results (user_id, phone) VALUES (?, ?)", (user_id, phone_number))

    conn.commit()
    conn.close()

# Клавиатура главного меню
menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.row(KeyboardButton("📖 О колледже"))
menu_keyboard.row(KeyboardButton("🎓 Профессии"))
menu_keyboard.row(KeyboardButton("📍 Расположение"))
menu_keyboard.row(KeyboardButton("☎️ Контакты"))
menu_keyboard.row(KeyboardButton("🌐 Посетить Сайт"))
menu_keyboard.row(KeyboardButton("🧭 Профориентация"))
menu_keyboard.row(KeyboardButton("📞 Отправить свой номер", request_contact=True))

# Обработчик полученного номера телефона
@bot.message_handler(content_types=["contact"])
def phone_number_handler(message: Message):
    if message.contact:
        user_id = message.chat.id
        phone_number = message.contact.phone_number
        save_phone_number(user_id, phone_number)
        bot.send_message(user_id, "Спасибо! Ваш номер телефона сохранён.", reply_markup=menu_keyboard)

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
        bot.send_message(user_id, "Улица Мустафы Озтюрка, 5а\n Бостандыкский район, Алматы\n 📍 [Открыть в картах](https://go.2gis.com/HfMFb)", parse_mode='Markdown')
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
        
        keyboard.row(KeyboardButton("❌ Выйти из теста"))  # Добавлена кнопка выхода
        
        bot.send_message(user_id, question, reply_markup=keyboard)
    else:
        finish_career_test(user_id)

# Завершение теста с сохранением результатов
def finish_career_test(user_id: int):
    result = TL.career_results.get(tuple(user_answers.get(user_id, [])), "")
    bot.send_message(user_id, result, reply_markup=menu_keyboard)
    
    # Сохранение результата в БД
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "Не указан"
    save_result(user_id, username, result)
   
    # Очистка данных пользователя
    active_users.discard(user_id)
    user_answers.pop(user_id, None)

# Обработчик ответов на вопросы теста
@bot.message_handler(func=lambda message: message.chat.id in active_users)
def career_answer_handler(message: Message):
    user_id = message.chat.id
    text = message.text

    if text == "❌ Выйти из теста":
        exit_career_test(user_id)
        return

    if user_id not in user_answers:
        return

    user_answers[user_id].append(text)
    ask_career_question(user_id, len(user_answers[user_id]))

# Функция выхода из теста
def exit_career_test(user_id):
    bot.send_message(user_id, "Вы вышли из профориентационного теста.", reply_markup=menu_keyboard)
    
    # Очистка данных пользователя
    active_users.discard(user_id)
    user_answers.pop(user_id, None)

# Обработчик кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_handler(message: Message):
    user_id = message.chat.id
    bot.send_message(user_id, "Вы вернулись назад.", reply_markup=menu_keyboard)

# Запуск бота
if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()