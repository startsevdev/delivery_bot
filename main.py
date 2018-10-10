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

items = ["Маргарита", "Прошуто фунге", "Пепперони"]

#, "Мортадела", "4 сыра", "С грушей и горгонзоллой",
#         "Вегетарианская", "С пореем", "С беконом и маскарпоне", "С лососем", "С артишоком и анчоусом",
#         "С лисичками и беконом", "Со старчетеллой и инжиром", "Сациви кальцоне", "Ди парма", "Фокачча


def console_print(message):
    now = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    print("{} | {}: {}".format(now, message.from_user.first_name, message.text))


def return_name(message):
    if message.from_user.last_name:
        name = message.from_user.last_name + message.from_user.first_name
    else:
        name = message.from_user.first_name

    return name



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

    keyboard.add("Удалить пиццу")

    return keyboard


def item_keyboard_1():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить в заказ")
    keyboard.add("Меню")

    return keyboard


def item_keyboard_2():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить в заказ")
    keyboard.add("Меню")
    keyboard.add("Оформить заказ")

    return keyboard


def confirm_order_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Подтвердить заказ")
    keyboard.add("Добавить пиццу")
    keyboard.add("Удалить пиццу")

    return keyboard



#WORK WITH DATABASE


def return_order_list(message):
    order_list = "Мой заказ: \n"
    order_item_names = []

    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT item_id FROM users_items WHERE user_id = {}".format(message.from_user.id))
    order_item_ids = cursor.fetchall()
    print(order_item_ids)

    for i in order_item_ids:
        cursor.execute("SELECT name FROM items WHERE id = {}".format(i[0]))
        order_item_names.append(cursor.fetchone()[0])

    conn.close()

    for counter, item_name in enumerate(order_item_names[0:], 1):
        order_list += "{}. {}\n".format(counter, item_name)

    if order_list == "Мой заказ: \n":
        order_list = "Заказ пуст 🤷‍♀️"

    return order_list


def set_state(message, state):
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET state = '{}' WHERE user_id = {}".format(state, message.from_user.id))
    conn.commit()
    conn.close()


def return_state(message):
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
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
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
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
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT watching_item from users WHERE user_id = {}".format(message.from_user.id))
    item_name = cursor.fetchone()[0]

    cursor.execute("SELECT id from items WHERE name = '{}'".format(item_name))
    item_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO users_items VALUES ({}, {}, Null)".format(message.from_user.id, item_id))
    conn.commit()

    cursor.execute("UPDATE users SET state = 'WAIT ORDER' WHERE user_id = {}".format(message.from_user.id))
    conn.commit()

    conn.close()


def del_item_from_order(message):
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users_items WHERE user_id = {}".format(message.from_user.id))

    try:
        id = cursor.fetchall()[int(message.text) - 1][0]
    except IndexError as err:
        print(err)
        #bot.send_message(message.from_user.id, return_order_list(message) + "Укажите номер пунктa")
    else:
        cursor.execute("DELETE FROM users_items WHERE id = {}".format(id))
        conn.commit()
    conn.close()


def send_menu(message):
    if return_state(message) == "WAIT_FIRST_ITEM":
        bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=menu_keyboard())
    else:
        bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=pre_order_menu_keyboard())


def send_order(message):
    conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
    cursor = conn.cursor()

    cursor.execute("SELECT address FROM users WHERE user_id = {}".format(message.from_user.id))
    address = cursor.fetchone()[0]

    cursor.execute("SELECT phone FROM users WHERE user_id = {}".format(message.from_user.id))
    phone = cursor.fetchone()[0]

    name = return_name(message)

    order_text = return_order_list(message) + "\n"
    order_text += "Адрес: " + address

    bot.send_message('26978532', order_text)
    bot.send_contact(message.from_user.id, phone, name)


@bot.message_handler(commands=['start'])
def start(message):
    console_print(message)

    add_user(message)

    bot.send_message(message.from_user.id, "Добро пожаловать!", reply_markup=menu_keyboard())


@bot.message_handler(content_types="location")
def get_location(message):
    print("I GOT LOCATION")

    bot.send_location(message.from_user.id, message.location.latitude, message.location.longitude)


@bot.message_handler(content_types="contact")
def get_contact(message):
    if return_state(message) == "WAIT_NUMBER":
        print("I GOT CONTACT")

        conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET phone = '{}' WHERE user_id = {}".format(message.contact.phone_number, message.from_user.id))
        conn.commit()

        send_order(message)

        cursor.execute("UPDATE users SET "
                       "phone = NULL, "
                       "address = NULL, "
                       "watching_item = NULL, "
                       "state = 'WAIT_FIRST_ITEM' "
                       "WHERE user_id = {}".format(message.from_user.id))
        conn.commit()

        cursor.execute("DELETE FROM users_items WHERE user_id = {}".format(message.from_user.id))
        conn.commit()

        conn.close()

        bot.send_message(message.from_user.id, "Ваш заказ успешно оформлен! Мы свяжемся с вами в течение 5 минут")

        send_menu(message)



@bot.message_handler()
def giving_text(message):
    console_print(message)

    if message.text == "Меню":
        send_menu(message)

    elif message.text == "Добавить в заказ":
        add_item_in_order(message)

        bot.send_message(message.from_user.id, "Пицца добавлена!\n\n" + return_order_list(message), reply_markup=pre_order_menu_keyboard())

    elif message.text == "Оформить заказ":

        conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET state = 'WAIT_CONFIRM' WHERE user_id = {}".format(message.from_user.id))
        conn.commit()
        conn.close()

        bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

    elif message.text == "Добавить пиццу":
        send_menu(message)

    elif message.text == "Удалить пиццу":
        if return_order_list(message) == "Заказ пуст 🤷‍♀️":
            set_state(message, "WAIT_FIRST_ITEM")
            bot.send_message(message.from_user.id, return_order_list(message))
            send_menu(message)
        else:
            bot.send_message(message.from_user.id, return_order_list(message))
            bot.send_message(message.from_user.id, "Укажите номер пунктa")

            set_state(message, "WAIT_DEL")

    elif message.text == "Подтвердить заказ":
        set_state(message, "WAIT_ADDRESS")
        bot.send_message(message.from_user.id, "Укажите адрес")

    elif return_state(message) == "WAIT_ADDRESS":
        conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET address = '{}', state = 'WAIT_NUMBER' WHERE user_id = {}".format(message.text, message.from_user.id))
        conn.commit()
        conn.close()

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
        keyboard.add(button_phone)

        bot.send_message(message.from_user.id, "Как с вами можно связаться?", reply_markup=keyboard)

    elif return_state(message) == "WAIT_DEL":
        if message.text.isdigit() and int(message.text) > 0:
            del_item_from_order(message)
            if return_order_list(message) == "Заказ пуст 🤷‍♀️":
                set_state(message, "WAIT_FIRST_ITEM")
                bot.send_message(message.from_user.id, return_order_list(message))
                send_menu(message)
            else:
                set_state(message, "WAIT_CONFIRM")
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())
        else:
            bot.send_message(message.from_user.id, "❗ Введите натуральное число.")

    # message.text == one of ITEM NAMES
    else:
        for item in items:
            if message.text == item:
                conn = sqlite3.connect('/Users/alexander/code/bots/databases/iskra.db')
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
                    bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=item_keyboard_1())
                else:
                    bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=item_keyboard_2())


bot.polling()
