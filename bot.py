import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters
from datetime import time, datetime
import pytz

# Настройки - Новосибирский часовой пояс
TOKEN = os.environ.get('TOKEN')
TIMEZONE = pytz.timezone('Asia/Novosibirsk')

# Время приёмов пищи (по Новосибирску)
MEAL_TIMES = [
    time(8, 0, 0, tzinfo=TIMEZONE),  # Завтрак в 8:00 Новосибирск
    time(13, 0, 0, tzinfo=TIMEZONE),  # Обед в 13:00 Новосибирск
    time(19, 0, 0, tzinfo=TIMEZONE)  # Ужин в 19:00 Новосибирск
]

MEAL_NAMES = ["завтрак", "обед", "ужин"]
USER_CONFIRMATIONS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def start(update: Update, context: CallbackContext):
    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(
        'Привет, котик! Я буду напоминать тебе о приёмах пищи по Новосибирскому времени 🍽️\n'
        'Нажимай кнопку "Поел(а)" после каждого приёма пищи! 💕',
        reply_markup=reply_markup
    )


def handle_meal_confirmation(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    USER_CONFIRMATIONS[user_id] = datetime.now(TIMEZONE)

    user = update.effective_user
    responses = [
        f"Молодец, {user.first_name}! Ты такой(ая) умничка 🥰",
        "Обожаю, когда ты заботишься о себе! 💖",
        "Так держать, мой хороший котик! 😻",
        "Ты сделал(а) мой день лучше! 🌈",
        "Как же я тобой горжусь! ✨",
    ]
    import random
    update.message.reply_text(random.choice(responses))


def help_command(update: Update, context: CallbackContext):
    help_text = """
🍽️ Помощь по боту-напоминателю:

/start - Начать работу
/help - Эта справка

Бот напоминает о (по Новосибирскому времени):
• Завтраке 🥞 - 8:00
• Обеде 🍲 - 13:00  
• Ужине 🍛 - 19:00

Нажимай "Поел(а)" после каждого приёма пищи!
    """
    update.message.reply_text(help_text)


def error_handler(update: Update, context: CallbackContext):
    """Обработчик ошибок"""
    logging.error(f'Ошибка: {context.error}')


def main():
    if not TOKEN:
        logging.error("Токен бота не установлен! Добавьте переменную TOKEN в настройки Render")
        return

    # Создаем Updater и передаем ему токен (use_context=True для версии 13.x)
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text("Поел(а)"), handle_meal_confirmation))

    # Обработчик ошибок
    dp.add_error_handler(error_handler)

    # Запускаем бота
    updater.start_polling()

    # Бот работает до прерывания
    logging.info("✅ Бот запущен и работает по Новосибирскому времени!")
    updater.idle()


if __name__ == '__main__':
    main()