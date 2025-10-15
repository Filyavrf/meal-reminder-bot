import os
import logging
from datetime import time

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Токен бота (будет установлен в переменных окружения)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Словарь для хранения статусов пользователей
user_status = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, любимая! Я буду напоминать тебе о приемах пищи 🍽️\n"
        "Теперь ты будешь получать напоминания:\n"
        "🍳 Завтрак в 8:00\n"
        "🍲 Обед в 13:00\n"
        "🍽️ Ужин в 19:00\n\n"
        "Не забудь нажимать кнопку 'Поела', когда поешь! 💖"
    )


async def send_reminder(context: ContextTypes.DEFAULT_TYPE, meal_type: str, meal_name: str):
    """Отправка напоминания о приеме пищи"""
    job = context.job

    # Создаем клавиатуру с кнопкой
    keyboard = [
        [InlineKeyboardButton("🍽️ Поела", callback_data=f"ate_{meal_type}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Текст напоминания
    messages = {
        "breakfast": "Доброе утро, котик! 🌅\nПора позавтракать 🍳\nНе забудь покушать, чтобы быть полной сил! 💪",
        "lunch": "Котик, уже обед! 🍲\nВремя подкрепиться и отдохнуть немного 😊",
        "dinner": "Вечер настал, котик! 🌙\nСамое время поужинать 🍽️\nПокушай хорошо перед сном! 💖"
    }

    message = messages.get(meal_type, "Котик, пора покушать! 🍽️")

    # Отправляем сообщение
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=message,
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    meal_type = query.data.replace('ate_', '')

    # Сообщения подтверждения
    confirm_messages = {
        "breakfast": "Отлично, что ты позавтракала! 🍳\nТеперь у тебя есть силы на весь день! 💪",
        "lunch": "Супер, что ты пообедала! 🍲\nТеперь можно и отдохнуть немного 😊",
        "dinner": "Замечательно, что ты поужинала! 🍽️\nСпокойной ночи, котик! 🌙💖"
    }

    confirmation = confirm_messages.get(meal_type, "Молодец, что покушала! 💖")

    # Обновляем сообщение
    await query.edit_message_text(
        text=f"{query.message.text}\n\n✅ {confirmation}",
        reply_markup=None
    )


async def setup_reminders(application: Application, chat_id: int):
    """Настройка напоминаний для пользователя"""
    timezone = pytz.timezone('Europe/Moscow')  # Установите нужный часовой пояс

    # Расписание напоминаний
    reminders = [
        ("breakfast", "завтрак", "8:00"),
        ("lunch", "обед", "13:00"),
        ("dinner", "ужин", "21:15")
    ]

    for meal_type, meal_name, time_str in reminders:
        hour, minute = map(int, time_str.split(':'))

        application.job_queue.run_daily(
            send_reminder,
            time=time(hour, minute, 0, tzinfo=timezone),
            days=(0, 1, 2, 3, 4, 5, 6),
            chat_id=chat_id,
            name=f"{meal_type}_{chat_id}",
            data=meal_type
        )


def main():
    """Основная функция"""
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()