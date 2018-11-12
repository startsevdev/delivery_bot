import telebot
import ssl
from geopy.geocoders import Nominatim
from telebot import types
from datetime import datetime
import sqlite3
import sys
sys.path.append('../')
import tokens


bot = telebot.TeleBot(tokens.IskraPizzaBot, threaded=False)

geolocator = Nominatim(user_agent="http://telegram.me/iskrapizzabot")

database = "/Users/alexander/code/bots/databases/iskra.db"


WAIT_DEL = 0
WAIT_FIRST_WATCHING_ITEM = 1
WAIT_FIRST_ITEM = 2
WAIT_WATCHING_ITEM = 3
WAIT_ITEM = 4
WAIT_CONFIRM = 5
WAIT_ADDRESS = 6
WAIT_OTHER_ADDRESS = 7
WAIT_PHONE_LOCATION = 8
WAIT_PHONE_ADDRESS = 9


print("\n- - - StartsevDev's IskraPizzaBot - - -\n")


# SUPPORT FUNCTIONS


def console_print(message):
    now = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")

    if message.content_type == "location":
        print("{} | {}: {}, {}".format
              (now, message.from_user.first_name, message.location.latitude, message.location.longitude))

    elif message.content_type == "contact":
        print("{} | {}: {}".format
              (now, message.from_user.first_name, message.contact.phone_number))

    else:
        print("{} | {}: {}".format(now, message.from_user.first_name, message.text))


def return_items():
    items_list = []

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM items")

    for item in cursor.fetchall():
        items_list.append(item[0])

    conn.close()

    return items_list


# KEYBOARDS

items = return_items()


def menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    for item in items:
        keyboard.add(item)

    return keyboard


def pre_order_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)

    keyboard.add("Удалить пиццу", "Оформить заказ")

    for item in items:
        keyboard.add(item)

    return keyboard


def item_keyboard_1():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить в заказ")
    keyboard.add("Меню")

    return keyboard


def item_keyboard_2():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Добавить в заказ")
    keyboard.add("Меню", "Оформить заказ")

    return keyboard


def confirm_order_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("Подтвердить заказ")
    keyboard.add("Удалить пиццу", "Добавить пиццу")

    return keyboard


def numbers_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    keyboard.add("1", "2", "3")
    keyboard.add("4", "5", "6")
    keyboard.add("7", "8", "9")
    keyboard.add("Отмена")

    return keyboard


def geo_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Поделиться текущим местоположением", request_location=True)
    keyboard.add(button_geo)

    return keyboard


def other_geo_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_geo = types.KeyboardButton(text="Поделиться текущим местоположением", request_location=True)
    keyboard.add(button_geo)
    keyboard.add("Отменить заказ")

    return keyboard


def phone_keyboard():
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Отправить телефон", request_contact=True)
    keyboard.add(button_phone)

    return keyboard


# GEOPY


def check_location(message):
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

    coords = "{}, {}".format(message.location.latitude, message.location.longitude)

    location = geolocator.reverse(coords)

    try:
        state = location.raw['address']['state']
        district = location.raw['address']['state_district']

        if state == "Санкт-Петербург" and district == "Центральный район":
            check = True

        else:
            check = False

    except KeyError:
        check = False

    return check


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


def send_watching_item(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT watching_item from users WHERE user_id = {}".format(message.from_user.id))
    watching_item_id = cursor.fetchone()[0]

    cursor.execute("SELECT image FROM items WHERE id = {}".format(watching_item_id))
    image = cursor.fetchone()[0]

    cursor.execute("SELECT price FROM items WHERE id = {}".format(watching_item_id))
    price = cursor.fetchone()[0]

    conn.close()

    bot.send_photo(message.from_user.id, image)
    bot.send_message(message.from_user.id, str(price) + " р.", reply_markup=item_keyboard_1())


def add_item_in_order(message):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT watching_item from users WHERE user_id = {}".format(message.from_user.id))
    item_id = cursor.fetchone()[0]

    cursor.execute("INSERT INTO users_items VALUES ({}, {}, Null)".format(message.from_user.id, item_id))
    conn.commit()

    conn.close()


def return_order_sum(message):
    order_prices = []

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    # достаем id добавленных товаров из users_items
    cursor.execute("SELECT item_id FROM users_items WHERE user_id = {}".format(message.from_user.id))
    order_item_ids = cursor.fetchall()

    # добавляем цену товаров в список кортежей order_prices
    for item_id in order_item_ids:
        cursor.execute("SELECT price FROM items WHERE id = {}".format(item_id[0]))

        order_prices.append(cursor.fetchone()[0])
    order_sum = sum(order_prices)

    return order_sum


def return_order_list(message):
    order_text = "Мой заказ:\n"
    order_items = []
    order_items_prices = []
    order_items_strings = []

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    # достаем id добавленных товаров из users_items
    cursor.execute("SELECT item_id FROM users_items WHERE user_id = {}".format(message.from_user.id))
    order_item_ids = cursor.fetchall()

    # добавляем название и цену добавленных товаров в список кортежей order_items
    for item_id in order_item_ids:
        cursor.execute("SELECT name FROM items WHERE id = {}".format(item_id[0]))
        order_items.append(cursor.fetchone()[0])
        #print(order_items)
    conn.close()

    # сортируем по имени товара
    order_items = sorted(order_items)

    # создаем строку с каждым из товаров
    #for order_item in order_items:
    #    order_items_strings.append("{} – {} р.".format(order_item[0], order_item[1]))

    # создаем пронумерованный список строк
    for counter, order_item in enumerate(order_items, 1):
        order_text += "{}. {}\n".format(counter, order_item)

    order_text += "\nСумма: {} р.".format(return_order_sum(message))

    if order_text == "Мой заказ:\n\nСумма: 0 р.":
        order_text = "Заказ пуст 🤷‍♀️"

    return order_text


def del_item_from_order(message):
    item_ids = []
    ids = []
    names_ids = []

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    # достаем item_id из users_items в список кортежей
    cursor.execute("SELECT item_id FROM users_items WHERE user_id = {}".format(message.from_user.id))
    item_ids_tuple = cursor.fetchall()

    for i in item_ids_tuple:
        item_ids.append(i[0])

    # достаем id из users_items в список кортежей
    cursor.execute("SELECT id FROM users_items WHERE user_id = {}".format(message.from_user.id))
    ids_tuple = cursor.fetchall()

    for i in ids_tuple:
        ids.append(i[0])

    # объединяем item_id и id
    item_id_id = [list(tup) for tup in zip(item_ids, ids)]

    # добавляем в names_ids списки [name, id]
    for i in item_id_id:
        cursor.execute("SELECT name FROM items WHERE id = {}".format(i[0]))
        names_ids.append([cursor.fetchone()[0], i[1]])

    # сортируем
    names_ids = sorted(names_ids)

    #print(names_ids)

    try:
        del_id = names_ids[int(message.text) - 1][1]
    except IndexError as err:
        print(err)
    else:
        cursor.execute("DELETE FROM users_items WHERE id = {}".format(del_id))
        conn.commit()
    conn.close()


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


def send_order(message):
    order_text = return_order_list(message) + "\n\n"

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    cursor.execute("SELECT phone FROM users WHERE user_id = {}".format(message.from_user.id))
    phone = cursor.fetchone()[0]

    if return_state(message) == WAIT_PHONE_ADDRESS:
        cursor.execute("SELECT address FROM users WHERE user_id = {}".format(message.from_user.id))

        address = cursor.fetchone()[0]

        order_text += "Адрес: " + address

        bot.send_contact('26978532', phone, message.from_user.first_name)
        bot.send_message("26978532", order_text)

    elif return_state(message) == WAIT_PHONE_LOCATION:
        cursor.execute("SELECT longitude FROM users WHERE user_id = {}".format(message.from_user.id))
        longitude = cursor.fetchone()[0]
        cursor.execute("SELECT latitude FROM users WHERE user_id = {}".format(message.from_user.id))
        latitude = cursor.fetchone()[0]

        bot.send_contact('26978532', phone, message.from_user.first_name)
        bot.send_message("26978532", order_text)
        bot.send_location("26978532", latitude, longitude)


# HANDLERS


@bot.message_handler(commands=['start'])
def start(message):
    console_print(message)

    add_user(message)

    bot.send_message(message.from_user.id, "Добро пожаловать!\n\nВыберите пиццу: ", reply_markup=menu_keyboard())


@bot.message_handler(commands=['cancel'])
def cancel(message):
    state = return_state(message)

    if state == WAIT_FIRST_WATCHING_ITEM:

        bot.send_message(message.from_user.id, "Заказ пуст. Выберите пиццу: ", reply_markup=menu_keyboard())

    elif state == WAIT_FIRST_ITEM:

        bot.send_message(message.from_user.id, "Ваш заказ пуст. Добавьте в него эту пиццу или перейдите в меню")

        send_watching_item(message)

    else:

        add_user(message)

        bot.send_message(message.from_user.id, "Заказ отменен")
        bot.send_message(message.from_user.id, "Новый заказ: ", reply_markup=menu_keyboard())


@bot.message_handler(content_types="location")
def get_location(message):
    console_print(message)

    if return_state(message) == WAIT_ADDRESS:
        if check_location(message):
            set_location(message)
            set_state(message, WAIT_PHONE_LOCATION)

            bot.send_message(message.from_user.id, "По какому номеру мы можем связаться с вами?", reply_markup=phone_keyboard())

        else:
            set_state(message, WAIT_OTHER_ADDRESS)
            bot.send_message(message.from_user.id, "Доставка доступна только в Центральном районе 🤷‍♀\n\nЧтобы указать другой адрес, нажмите 📎, затем 📍 и выберите другую точку на карте", reply_markup=other_geo_keyboard())

    elif return_state(message) == WAIT_OTHER_ADDRESS:
        if check_location(message):
            set_location(message)
            set_state(message, WAIT_PHONE_LOCATION)

            bot.send_message(message.from_user.id, "По какому номеру мы можем связаться с вами?", reply_markup=phone_keyboard())
        else:
            bot.send_message(message.from_user.id, "Доставка доступна только в Центральном районе 🤷‍♀\n\nЧтобы указать другой адрес, нажмите 📎, затем 📍 и выберите другую точку на карте", reply_markup=other_geo_keyboard())


@bot.message_handler(content_types="contact")
def get_contact(message):
    console_print(message)

    if return_state(message) == WAIT_PHONE_ADDRESS or return_state(message) == WAIT_PHONE_LOCATION:

        set_phone(message)
        send_order(message)
        add_user(message)
        bot.send_message(message.from_user.id, "Ваш заказ успешно оформлен! Мы свяжемся с вами в течение 5 минут")
        bot.send_message(message.from_user.id, "Новый заказ: ", reply_markup=menu_keyboard())


@bot.message_handler(content_types="text")
def giving_text(message):
    console_print(message)

    if return_state(message) == WAIT_FIRST_WATCHING_ITEM:

        for item in items:
            if message.text == item:
                send_item(message)
                set_watching_item(message)
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
            if return_order_sum(message) >= 500:
                set_state(message, WAIT_CONFIRM)
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())
            else:
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message) + "\n\nМинимальная сумма заказа 500 руб. Добавьте еще одну пиццу 🍕", reply_markup=menu_keyboard())

        elif message.text == "Удалить пиццу":
            if return_order_list(message) == "Заказ пуст 🤷‍♀️":
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message) + "\nДобавьте пиццу:", reply_markup=menu_keyboard())
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
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
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
            if return_order_sum(message) >= 500:
                clear_watching_item(message)
                set_state(message, WAIT_CONFIRM)
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())
            else:
                set_state(message, WAIT_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(
                    message) + "\n\nМинимальная сумма заказа 500 руб. Добавьте еще одну пиццу 🍕", reply_markup=menu_keyboard())

        else:
            bot.send_message(message.from_user.id, "Добавьте пиццу в заказ, вернитесь к меню или перейдите к оформлению заказа:", item_keyboard_2())

    elif return_state(message) == WAIT_CONFIRM:

        if message.text == "Подтвердить заказ":
            if return_order_sum(message) >= 500:
                set_state(message, WAIT_ADDRESS)
                bot.send_message(message.from_user.id, "Поделитесь своей геопозицией через кнопку ниже или просто впишите улицу, номер дома и подъезд", reply_markup=geo_keyboard())
            else:
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message) + "\n\nМинимальная сумма заказа 500 руб. Добавьте еще одну пиццу 🍕", reply_markup=menu_keyboard())

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

    elif return_state(message) == WAIT_OTHER_ADDRESS:

        if message.text == "Отменить заказ":
            add_user(message)
            bot.send_message(message.from_user.id, "Заказ отменен")
            bot.send_message(message.from_user.id, "Выберите пиццу: ", reply_markup=menu_keyboard())
        else:
            set_address(message)
            set_state(message, WAIT_PHONE_ADDRESS)
            bot.send_message(message.from_user.id, "По какому номеру мы можем связаться с вами?", reply_markup=phone_keyboard())

    elif return_state(message) == WAIT_PHONE_ADDRESS or return_state(message) == WAIT_PHONE_LOCATION:

        if message.text.isdigit() or (message.text[0] == "+" and message.text[1:].isdigit()):

            set_phone(message)
            send_order(message)
            add_user(message)
            bot.send_message(message.from_user.id, "Ваш заказ успешно оформлен! Мы свяжемся с вами в течение 5 минут")
            bot.send_message(message.from_user.id, "Новый заказ: ", reply_markup=menu_keyboard())

        else:
            bot.send_message(message.from_user.id, "Отправьте контакт через кнопку или в введите в формате +71234567890 или 81234567890", reply_markup=phone_keyboard())

    elif return_state(message) == WAIT_DEL:

        if message.text.isdigit() and int(message.text) > 0:
            del_item_from_order(message)

            if return_order_list(message) == "Заказ пуст 🤷‍♀️":
                set_state(message, WAIT_FIRST_WATCHING_ITEM)
                bot.send_message(message.from_user.id, return_order_list(message) + "\nДобавьте пиццу:", reply_markup=menu_keyboard())

            else:
                set_state(message, WAIT_CONFIRM)
                bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        elif message.text == "Отмена":

            set_state(message, WAIT_CONFIRM)
            bot.send_message(message.from_user.id, return_order_list(message), reply_markup=confirm_order_keyboard())

        else:
            bot.send_message(message.from_user.id, "❗ Введите натуральное число.")


bot.polling(True)
