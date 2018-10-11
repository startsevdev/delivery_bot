import telebot
from telebot import types
from datetime import datetime
import sqlite3
import logging
import time
import sys
sys.path.append('../')
import tokens


token = tokens.IskraPizzaBot
bot = telebot.TeleBot(token)

logger = telebot.logger

database = "/Users/alexander/code/bots/databases/iskra.db"

items = ["Маргарита", "Прошуто фунге", "Пепперони"]

WAIT_DEL = 0
WAIT_FIRST_WATCHING_ITEM = 1
WAIT_FIRST_ITEM = 2
WAIT_WATCHING_ITEM = 3
WAIT_ITEM = 4
WAIT_CONFIRM = 5
WAIT_ADDRESS = 6
WAIT_PHONE_LOCATION = 7
WAIT_PHONE_ADDRESS = 8


print("\n- - - StartsevDev's IskraPizzaBot - - -\n")


# SUPPORT FUNCTIONS


def console_print(message):
    now = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    print("{} | {}: {}".format(now, message.from_user.first_name, message.text))


# KEYBOARDS


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


def numbers_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("1")
    keyboard.add("2")
    keyboard.add("3")
    keyboard.add("4")
    keyboard.add("5")
    keyboard.add("6")
    keyboard.add("7")
    keyboard.add("8")
    keyboard.add("9")

    return keyboard


def geo_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Отправить точку на карте", request_location=True)
    keyboard.add(button_geo)

    return keyboard


def phone_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Отправить телефон", request_contact=True)
    keyboard.add(button_phone)

    return keyboard


# DATABASE FUNCTIONS


def set_state(message, state):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET state = {} WHERE user_id = {}".format(state, message.from_user.id))
    conn.commit()
    conn.close()


def return_state(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT state FROM users WHERE user_id = {}".format(message.chat.id))
    state = cursor.fetchone()

    try:
        state = state[0]
    except TypeError as err:
        print("TypeError: ", err)
        bot.send_message(message.from_user.id, "Чтобы начать работу, отправьте /start")
    else:
        return int(state)

    conn.close()


def add_user(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users VALUES ({}, Null, Null, Null, 1, Null, Null)".format(message.from_user.id))
        conn.commit()
    except sqlite3.IntegrityError as err:
        cursor.execute("DELETE FROM users WHERE user_id = {}".format(message.from_user.id))
        cursor.execute("DELETE FROM users_items WHERE user_id = {}".format(message.from_user.id))
        conn.commit()

        add_user(message)

    conn.close()


def set_watching_item(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items WHERE name = '{}'".format(message.text))
    item_id = cursor.fetchone()[0]
    cursor.execute("UPDATE users SET watching_item = {} WHERE user_id = {}".format(item_id, message.from_user.id))
    conn.commit()
    conn.close()


def clear_watching_item(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET watching_item = Null WHERE user_id = {}".format(message.from_user.id))
    conn.commit()
    conn.close()


def send_item(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT image FROM items WHERE name = '{}'".format(message.text))
    image = cursor.fetchone()[0]

    cursor.execute("SELECT price FROM items WHERE name = '{}'".format(message.text))
    price = cursor.fetchone()[0]

    conn.close()

    bot.send_photo(message.from_user.id, image)

    if return_state(message) == WAIT_FIRST_WATCHING_ITEM:
        bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=item_keyboard_1())
    elif return_state(message) == WAIT_WATCHING_ITEM:
        bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=item_keyboard_2())


def add_item_in_order(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT watching_item from users WHERE user_id = {}".format(message.from_user.id))
    item_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO users_items VALUES ({}, {}, Null)".format(message.from_user.id, item_id))
    conn.commit()

    conn.close()


def return_order_list(message):
    order_list = "Мой заказ: \n"
    order_item_names = []

    conn = sqlite3.connect(database)
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


def set_location(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET longitude = {}, latitude = {} WHERE user_id = {}".format(message.location.longitude, message.location.latitude, message.from_user.id))
    conn.commit()
    conn.close()


def set_address(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET address = '{}' WHERE user_id = {}".format(message.text, message.from_user.id))
    conn.commit()
    conn.close()


def set_phone(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    try:
        phone = message.contact.phone_number
    except AttributeError:
        phone = message.text

    cursor.execute("UPDATE users SET phone = '{}' WHERE user_id = {}".format(phone, message.from_user.id))
    conn.commit()
    conn.close()


def send_order_address(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT address FROM users WHERE user_id = {}".format(message.from_user.id))
    address = cursor.fetchone()[0]

    cursor.execute("SELECT phone FROM users WHERE user_id = {}".format(message.from_user.id))
    phone = cursor.fetchone()[0]

    order_text = return_order_list(message) + "\n"
    order_text += "Адрес: " + address

    bot.send_message("26978532", order_text)
    bot.send_contact('26978532', phone, message.from_user.first_name)


def send_order(message):
    order_text = return_order_list(message) + "\n"

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT phone FROM users WHERE user_id = {}".format(message.from_user.id))
    phone = cursor.fetchone()[0]

    if return_state(message) == WAIT_PHONE_ADDRESS:
        cursor.execute("SELECT address FROM users WHERE user_id = {}".format(message.from_user.id))
        address = cursor.fetchone()[0]
        order_text += "Адрес: " + address
        bot.send_message("26978532", order_text)

    elif return_state(message) == WAIT_PHONE_LOCATION:
        cursor.execute("SELECT longitude FROM users WHERE user_id = {}".format(message.from_user.id))
        longitude = cursor.fetchone()[0]
        cursor.execute("SELECT latitude FROM users WHERE user_id = {}".format(message.from_user.id))
        latitude = cursor.fetchone()[0]
        bot.send_message("26978532", order_text)
        bot.send_location(message.from_user.id, longitude, latitude)

    bot.send_contact('26978532', phone, message.from_user.first_name)


def del_item_from_order(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users_items WHERE user_id = {}".format(message.from_user.id))

    try:
        item_id = cursor.fetchall()[int(message.text) - 1][0]
    except IndexError as err:
        print(err)
    else:
        cursor.execute("DELETE FROM users_items WHERE id = {}".format(item_id))
        conn.commit()
    conn.close()


# HANDLERS


@bot.message_handler(commands=['start'])
def start(message):
    console_print(message)

    add_user(message)

    bot.send_message(message.from_user.id, "Добро пожаловать!\n\nВыберите пиццу: ", reply_markup=menu_keyboard())


@bot.message_handler(content_types="location")
def get_location(message):

    if return_state(message) == WAIT_ADDRESS:

        set_location(message)
        set_state(message, WAIT_PHONE_LOCATION)
        bot.send_message(message.from_user.id, "По какому номеру мы можем связаться с вами?", reply_markup=phone_keyboard())


@bot.message_handler(content_types="contact")
def get_contact(message):

    if return_state(message) == WAIT_PHONE_ADDRESS or return_state(message) == WAIT_PHONE_LOCATION:

        set_phone(message)
        send_order(message)
        add_user(message)
        bot.send_message(message.from_user.id, "Ваш заказ успешно оформлен! Мы свяжемся с вами в течение 5 минут", reply_markup=menu_keyboard())


@bot.message_handler(content_types="text")
def giving_text(message):
    console_print(message)

    if return_state(message) == WAIT_FIRST_WATCHING_ITEM:

        for item in items:
            if message.text == item:
                set_watching_item(message)
                send_item(message)
                set_state(message, WAIT_FIRST_ITEM)
                break
        else:
            bot.send_message(message.from_user.id, "Сначала выберите пиццу:\n", reply_markup=menu_keyboard())

    elif return_state(message) == WAIT_FIRST_ITEM:

        if message.text == "Добавить в заказ":
            add_item_in_order(message)
            clear_watching_item(message)
            set_state(message, WAIT_WATCHING_ITEM)
            bot.send_message(message.from_user.id, "Пицца добавлена!\n\n" + return_order_list(message), reply_markup=pre_order_menu_keyboard())

        elif message.text == "Меню":
            clear_watching_item(message)
            set_state(message, WAIT_FIRST_WATCHING_ITEM)
            bot.send_message(message.from_user.id, "Выберите пиццу:\n", reply_markup=menu_keyboard())

        else:
            bot.send_message(message.from_user.id, "Добавьте пиццу в заказ или перейдите в меню:", item_keyboard_1())

    elif return_state(message) == WAIT_WATCHING_ITEM:

        if message.text == "Оформить заказ":
            set_state(message, WAIT_CONFIRM)
            bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        elif message.text == "Удалить пиццу":
            if return_order_list(message) == "Заказ пуст 🤷‍♀️":
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message) + "\nВыберите пиццу:", reply_markup=menu_keyboard())
            else:
                set_state(message, WAIT_DEL)
                bot.send_message(message.from_user.id, return_order_list(message) + "\nУкажите номер пункта", reply_markup=numbers_keyboard())

        else:
            for item in items:
                if message.text == item:
                    set_watching_item(message)
                    send_item(message)
                    set_state(message, WAIT_ITEM)
                    break
            else:
                bot.send_message(message.from_user.id, "Выберите еще одну пиццу, перейдите к офромлению заказа или удалите пиццу", reply_markup=pre_order_menu_keyboard())

    elif return_state(message) == WAIT_ITEM:

        if message.text == "Добавить в заказ":
            add_item_in_order(message)
            clear_watching_item(message)
            set_state(message, WAIT_WATCHING_ITEM)
            bot.send_message(message.from_user.id, "Пицца добавлена!\n\n" + return_order_list(message), reply_markup=pre_order_menu_keyboard())

        elif message.text == "Меню":
            clear_watching_item(message)
            set_state(message, WAIT_WATCHING_ITEM)
            bot.send_message(message.from_user.id, "Выберите пиццу:\n", reply_markup=pre_order_menu_keyboard())

        elif message.text == "Оформить заказ":
            clear_watching_item(message)
            set_state(message, WAIT_CONFIRM)
            bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        else:
            bot.send_message(message.from_user.id, "Добавьте пиццу в заказ, вернитесь к меню или перейдите к оформлению заказа:", item_keyboard_2())

    elif return_state(message) == WAIT_CONFIRM:

        if message.text == "Подтвердить заказ":
            set_state(message, WAIT_ADDRESS)
            bot.send_message(message.from_user.id, "Поделитесь своей геопозицией через кнопку ниже или просто впишите улицу, номер дома и подъезд", reply_markup=geo_keyboard())

        elif message.text == "Добавить пиццу":
            set_state(message, WAIT_WATCHING_ITEM)
            bot.send_message(message.from_user.id, "Выберите пиццу:\n", reply_markup=pre_order_menu_keyboard())

        elif message.text == "Удалить пиццу":
            set_state(message, WAIT_DEL)
            bot.send_message(message.from_user.id, return_order_list(message) + "\nУкажите номер пункта", reply_markup=numbers_keyboard())

        else:
            bot.send_message(message.from_user.id, "Подтвердите заказ, добавьте или удалите пиццу:", confirm_order_keyboard())

    elif return_state(message) == WAIT_ADDRESS:

        set_address(message)
        set_state(message, WAIT_PHONE_ADDRESS)
        bot.send_message(message.from_user.id, "По какому номеру мы можем связаться с вами?", reply_markup=phone_keyboard())

    elif return_state(message) == WAIT_PHONE_ADDRESS or return_state(message) == WAIT_PHONE_LOCATION:

        set_phone(message)
        send_order(message)
        add_user(message)
        bot.send_message(message.from_user.id, "Ваш заказ успешно оформлен! Мы свяжемся с вами в течение 5 минут", reply_markup=menu_keyboard())

    elif return_state(message) == WAIT_DEL:

        if message.text.isdigit() and int(message.text) > 0:
            del_item_from_order(message)

            if return_order_list(message) == "Заказ пуст 🤷‍♀️":
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=menu_keyboard())

            else:
                set_state(message, WAIT_CONFIRM)
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        elif message.text == "Отмена":

            set_state(message, WAIT_CONFIRM)
            bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        else:
            bot.send_message(message.from_user.id, "❗ Введите натуральное число.")


bot.polling()