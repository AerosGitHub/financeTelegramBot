import logging
import os

from telegram import Update
from telegram.ext import ConversationHandler, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from db import DB

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

db = DB()

ENTER_LOGIN, ENTER_PASSWORD, ENTER_CONTROL_PHRASE, CHECK_PASSWORD = range(4)

register_buffer = {}
login_buffer = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.check_telegram_id(update.effective_chat.id):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You connect to your account")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You don't connect to account\nIf you would like to connect account "
                                            "with this telegram type /connect\n"
                                            "If you wanna register you need to type /register")


async def connect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Type your login")
    return ENTER_PASSWORD


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello, type login you would like")
    return ENTER_LOGIN


async def set_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if db.check_login(update.message.text):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This login is used. Try another login")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Greate, type password you would like")
        register_buffer[update.effective_chat.id] = [update.message.text]
        return ENTER_PASSWORD


async def set_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in register_buffer.keys():
        register_buffer[update.effective_chat.id].append(update.message.text)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Greate, now type your control phrase. It will use for backup your account")
        return ENTER_CONTROL_PHRASE


async def set_control_phrase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.effective_chat.id in register_buffer.keys()) and (len(register_buffer[update.effective_chat.id]) == 2):
        buff_array = register_buffer.pop(update.effective_chat.id)
        login = buff_array[0]
        password = buff_array[1]
        control_phrase = update.message.text
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=db.set_user(login, password, control_phrase))
        return ConversationHandler.END


async def enter_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login_buffer[update.effective_chat.id] = [update.message.text]
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Now enter your password")
    return CHECK_PASSWORD


async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    login_buffer[update.effective_chat.id].append(update.message.text)
    if db.check_login(login_buffer[update.effective_chat.id][0]) and db.check_password(
            login_buffer[update.effective_chat.id][0], login_buffer[update.effective_chat.id][1]):
        db.set_telegram_id(update.effective_chat.id, login_buffer[update.effective_chat.id][1])
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You connected your login to telegram")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Login or password you typed incorrect. Try again")
    return ConversationHandler.END


async def something_went_wrong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text='Something went wrong')
    return ConversationHandler.END


if __name__ == '__main__':
    application = ApplicationBuilder().token(os.environ['TOKEN']).build()

    start_handler = CommandHandler('start', start)
    login_handler = ConversationHandler(entry_points=[CommandHandler('connect', connect)], states={
        ENTER_PASSWORD: [
            MessageHandler(filters.TEXT, enter_password)
        ],
        CHECK_PASSWORD: [
            MessageHandler(filters.TEXT, check_password)
        ]
    }, fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, something_went_wrong),
                  CommandHandler('cancel', something_went_wrong)])
    register_handler = ConversationHandler(entry_points=[CommandHandler('register', register)], states={
        ENTER_LOGIN: [
            MessageHandler(filters.TEXT, set_login)
        ],
        ENTER_PASSWORD: [
            MessageHandler(filters.TEXT, set_password)
        ],
        ENTER_CONTROL_PHRASE: [
            MessageHandler(filters.TEXT, set_control_phrase)
        ]
    }, fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, something_went_wrong),
                  CommandHandler('cancel', something_went_wrong)])

    application.add_handler(start_handler)
    application.add_handler(login_handler)
    application.add_handler(register_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)
