import logging
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import time, datetime
import pytz
import random

# Настройки
TOKEN = os.environ.get('TOKEN')
TIMEZONE = pytz.timezone('Asia/Novosibirsk')

# Время приёмов пищи
MEAL_TIMES = [
    time(8, 0, 0),
    time(13, 0, 0),
    time(19, 0, 0)
]
MEAL_NAMES = ["завтрак", "обед", "ужин"]
USER_CONFIRMATIONS = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        'Привет, котик! Я буду напоминать тебе о приёмах пищи по Новосибирскому времени 🍽️',
        reply_markup=reply_markup
    )

    # Удаляем старые задачи
    for job in context.job_queue.jobs():
        job.schedule_removal()

    # Планируем напоминания
    for meal_time, meal_name in zip(MEAL_TIMES, MEAL_NAMES):
        context.job_queue.run_daily(
            meal_reminder,
            time=meal_time,
            days=(0, 1, 2, 3, 4, 5, 6),
            chat_id=chat_id,
            name=f"{user_id}-{meal_name}",
            data=meal_name
        )

    # Проверка пропущенных приёмов пищи
    context.job_queue.run_repeating(check_missed_meals, interval=3600, first=10, chat_id=chat_id, name=f"{user_id}-check")


async def handle_meal_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_CONFIRMATIONS[user_id] = datetime.now(TIMEZONE)

    responses = [
        f"Молодец, {update.effective_user.first_name}! Ты умничка 🥰",
        "Обожаю, когда ты заботишься о себе! 💖",
        "Так держать, мой хороший котик! 😻",
        "Ты сделал(а) мой день лучше! 🌈",
        "Как же я тобой горжусь! ✨",
    ]
    await update.message.reply_text(random.choice(responses))


async def meal_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    meal_name = job.data

    keyboard = [['Поел(а)']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    messages = [
        f"🍽️ Котик, пора кушать! ({meal_name}) 💕",
        f"🥣 Время {meal_name.lower()}а, мой хороший! Не забудь покушать!",
        f"💫 Котик, {meal_name} ждёт тебя! 🌟",
    ]
    await context.bot.send_message(chat_id=job.chat_id, text=random.choice(messages), reply_markup=reply_markup)


async def check_missed_meals(context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now(TIMEZONE)
    current_hour = current_time.hour
    current_meal = None

    if 7 <= current_hour < 11:
        current_meal = 0
    elif 12 <= current_hour < 15:
        current_meal = 1
    elif 18 <= current_hour < 21:
        current_meal = 2

    if current_meal is not None:
        user_id = context.job.name.split('-')[0]
        last_confirmation = USER_CONFIRMATIONS.get(int(user_id))
        if last_confirmation is None or last_confirmation.date() < current_time.date():
            meal_name = MEAL_NAMES[current_meal]
            messages = [
                f"😿 Котик, ты не подтвердил(а) {meal_name}... Всё в порядке?",
                f"💔 Я не вижу подтверждения {meal_name}а... Ты точно покушал(а)?",
                f"🌟 Напоминаю: важно не пропускать приёмы пищи! Как насчёт {meal_name}а?"
            ]
            await context.bot.send_message(chat_id=context.job.chat_id, text=random.choice(messages))


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        message = "📊 Я ещё не получал подтверждений. Надеюсь, ты кушаешь регулярно!"
    await update.message.reply_text(message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await update.message.reply_text(help_text)


def main():
    if not TOKEN:
        logging.error("❌ Токен бота не установлен! Добавьте переменную TOKEN в Render → Environment.")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Text("Поел(а)"), handle_meal_confirmation))

    logging.info("✅ Бот запущен и работает по Новосибирскому времени!")
    application.run_polling()


if __name__ == '__main__':
    main()
