import time

import telebot
from telebot import types
from datetime import datetime
import sqlite3
import logging

import sys
sys.path.append('../')
import tokens


print("\n- - - StartsevDev's IskraPizzaBot - - -\n")


token = tokens.IskraPizzaBot
bot = telebot.TeleBot(token)
logger = telebot.logger

items = ["Маргарита", "Мортадела", "Прошуто фунге", "Пепперони", "4 сыра", "С грушей и горгонзоллой",
         "Вегетарианская", "С пореем", "С беконом и маскарпоне", "С лососем", "С артишоком и анчоусом",
         "С лисичками и беконом", "Со старчетеллой и инжиром", "Сациви кальцоне", "Ди парма", "Фокачча"]


def console_print(message):
    now = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    print("{} | {}: {}".format(now, message.from_user.first_name, message.text))



#KEYBOARDS


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


def pre_order_keyboard_1():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить")
    keyboard.add("Меню")

    return keyboard


def pre_order_keyboard_2():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить")
    keyboard.add("Меню")
    keyboard.add("Оформить заказ")

    return keyboard



#WORK WITH DATABASE


def return_state(message):
    conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM users WHERE user_id = {}".format(message.chat.id))
    state = cursor.fetchone()

    try:
        state = state[0]
    except TypeError as err:
        print("TypeError: ", err)
        bot.send_message(message.from_user.id, "🔴 Ошибка. Чтобы начать работу, отправьте /start")
    else:
        return state

    conn.close()


def add_user(message):
    conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users VALUES ({}, Null, Null, Null, 'WAIT_FIRST_ITEM')".format(message.from_user.id))
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

    cursor.execute("SELECT watching_item from users WHERE user_id = {}".format(message.from_user.id))
    item_name = cursor.fetchone()[0]

    cursor.execute("SELECT id from items WHERE name = '{}'".format(item_name))
    item_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO users_items VALUES ({}, {})".format(message.from_user.id, item_id))
    conn.commit()

    cursor.execute("UPDATE users SET state = 'WAIT ORDER' WHERE user_id = {}".format(message.from_user.id))
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

    if message.text == "Меню":
        if return_state(message) == "WAIT_FIRST_ITEM":
            bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=menu_keyboard())
        else:
            bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=pre_order_menu_keyboard())

    elif message.text == "Добавить":
        add_item_in_order(message)

        bot.send_message(message.from_user.id, "Пицца добавлена в заказ!", reply_markup=pre_order_menu_keyboard())

    elif message.text == "Оформить заказ":
        order_text = "Мой заказ: \n"
        order_items = []

        conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
        cursor = conn.cursor()

        cursor.execute("SELECT item_id FROM users_items WHERE user_id = {}".format(message.from_user.id))
        item_ids = cursor.fetchall()

        for i in item_ids:
            cursor.execute("SELECT name FROM items WHERE id = {}".format(i[0]))
            order_items.append(cursor.fetchone()[0])

        print(order_items)

        conn.commit()
        conn.close()

    else:
        for item in items:
            if message.text == item:
                conn = sqlite3.connect('/Users/alexander/code/databases/iskra.db')
                cursor = conn.cursor()

                cursor.execute("UPDATE users SET watching_item = '{}' WHERE user_id = '{}'".format(message.text,
                                                                                                   message.from_user.id))

                cursor.execute("SELECT image FROM items WHERE name = '{}'".format(message.text))
                image = cursor.fetchone()[0]

                cursor.execute("SELECT price FROM items WHERE name = '{}'".format(message.text))
                price = cursor.fetchone()[0]

                conn.commit()
                conn.close()

                bot.send_photo(message.from_user.id, image)

                if return_state(message) == "WAIT_FIRST_ITEM":
                    bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=pre_order_keyboard_1())
                else:
                    bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=pre_order_keyboard_2())


bot.polling(none_stop=True)

#while True:
#    try:
#        bot.polling(none_stop=True)   except Exception as e:
#        logger.error(e)
#        time.sleep(15)
