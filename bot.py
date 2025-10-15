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
USER_JOBS = {}  # Храним задания для каждого пользователя

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Останавливаем старые задания для этого пользователя, если они есть
    if user_id in USER_JOBS:
        for job in USER_JOBS[user_id]:
            job.schedule_removal()

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        'Привет, котик! Я буду напоминать тебе о приёмах пищи по Новосибирскому времени 🍽️\n'
        'Я также буду проверять, не пропустил(а) ли ты приём пищи 💕',
        reply_markup=reply_markup
    )

    # Создаем новые задания для этого пользователя
    user_jobs = []

    # Добавляем задания для приёмов пищи
    for i, meal_time in enumerate(MEAL_TIMES):
        job = context.application.job_queue.run_daily(
            meal_reminder,
            meal_time,
            days=tuple(range(7)),
            data={'meal_name': MEAL_NAMES[i].capitalize(), 'chat_id': chat_id, 'user_id': user_id},
            name=f"meal_reminder_{user_id}_{i}"
        )
        user_jobs.append(job)

    # Проверка пропущенных приёмов пищи каждый час
    job = context.application.job_queue.run_repeating(
        check_missed_meals,
        interval=3600,
        first=10,
        data={'user_id': user_id, 'chat_id': chat_id},
        name=f"missed_meals_check_{user_id}"
    )
    user_jobs.append(job)

    # Сохраняем задания для пользователя
    USER_JOBS[user_id] = user_jobs

    await update.message.reply_text("✅ Напоминания настроены! Буду напоминать о приёмах пищи 🍽️")


async def handle_meal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_CONFIRMATIONS[user_id] = datetime.now(TIMEZONE)

    user = update.effective_user
    responses = [
        f"Молодец, {user.first_name}! Ты такой(ая) умничка 🥰",
        "Обожаю, когда ты заботиться о себе! 💖",
        "Так держать, мой хороший котик! 😻",
        "Ты сделал(а) мой день лучше! 🌈",
        "Как же я тобой горжусь! ✨",
    ]
    import random
    await update.message.reply_text(random.choice(responses))


async def meal_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    meal_name = job.data['meal_name']
    chat_id = job.data['chat_id']

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    messages = [
        f"🍽️ Котик, пора кушать! ({meal_name})\nНе забудь позаботиться о себе 💕",
        f"🥣 Время {meal_name.lower()}а, мой хороший! Ты ведь не забыл(а) покушать?",
        f"💫 Котик, {meal_name} ждёт тебя! Ты важнее всех дел на свете 🌟",
    ]
    import random
    message = random.choice(messages)
    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


async def check_missed_meals(context: ContextTypes.DEFAULT_TYPE):
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
        user_id = context.job.data['user_id']
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
            await context.bot.send_message(chat_id=context.job.data['chat_id'], text=message)


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

/start - Начать работу (настройка напоминаний)
/stats - Статистика приёмов пищи
/help - Эта справка

Бот напоминает о (по Новосибирскому времени):
• Завтраке 🥞 - 8:00
• Обеде 🍲 - 13:00  
• Ужине 🍛 - 19:00

Нажимай "Поел(а)" после каждого приёма пищи!
    """
    await update.message.reply_text(help_text)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Останавливает напоминания для пользователя"""
    user_id = update.effective_user.id

    if user_id in USER_JOBS:
        for job in USER_JOBS[user_id]:
            job.schedule_removal()
        del USER_JOBS[user_id]
        await update.message.reply_text("⏸️ Напоминания остановлены! Используй /start чтобы возобновить.")
    else:
        await update.message.reply_text("ℹ️ У тебя нет активных напоминаний.")


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
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(MessageHandler(filters.Text("Поел(а)"), handle_meal_confirmation))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    logging.info("✅ Бот запущен и работает по Новосибирскому времени!")
    application.run_polling()


if __name__ == '__main__':
    main()