import telebot
from telebot import types
from datetime import datetime
import sqlite3


print("\n- - - StartsevDev's IskraPizzaBot - - -\n")


token = "656442097:AAFlmiPYuzWFYrP7EJcDCbi4iKDaKB-hWoQ"
bot = telebot.TeleBot(token)


items = ["Маргарита", "Мортадела", "Прошуто фунге", "Пепперони", "4 сыра", "С грушей и горгонзоллой",
         "Вегетарианская", "С пореем", "С беконом и маскарпоне", "С лососем", "С артишоком и анчоусом",
         "С лисичками и беконом", "Со старчетеллой и инжиром", "Сациви кальцоне", "Ди парма", "Фокачча"]


def console_print(message):
    now = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    print("{} | {}: {}".format(now, message.from_user.first_name, message.text))


def menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    for item in items:
        keyboard.add(item)

    return keyboard


def add_order(message):
    conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO orders VALUES (Null, {}, Null, Null, 0)".format(message.from_user.id))
    except sqlite3.IntegrityError as err:
        print("sqlite3.IntegrityError: ", err)
        cursor.execute("UPDATE orders "
                       "SET state = 0, phone = NULL, address = NULL "
                       "WHERE user_id = {}".format(message.from_user.id))

    conn.commit()
    conn.close()


@bot.message_handler(commands=['start'])
def start(message):
    console_print(message)

    add_order(message)

    bot.send_message(message.from_user.id, "Добро пожаловать!", reply_markup=menu_keyboard())


@bot.message_handler()
def giving_text(message):
    console_print(message)


bot.polling(none_stop=0, interval=0)
