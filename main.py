from datetime import datetime
import sqlite3
import threading
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

TOKEN = open("TOKEN.txt", "r").read()

connection = sqlite3.connect("my_database.db", check_same_thread=False)
cur = connection.cursor()

updater = Updater(TOKEN, use_context=True)
disp = updater.dispatcher

# Using a dictionary to map user_id to the current_name
user_names = {}

def start(update, context):
    update.message.reply_text('Hey! Type /new to create a new reminder')

def new_reminder(update, context):
    update.message.reply_text('What shall I remind you of ?')
    return 1

def get_name(update, context):
    context.user_data['current_name'] = update.message.text
    user_names[update.message.chat_id] = context.user_data['current_name']  # Storing in the dictionary
    update.message.reply_text("Insert these info (Year-Month-Day) ?")
    return 2

def get_date(update, context):
    current_name = user_names.get(update.message.chat_id, "Unknown")  # Retrieving the name from the dictionary
    current_date = update.message.text
    user_id = update.message.chat_id

    cur.execute("SELECT * FROM user WHERE id=?", (user_id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO user (id) VALUES (?)", (user_id,))
    cur.execute("INSERT INTO reminder (user_id, name, date, reminded ) VALUES (?, ?, ?, ?)",
                (user_id, current_name, current_date, 0))

    connection.commit()

    update.message.reply_text("I will remind you!")
    return ConversationHandler.END

def cancel(update, context):
    update.message.reply_text("Cancelled")
    return ConversationHandler.END

def do_remind():
    while True:
        today = datetime.now().strftime('%m-%d')
        cur.execute("SELECT * FROM reminder WHERE strftime('%m-%d', date)=? AND reminded=0", (today,))

        rows = cur.fetchall()
        for row in rows:
            row_id = row[0]
            name = row[2]
            user_id = row[4]
            updater.bot.send_message(chat_id=user_id, text=f"Today's reminder :{name}")
            cur.execute("UPDATE reminder SET reminded = 1 WHERE id=?", (row_id,))
            connection.commit()
        time.sleep(10)

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("new", new_reminder)],
    states={
        1: [MessageHandler(Filters.text, get_name)],
        2: [MessageHandler(Filters.text, get_date)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

disp.add_handler(CommandHandler("start", start))
disp.add_handler(conv_handler)

threading.Thread(target=do_remind).start()

updater.start_polling()
updater.idle()
