
import json
import os
import logging

from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Загружаем токен из файла .env
load_dotenv("/home/TIshka/bot/.env")
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Проверь файл .env")

DATA_FILE = "user.json"

# Этапы заполнения профиля
NAME, AGE, COLOR, CITY, COUNTRY = range(5)

# Настройка журнала ошибок
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Загружаем сохранённые профили
def load_users():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return {}


# Сохраняем профили
def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=4)


users = load_users()


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот, который запоминает твой профиль.\n\n"
        "/setprofile — создать или изменить профиль\n"
        "/profile — посмотреть профиль\n"
        "/help — список команд"
    )


# Начинаем заполнение профиля
async def setprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как тебя зовут?")
    return NAME


# Проверка текста
def valid_text(text):
    return bool(text.strip()) and len(text.strip()) <= 100


# Получаем имя
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()

    if not valid_text(name) or len(name) > 50:
        await update.message.reply_text(
            "Введи имя длиной от 1 до 50 символов."
        )
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text("Сколько тебе лет?")
    return AGE


# Получаем возраст
async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(update.message.text.strip())

        if not 1 <= age <= 120:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "Введи возраст целым числом от 1 до 120."
        )
        return AGE

    context.user_data["age"] = age

    await update.message.reply_text("Какой твой любимый цвет?")
    return COLOR


# Получаем любимый цвет
async def get_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    color = update.message.text.strip()

    if not valid_text(color):
        await update.message.reply_text(
            "Введи корректное название цвета."
        )
        return COLOR

    context.user_data["color"] = color

    await update.message.reply_text("В каком городе ты живёшь?")
    return CITY


# Получаем город
async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()

    if not valid_text(city):
        await update.message.reply_text("Введи название города.")
        return CITY

    context.user_data["city"] = city

    await update.message.reply_text("В какой стране ты живёшь?")
    return COUNTRY


# Получаем страну и сохраняем профиль
async def get_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()

    if not valid_text(country):
        await update.message.reply_text("Введи название страны.")
        return COUNTRY

    user_id = str(update.effective_user.id)

    users[user_id] = {
        "name": context.user_data["name"],
        "age": context.user_data["age"],
        "favorite_color": context.user_data["color"],
        "city": context.user_data["city"],
        "country": country,
    }

    save_users(users)

    await update.message.reply_text(
        "Профиль успешно сохранён!\n\n"
        f"Имя: {users[user_id]['name']}\n"
        f"Возраст: {users[user_id]['age']}\n"
        f"Любимый цвет: {users[user_id]['favorite_color']}\n"
        f"Город: {users[user_id]['city']}\n"
        f"Страна: {users[user_id]['country']}\n\n"
        "Посмотреть профиль можно командой /profile."
    )

    context.user_data.clear()
    return ConversationHandler.END


# Команда /profile
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user = users.get(user_id)

    if user is None:
        await update.message.reply_text(
            "Профиль ещё не создан. Используй /setprofile."
        )
        return

    await update.message.reply_text(
        "Твой сохранённый профиль:\n\n"
        f"Имя: {user.get('name', 'Не указано')}\n"
        f"Возраст: {user.get('age', 'Не указан')}\n"
        f"Любимый цвет: {user.get('favorite_color', 'Не указан')}\n"
        f"Город: {user.get('city', 'Не указан')}\n"
        f"Страна: {user.get('country', 'Не указана')}"
    )


# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start — запуск бота\n"
        "/setprofile — заполнить или обновить профиль\n"
        "/profile — показать сохранённые данные\n"
        "/help — помощь\n"
        "/cancel — отменить заполнение профиля"
    )


# Отмена заполнения
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "Заполнение профиля отменено."
    )

    return ConversationHandler.END


# Запуск бота
def main():
    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("setprofile", setprofile)
        ],
        states={
            NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)
            ],
            AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)
            ],
            COLOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_color)
            ],
            CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)
            ],
            COUNTRY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_country)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation)
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("help", help_command))

    print("Бот запущен!")

    app.run_polling()


if __name__ == "__main__":
    main()
