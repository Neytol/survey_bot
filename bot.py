import json
import os
from json import JSONDecodeError
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import Application, ContextTypes, CommandHandler, ConversationHandler, MessageHandler, filters
import logging
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level= logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


NAME, AGE, CITY = range(3)

USERS_FILE = 'users.json'

def load_user():
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except JSONDecodeError:
        return {}

def save_user(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f ,indent=2, ensure_ascii=False)

def register_user(user_id, user_name, first_name):
    users = load_user()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": user_name,
            "first_name": first_name
        }
        save_user(users)
        return True
    return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(f"Привет {user.first_name}, рад познакомится!") if register_user(user.id, user.username, user.first_name) else await update.message.reply_text(f"Привет {user.first_name}!")

    reply_keyboard = [["Пройти опрос"]]
    await update.message.reply_text("Выберите действие:", reply_markup=ReplyKeyboardMarkup(reply_keyboard,resize_keyboard=True))



async def survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Как вас зовут?")
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['survey_name'] = update.message.text
    await update.message.reply_text("Сколько тебе лет?")
    return AGE

async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Введите ваш возраст цифарми")
        return AGE
    context.user_data['survey_age'] = text
    await update.message.reply_text("Какой твой любимый город?")
    return CITY

async  def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    name = context.user_data['survey_name']
    age = context.user_data['survey_age']
    city = update.message.text

    users = load_user()

    user_id = str(user.id)
    users[user_id].update({
        "survey_name": name,
        "survey_age": age,
        "survey_city": city
    })
    save_user(users)

    await update.message.reply_text(f"Спасибо {name}, ты из {city}, тебе {age} лет")
    await start(update,context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Опрос отменен")
    await start(update,context)
    return ConversationHandler.END





def main() -> None:
    application = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Пройти опрос$"), survey)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    application.add_handler(conv_handler)

    logger.info("Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()