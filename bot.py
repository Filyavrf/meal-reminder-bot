import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import time, datetime, timedelta
import pytz

# Настройки - токен берется из переменных окружения
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise ValueError("Не установлен токен бота! Добавьте переменную TOKEN в настройки Render")

TIMEZONE = pytz.timezone('Europe/Moscow')

# Время приёмов пищи
MEAL_TIMES = [
    time(8, 0, 0, tzinfo=TIMEZONE),  # Завтрак
    time(13, 0, 0, tzinfo=TIMEZONE),  # Обед
    time(19, 0, 0, tzinfo=TIMEZONE)  # Ужин
]

MEAL_NAMES = ["завтрак", "обед", "ужин"]
USER_CONFIRMATIONS = {}  # Хранит последние подтверждения

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()  # Важно для Render - выводит логи в консоль
    ]
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Привет, котик! Я буду напоминать тебе о приёмах пищи 🍽️\n'
        'Я также буду проверять, не пропустил(а) ли ты приём пищи 💕',
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
        "Ты сегодня просто супер! 🌟",
        "Вот это забота о здоровье! 💪",
        "Ты мой пример для подражания! 🌺"
    ]
    import random
    await update.message.reply_text(random.choice(responses))


async def meal_reminder(context: ContextTypes.DEFAULT_TYPE):
    meal_names = ["Завтрак", "Обед", "Ужин"]
    job = context.job
    meal_name = meal_names[job.data]

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    messages = [
        f"🍽️ Котик, пора кушать! ({meal_name})\nНе забудь позаботиться о себе 💕",
        f"🥣 Время {meal_name.lower()}а, мой хороший! Ты ведь не забыл(а) покушать?",
        f"💫 Котик, {meal_name} ждёт тебя! Ты важнее всех дел на свете 🌟",
        f"🍴 Напоминание о {meal_name.lower()}е! Ты заслуживаешь вкусной еды 💝"
    ]
    import random
    message = random.choice(messages)
    await context.bot.send_message(job.chat_id, text=message, reply_markup=reply_markup)


async def check_missed_meals(context: ContextTypes.DEFAULT_TYPE):
    """Проверяет пропущенные приёмы пищи"""
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
        user_id = context.job.chat_id
        last_confirmation = USER_CONFIRMATIONS.get(user_id)

        # Если не подтверждал сегодня или подтверждал до текущего приёма пищи
        if last_confirmation is None or last_confirmation.date() < current_time.date():
            meal_name = MEAL_NAMES[current_meal]
            messages = [
                f"😿 Котик, ты не подтвердил(а) {meal_name}... Всё в порядке?",
                f"💔 Я не вижу подтверждения {meal_name}а... Ты точно покушал(а)?",
                f"🕰️ Котик, время {meal_name}а прошло... Надеюсь, ты не забыл(а) о себе!",
                f"🌟 Напоминаю: важно не пропускать приёмы пищи! Как насчёт {meal_name}а?"
            ]
            import random
            message = random.choice(messages)
            await context.bot.send_message(user_id, text=message)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🍽️ Помощь по боту-напоминателю:

/start - Начать работу
/stats - Статистика приёмов пищи
/help - Эта справка

Бот напоминает о:
• Завтраке 🥞 - 8:00
• Обеде 🍲 - 13:00  
• Ужине 🍛 - 19:00

Нажимай "Поел(а)" после каждого приёма пищи!
    """
    await update.message.reply_text(help_text)


def main():
    # Проверяем, что токен установлен
    if not TOKEN:
        logging.error("Токен бота не установлен! Добавьте переменную TOKEN в настройки Render")
        return

    application = Application.builder().token(TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Text("Поел(а)"), handle_meal_confirmation))

    # Добавление заданий для напоминаний
    for i, meal_time in enumerate(MEAL_TIMES):
        application.job_queue.run_daily(
            meal_reminder,
            meal_time,
            days=(0, 1, 2, 3, 4, 5, 6),
            data=i,
            name=f"meal_reminder_{i}"
        )

    # Проверка пропущенных приёмов пищи каждый час
    application.job_queue.run_repeating(
        check_missed_meals,
        interval=3600,  # Каждый час
        first=10,
        name="missed_meals_check"
    )

    logging.info("Бот запущен и готов к работе!")
    application.run_polling()


if __name__ == '__main__':
    main()