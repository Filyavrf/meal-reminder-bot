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
        'Я также буду проверять, не пропустил(а) ли ты приём пищи 💕',
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


def meal_reminder(context: CallbackContext):
    job = context.job
    meal_name = job.context['meal_name']
    chat_id = job.context['chat_id']

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    messages = [
        f"🍽️ Котик, пора кушать! ({meal_name})\nНе забудь позаботиться о себе 💕",
        f"🥣 Время {meal_name.lower()}а, мой хороший! Ты ведь не забыл(а) покушать?",
        f"💫 Котик, {meal_name} ждёт тебя! Ты важнее всех дел на свете 🌟",
    ]
    import random
    message = random.choice(messages)
    context.bot.send_message(chat_id, text=message, reply_markup=reply_markup)


def check_missed_meals(context: CallbackContext):
    """Проверяет пропущенные приёмы пищи по Новосибирскому времени"""
    current_time = datetime.now(TIMEZONE)
    current_hour = current_time.hour

    # Определяем, какой приём пищи должен быть сейчас
    current_meal = None
    if 7 <= current_hour < 11:  # Завтрак
        current_meal = 0
    elif 12 <= current_hour < 15:  # Обед
        current_meal = 1
    elif 18 <= current_hour < 21:  # Ужин
        current_meal = 2

    if current_meal is not None:
        user_id = context.job.context['user_id']
        last_confirmation = USER_CONFIRMATIONS.get(user_id)

        if last_confirmation is None or last_confirmation.date() < current_time.date():
            meal_name = MEAL_NAMES[current_meal]
            messages = [
                f"😿 Котик, ты не подтвердил(а) {meal_name}... Всё в порядке?",
                f"💔 Я не вижу подтверждения {meal_name}а... Ты точно покушал(а)?",
                f"🌟 Напоминаю: важно не пропускать приёмы пищи! Как насчёт {meal_name}а?"
            ]
            import random
            message = random.choice(messages)
            context.bot.send_message(user_id, text=message)


def stats_command(update: Update, context: CallbackContext):
    """Показывает статистику подтверждений"""
    user_id = update.effective_user.id
    last_confirmation = USER_CONFIRMATIONS.get(user_id)

    if last_confirmation:
        time_diff = datetime.now(TIMEZONE) - last_confirmation
        hours = int(time_diff.total_seconds() / 3600)

        if hours < 1:
            message = "🎉 Ты сегодня молодец! Все приёмы пищи подтверждены вовремя!"
        elif hours < 4:
            message = f"⏰ Прошло {hours} часа с последнего подтверждения. Так держать!"
        else:
            message = f"💝 Котик, давно не было подтверждений... Всё хорошо?"
    else:
        message = "📊 Я ещё не получал подтверждений от тебя. Надеюсь, ты кушаешь регулярно!"

    update.message.reply_text(message)


def help_command(update: Update, context: CallbackContext):
    help_text = """
🍽️ Помощь по боту-напоминателю:

/start - Начать работу
/stats - Статистика приёмов пищи
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

    # Создаем Updater и передаем ему токен
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("stats", stats_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(MessageHandler(Filters.text("Поел(а)"), handle_meal_confirmation))

    # Обработчик ошибок
    dp.add_error_handler(error_handler)

    # Получаем job_queue для планирования задач
    jq = updater.job_queue

    # Запускаем бота
    updater.start_polling()

    # Бот работает до прерывания
    logging.info("Бот запущен и работает по Новосибирскому времени!")
    updater.idle()


if __name__ == '__main__':
    main()