import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import pytz
from datetime import time, datetime
from flask import Flask
from threading import Thread

# Простой Flask сервер для health checks
app = Flask(__name__)


@app.route('/')
def health_check():
    return "Food Reminder Bot is running! 🍽️", 200


@app.route('/health')
def health():
    return "OK", 200


def run_flask():
    app.run(host='0.0.0.0', port=10000, debug=False)


# Запускаем Flask в отдельном потоке
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')

if not BOT_TOKEN:
    logging.error("BOT_TOKEN не установлен!")
    exit(1)

# Глобальный словарь для хранения chat_id пользователей
user_chats = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Сохраняем chat_id пользователя
    user_chats.add(chat_id)
    logging.info(f"Пользователь {user.first_name} (ID: {chat_id}) добавил бота")

    await update.message.reply_text(
        f"Привет, {user.first_name}! Я буду напоминать тебе о приемах пищи 🍽️\n"
        "Теперь ты будешь получать напоминания:\n"
        "🍳 Завтрак в 8:00 (Новосибирск, UTC+7)\n"
        "🍲 Обед в 13:00 (Новосибирск, UTC+7)\n"
        "🍽️ Ужин в 19:00 (Новосибирск, UTC+7)\n\n"
        "Не забудь нажимать кнопку 'Поела', когда поешь! 💖"
    )


async def test_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для отправки напоминания"""
    chat_id = update.effective_chat.id
    user_chats.add(chat_id)

    # Создаем инлайн-кнопку
    keyboard = [
        [InlineKeyboardButton("🍽️ Поела", callback_data="ate_test")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="🔧 **Тестовое напоминание!**\nКотик, пора покушать! 🍽️\nЭто тестовое сообщение для проверки бота.",
        reply_markup=reply_markup
    )


async def send_meal_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Отправка напоминания о приеме пищи всем пользователям"""
    job = context.job
    meal_type = job.data

    logging.info(f"Отправка напоминания: {meal_type}, пользователей: {len(user_chats)}")

    # Создаем инлайн-кнопку
    keyboard = [
        [InlineKeyboardButton("🍽️ Поела", callback_data=f"ate_{meal_type}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сообщения для разных приемов пищи
    messages = {
        "breakfast": "Доброе утро, котик! 🌅\nПора позавтракать 🍳\nНе забудь покушать, чтобы быть полной сил! 💪",
        "lunch": "Котик, уже обед! 🍲\nВремя подкрепиться и отдохнуть немного 😊",
        "dinner": "Вечер настал, котик! 🌙\nСамое время поужинать 🍽️\nПокушай хорошо перед сном! 💖"
    }

    message_text = messages.get(meal_type, "Котик, пора покушать! 🍽️")

    # Отправляем сообщение всем пользователям
    successful_sends = 0
    for chat_id in user_chats.copy():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=reply_markup
            )
            successful_sends += 1
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение {chat_id}: {e}")
            # Удаляем невалидный chat_id
            user_chats.discard(chat_id)

    logging.info(f"Успешно отправлено: {successful_sends} напоминаний")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на инлайн-кнопку"""
    query = update.callback_query
    await query.answer()

    meal_type = query.data.replace('ate_', '')

    # Сообщения подтверждения
    confirm_messages = {
        "breakfast": "Отлично, что ты позавтракала! 🍳\nТеперь у тебя есть силы на весь день! 💪",
        "lunch": "Супер, что ты пообедала! 🍲\nТеперь можно и отдохнуть немного 😊",
        "dinner": "Замечательно, что ты поужинала! 🍽️\nСпокойной ночи, котик! 🌙💖",
        "test": "✅ Тест прошел успешно! Бот работает корректно! 🎉"
    }

    confirmation = confirm_messages.get(meal_type, "Молодец, что покушала! 💖")

    # Редактируем сообщение, убирая кнопку
    await query.edit_message_text(
        text=f"{query.message.text}\n\n✅ {confirmation}",
        reply_markup=None
    )


def setup_reminders(application: Application):
    """Настройка расписания напоминаний"""
    # Часовой пояс Новосибирска (UTC+7)
    timezone = pytz.timezone('Asia/Novosibirsk')

    # Создаем время с учетом часового пояса
    breakfast_time = time(8, 0, 0)
    lunch_time = time(13, 0, 0)
    dinner_time = time(22, 12, 0)

    # Расписание напоминаний
    schedule = [
        ("breakfast", breakfast_time),
        ("lunch", lunch_time),
        ("dinner", dinner_time)
    ]

    for meal_type, reminder_time in schedule:
        # Применяем часовой пояс ко времени
        localized_time = timezone.localize(datetime.combine(datetime.today(), reminder_time)).timetz()

        application.job_queue.run_daily(
            send_meal_reminder,
            time=localized_time,
            days=(0, 1, 2, 3, 4, 5, 6),  # Все дни недели
            data=meal_type,
            name=f"meal_reminder_{meal_type}"
        )

    logging.info("Напоминания настроены")


def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("test", test_reminder))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Настраиваем расписание
    setup_reminders(application)

    # Логируем информацию о настройках
    logging.info("=== Информация о боте ===")
    logging.info(f"Токен: {'установлен' if BOT_TOKEN else 'не установлен'}")
    logging.info("Часовой пояс: Asia/Novosibirsk (UTC+7)")
    logging.info("Расписание: завтрак 8:00, обед 13:00, ужин 19:00")
    logging.info("Flask сервер запущен на порту 10000")
    logging.info("========================")

    # Запускаем бота
    logging.info("Бот запускается...")
    application.run_polling()
    logging.info("Бот остановлен")


if __name__ == '__main__':
    main()