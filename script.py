import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton 
import textlines as TL
#import server
import threading
import sqlite3

TOKEN = "7623890164:AAGjbXji5sklmFccgwd3Z30xZRFNS0ZkDU4"

bot = telebot.TeleBot(TOKEN)

def init_db():
    conn = sqlite3.connect("phone_numbers.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phone_numbers (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            career_result TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_or_update_user(user_id, username=None, full_name=None, phone=None, career_result=None):
    conn = sqlite3.connect("phone_numbers.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO phone_numbers (user_id) VALUES (?)", (user_id,))
    fields = []
    values = []
    if username is not None:
        fields.append("username=?")
        values.append(username)
    if full_name is not None:
        fields.append("full_name=?")
        values.append(full_name)
    if phone is not None:
        fields.append("phone=?")
        values.append(phone)
    if career_result is not None:
        fields.append("career_result=?")
        values.append(career_result)
    if fields:
        values.append(user_id)
        cursor.execute(f"UPDATE phone_numbers SET {', '.join(fields)} WHERE user_id=?", values)
    conn.commit()
    conn.close()

menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
menu_keyboard.row(KeyboardButton("🏫 Колледж"))
menu_keyboard.row(KeyboardButton("🎓 Специальность"), KeyboardButton("🧭 Подбор специальности"))
menu_keyboard.row(KeyboardButton("📞 Контакты/Сайт"), KeyboardButton("📍 Адрес"))
menu_keyboard.row(KeyboardButton("❓ Часто задаваемые вопросы"), KeyboardButton("📝 Записаться"))

user_states = {}
user_data = {}
STATE_WAITING_NAME = "WAITING_NAME"
STATE_WAITING_PHONE = "WAITING_PHONE"

@bot.message_handler(commands=["start"])
def start_handler(message: Message):
    photo_path = "image/image1.jpg"  # Укажи путь к фото

    try:
        with open(photo_path, "rb") as photo:
            bot.send_photo(message.chat.id, photo, caption="👋 Доброго времени суток! Вас приветствует чатбот колледжа Международной Академии Бизнеса.")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "Ошибка: Фото не найдено!")

    bot.send_message(message.chat.id, "Какая информация вас интересует?", reply_markup=menu_keyboard)

# 🔹 Функция для запуска Flask в отдельном потоке
#def run_flask():
#    server.app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)


# Запускаем Flask в отдельном потоке
#threading.Thread(target=run_flask, daemon=True).start()

@bot.message_handler(func=lambda m: m.text in [
    "🏫 Колледж",
    "🎓 Специальность",
    "🧭 Подбор специальности",
    "📞 Контакты/Сайт",
    "📍 Адрес",
    "❓ Часто задаваемые вопросы",
    "📝 Записаться"
])
def menu_handler(message: Message):
    user_id = message.chat.id
    text = message.text

    if text == "🏫 Колледж":
        show_college_submenu(user_id)
    elif text == "🎓 Специальность":
        bot.send_message(user_id, TL.professions, parse_mode='Markdown')
    elif text == "🧭 Подбор специальности":
        start_career_test(user_id)
    elif text == "📞 Контакты/Сайт":
        bot.send_message(
            user_id,
            f"{TL.contact}\n\nСайт: https://cmab.edu.kz",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    elif text == "📍 Адрес":
        bot.send_message(
            user_id,
            "Улица Мустафы Озтюрка, 5а\nБостандыкский район, Алматы\n"
            "📍 [Открыть в картах](https://go.2gis.com/HfMFb)",
            parse_mode='Markdown'
        )
    elif text == "❓ Часто задаваемые вопросы":
        bot.send_message(user_id, TL.faq, parse_mode='Markdown')
    
    elif text == "📝 Записаться":
        user_states[user_id] = STATE_WAITING_NAME
        bot.send_message(
            user_id,
            "Чтобы записаться, введите, пожалуйста, *своё имя и фамилию*:",
            parse_mode="Markdown"
        )

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == STATE_WAITING_NAME)
def handle_full_name(message: Message):
    user_id = message.chat.id
    full_name = message.text.strip()
    if not full_name:
        bot.send_message(user_id, "Пожалуйста, введите корректное имя и фамилию.")
        return
    user_data[user_id] = {"full_name": full_name}
    user_states[user_id] = STATE_WAITING_PHONE
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Отправить номер", request_contact=True))
    bot.send_message(
        user_id,
        "Теперь отправьте свой *номер телефона* кнопкой ниже:",
        parse_mode="Markdown",
        reply_markup=kb
    )

@bot.message_handler(content_types=["contact"])
def handle_contact(message: Message):
    user_id = message.chat.id
    if user_states.get(user_id) == STATE_WAITING_PHONE and message.contact:
        phone_number = message.contact.phone_number
        full_name = user_data[user_id]["full_name"]
        info = bot.get_chat(user_id)
        username = info.username if info.username else "Не указан"
        save_or_update_user(user_id, username=username, full_name=full_name, phone=phone_number)
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)
        bot.send_message(
            user_id,
            "Спасибо! Вы *записаны*. Ваш номер и имя сохранены.\n"
            "Мы свяжемся с вами в ближайшее время 😎",
            parse_mode="Markdown",
            reply_markup=menu_keyboard
        )
    else:
        bot.send_message(user_id, "Номер телефона сейчас не требуется.", reply_markup=menu_keyboard)

def show_college_submenu(user_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(KeyboardButton("📅 О нас"))
    kb.row(KeyboardButton("👩‍🏫 Проведение занятий"))
    kb.row(KeyboardButton("🎉 Мероприятия"))
    kb.row(KeyboardButton("🔙 Назад"))
    bot.send_message(user_id, "Что хотите узнать о колледже?", reply_markup=kb)
        
@bot.message_handler(func=lambda m: m.text in [
    "📅 О нас", "👩‍🏫 Проведение занятий", "🎉 Мероприятия"
])
def college_submenu_handler(message: Message):
    text = message.text
    if text == "📅 О нас":
        bot.send_message(message.chat.id, TL.college_history)
    elif text == "👩‍🏫 Проведение занятий":
        photo_paths = [
            "image/class_work1.png",
            "image/class_work2.png",
            "image/class_work3.png",
            "image/class_work4.png",
            "image/class_work5.png"
        ]

        for path in photo_paths:
            try:
                with open(path, "rb") as photo:
                    bot.send_photo(message.chat.id, photo)
            except FileNotFoundError:
                bot.send_message(message.chat.id, f"Ошибка: {path} не найдено!")
        bot.send_message(message.chat.id, "наши занятия - выглядят так")

    elif text == "🎉 Мероприятия":
        # 1. Отправляем текст о мероприятии
        bot.send_message(message.chat.id, TL.college_activities)

        # 2. Отправляем фото
        photo_path = "image/event_photo.png"  # Укажи путь к фото
        try:
            with open(photo_path, "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption="Фото с мероприятия 📸")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Ошибка: Фото не найдено!")

        # 3. Отправляем видео
        video_path = "image/bisnesWomen.mp4"
        try:
            with open(video_path, "rb") as video:
                bot.send_video(message.chat.id, video, caption="Видео с мероприятия 🎥")
        except FileNotFoundError:
            bot.send_message(message.chat.id, "Ошибка: Видео не найдено!")
            
@bot.message_handler(func=lambda m: m.text == "🔙 Назад")
def back_handler(message: Message):
    bot.send_message(
        message.chat.id,
        "Вы вернулись в главное меню.",
        reply_markup=menu_keyboard
    )

user_answers = {}
active_users = set()

def start_career_test(user_id):
    active_users.add(user_id)
    user_answers[user_id] = []
    ask_career_question(user_id, 0)

def ask_career_question(user_id, index):
    if index < len(TL.career_questions):
        question, options = TL.career_questions[index]
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for opt in options:
            kb.add(KeyboardButton(opt))
        kb.row(KeyboardButton("❌ Выйти"))
        bot.send_message(user_id, f"🤔 {question}", reply_markup=kb)
    else:
        finish_career_test(user_id)

def finish_career_test(user_id):
    answers = user_answers.get(user_id, [])
    result = TL.career_results.get(tuple(answers), "Результат не найден")
    bot.send_message(
        user_id,
        f"Ваш результат профориентации:\n{result}",
        reply_markup=menu_keyboard
    )
    info = bot.get_chat(user_id)
    username = info.username if info.username else "Не указан"
    save_or_update_user(user_id, username=username, career_result=result)
    active_users.discard(user_id)
    user_answers.pop(user_id, None)

@bot.message_handler(func=lambda m: m.chat.id in active_users)
def career_answer_handler(message: Message):
    user_id = message.chat.id
    if message.text == "❌ Выйти":
        bot.send_message(user_id, "Вы вышли из теста.", reply_markup=menu_keyboard)
        active_users.discard(user_id)
        user_answers.pop(user_id, None)
        return
    user_answers[user_id].append(message.text)
    ask_career_question(user_id, len(user_answers[user_id]))

if __name__ == "__main__":
    bot.infinity_polling()
    print("чурка завелась")
