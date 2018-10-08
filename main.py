import telebot
from telebot import types
from datetime import datetime
import sqlite3

import sys
sys.path.append('../')
import tokens


print("\n- - - StartsevDev's IskraPizzaBot - - -\n")


token = tokens.IskraPizzaBot
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


def pre_order_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    keyboard.add("Оформить заказ")

    for item in items:
        keyboard.add(item)

    return keyboard


def pre_order_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Заказать")
    keyboard.add("Меню")

    return keyboard


def add_user(message):
    conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users VALUES ({}, Null, Null, 0, Null)".format(message.from_user.id))
    except sqlite3.IntegrityError as err:
        cursor.execute("DELETE FROM users WHERE user_id = {}".format(message.from_user.id))
        cursor.execute("DELETE FROM users_items WHERE user_id = {}".format(message.from_user.id))

        conn.commit()

        add_user(message)

    conn.commit()
    conn.close()


def add_item_in_order(message):
    conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT item_name from orders WHERE user_id = {}".format(message.from_user.id))
    item_name = cursor.fetchone()[0]

    cursor.execute("SELECT id from items WHERE name = '{}'".format(item_name))
    item_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO users_items VALUES ('{}', '{}')".format(message.from_user.id, item_id))

    conn.commit()
    conn.close()


@bot.message_handler(commands=['start'])
def start(message):
    console_print(message)

    add_user(message)

    bot.send_message(message.from_user.id, "Добро пожаловать!", reply_markup=menu_keyboard())


@bot.message_handler()
def giving_text(message):
    console_print(message)

    for item in items:
        if message.text == item:
            conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
            cursor = conn.cursor()

            cursor.execute("UPDATE users SET watching_item = '{}'".format(message.text))

            cursor.execute("SELECT image FROM items WHERE name = '{}'".format(message.text))
            image = cursor.fetchone()[0]

            cursor.execute("SELECT price FROM items WHERE name = '{}'".format(message.text))
            price = cursor.fetchone()[0]

            conn.commit()
            conn.close()

            bot.send_photo(message.from_user.id, image)
            bot.send_message(message.from_user.id, "280 р.", reply_markup=pre_order_keyboard())

    if message.text == "Меню":
        bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=menu_keyboard())

    elif message.text == "Заказать":
        add_item_in_order(message)

        bot.send_message(message.from_user.id, "Пицца добавлена в заказ!", reply_markup=pre_order_menu_keyboard())


bot.polling(none_stop=0, interval=0)
