import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import time

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

    await update.message.reply_text(
        f"Привет, {user.first_name}! Я буду напоминать тебе о приемах пищи 🍽️\n"
        "Теперь ты будешь получать напоминания:\n"
        "🍳 Завтрак в 8:00 (UTC+4)\n"
        "🍲 Обед в 13:00 (UTC+4)\n"
        "🍽️ Ужин в 19:00 (UTC+4)\n\n"
        "Не забудь нажимать кнопку 'Поела', когда поешь! 💖"
    )


async def send_meal_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Отправка напоминания о приеме пищи всем пользователям"""
    job = context.job
    meal_type = job.data

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
    for chat_id in user_chats.copy():  # Используем копию на случай изменений во время итерации
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=message_text,
                reply_markup=reply_markup
            )
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение {chat_id}: {e}")
            # Удаляем невалидный chat_id
            user_chats.discard(chat_id)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на инлайн-кнопку"""
    query = update.callback_query
    await query.answer()

    meal_type = query.data.replace('ate_', '')

    # Сообщения подтверждения
    confirm_messages = {
        "breakfast": "Отлично, что ты позавтракала! 🍳\nТеперь у тебя есть силы на весь день! 💪",
        "lunch": "Супер, что ты пообедала! 🍲\nТеперь можно и отдохнуть немного 😊",
        "dinner": "Замечательно, что ты поужинала! 🍽️\nСпокойной ночи, котик! 🌙💖"
    }

    confirmation = confirm_messages.get(meal_type, "Молодец, что покушала! 💖")

    # Редактируем сообщение, убирая кнопку
    await query.edit_message_text(
        text=f"{query.message.text}\n\n✅ {confirmation}",
        reply_markup=None
    )


def setup_reminders(application: Application):
    """Настройка расписания напоминаний"""
    # Часовой пояс UTC+4 (например, Самара)
    timezone = pytz.timezone('Europe/Samara')

    # Расписание напоминаний (время UTC+4)
    schedule = [
        ("breakfast", time(8, 0, 0, tzinfo=timezone)),  # Завтрак в 8:00
        ("lunch", time(13, 0, 0, tzinfo=timezone)),  # Обед в 13:00
        ("dinner", time(21, 31, 0, tzinfo=timezone))  # Ужин в 19:00
    ]

    for meal_type, reminder_time in schedule:
        application.job_queue.run_daily(
            send_meal_reminder,
            reminder_time,
            days=(0, 1, 2, 3, 4, 5, 6),  # Все дни недели
            data=meal_type,
            name=f"meal_reminder_{meal_type}"
        )


def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Настраиваем расписание
    setup_reminders(application)

    # Запускаем бота
    logging.info("Бот запускается...")
    application.run_polling()
    logging.info("Бот остановлен")


if __name__ == '__main__':
    main()