import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Привет, котик! Я буду напоминать тебе о приёмах пищи по Новосибирскому времени 🍽️\n'
        'Нажимай кнопку "Поел(а)" после каждого приёма пищи! 💕',
        reply_markup=reply_markup
    )


async def handle_meal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(random.choice(responses))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(help_text)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logging.error(f'Ошибка: {context.error}')


def main():
    if not TOKEN:
        logging.error("Токен бота не установлен! Добавьте переменную TOKEN в настройки Render")
        return

    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Text("Поел(а)"), handle_meal_confirmation))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    logging.info("✅ Бот запущен и работает по Новосибирскому времени!")
    application.run_polling()


if __name__ == '__main__':
    main()