import telebot
from registration_handler import RegistrationHandler
from interests_handler import InterestsHandler
from add_items import NewItem
import asyncio


bot = telebot.TeleBot("6885951107:AAH6BJaLwZmO5L4Scf6F3IEt_Wdvdbm3nDk")

states = {}
reg_handlers = {}
interests = {}
items = {}

counter = 0
user_data = []


# Обрабатываем команду start, если пользователя нет в бд, начинаем процесс регистрации, создавая соответствующий хэндлер
# и обновляя текущий статус пользователя
@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    if message.chat.id not in states:
        states[message.chat.id] = 'notRegistered'
        reg_handlers[message.chat.id] = RegistrationHandler()
        bot.send_message(message.chat.id, 'Добро пожаловать! Давайте Вас зарегистрируем.')
        bot.send_message(message.chat.id, reg_handlers[message.chat.id].do_registration(''))


# Обрабатываем команду profile, выводим информацию о профиле отправившего команду
@bot.message_handler(commands=['profile'])
def open_profile(message):
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        current_bot_message = reg_handlers[message.chat.id].get_user_profile()
        bot.send_message(message.chat.id, current_bot_message)
    else:
        bot.send_message(message.chat.id, 'Вы еще не зарегистрированы')


# Отправляем отдельными сообщениями все интересы данного пользователя
@bot.message_handler(commands=['interests'])
def open_profile(message):
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        for interest in interests[message.chat.id]:
            bot.send_message(message.chat.id, interest.interest_info())
    else:
        bot.send_message(message.chat.id, 'Необходимо зарегестрироваться и указать интересы')


# создание кнопок
def get_button_brand():
    # переменная в которой хранятся все кнопки
    markup_inline = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    item = NewItem()
    for name_brand in item.all_brand: # создание кнопок
        brand_button = telebot.types.KeyboardButton(text=name_brand)
        markup_inline.add(brand_button)
    return markup_inline


@bot.message_handler(commands=['add_item'])
def add_item(message):
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        states[message.chat.id] = 'on_adding_items'
        if message.chat.id not in items:
            items[message.chat.id] = []
        items[message.chat.id].append(NewItem())
        bot.send_message(message.chat.id, 'Давайте добавим предмет.')
        bot.send_message(message.chat.id, 'Укадите бренд часов', reply_markup=get_button_brand()) #вынес вывод сообщения с кнопками в функцию
        current_bot_message = items[message.chat.id][len(items[message.chat.id]) - 1].create_item(message.text)
        bot.send_message(message.chat.id, current_bot_message)
# вынести часть создания бренда (сообщение) в add_item, туда прикрепить кнопки, и вынести вывод последнего сообщения, на прикрепить удаление клавиатуры


# созадание фунции с переменной по удалению клавиатуры
def remove_button_brand():
    remove_markup = telebot.types.ReplyKeyboardRemove()
    return remove_markup


# Обработка всех текстовых сообщений, которые не являются командами
@bot.message_handler(func=lambda message: True)
def handle_request(message):
    if states[message.chat.id] == 'notRegistered': # Данный статус только в том случае, если человек не завершил регистрацию и зашел в бота впервые
        current_bot_message = reg_handlers[message.chat.id].do_registration(message.text) # По айди чата вызываем функцию регистрации
        bot.send_message(message.chat.id, current_bot_message)
        if current_bot_message == 'Отлично! Регистрация завершена': # Если пользователь завершил регистрацию - меняем статус на сбор интересов
            states[message.chat.id] = 'on_interest_survey'
            bot.send_message(message.chat.id, 'Теперь давайте поговорим о ваших интересах! Вы можете нажать '
                                              '"пропустить" '
                                              'и заполнить эту информацию позже в профиле.')
            interests[message.chat.id] = []
            interests[message.chat.id].append(InterestsHandler())
            current_bot_message = interests[message.chat.id][len(interests[message.chat.id]) - 1].interest_survey('') # Для каждого айди создаем массив интересов, после добавленя бд - переписать
            bot.send_message(message.chat.id, current_bot_message)
    elif states[message.chat.id] == 'on_interest_survey': # по айди чата вызываем функцию добавления интереса
        current_bot_message = interests[message.chat.id][len(interests[message.chat.id]) - 1].interest_survey(
            message.text)
        bot.send_message(message.chat.id, current_bot_message)
        if current_bot_message == 'Отлично! Фильтр объявлений добавлен. Желаете создать еще один?':
            states[message.chat.id] = 'can_end_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Да' or message.text == 'да'):
        interests[message.chat.id].append(InterestsHandler())
        current_bot_message = interests[message.chat.id][len(interests[message.chat.id]) - 1].interest_survey('')
        bot.send_message(message.chat.id, current_bot_message)
        states[message.chat.id] = 'on_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Нет' or message.text == 'нет'):
        states[message.chat.id] = 'on_main_menu'
    elif states[message.chat.id] == 'on_adding_items':
        current_bot_message = items[message.chat.id][len(items[message.chat.id]) - 1].create_item(message.text)
        bot.send_message(message.chat.id, current_bot_message)
        if items[message.chat.id][len(items[message.chat.id]) - 1].currentState == 'check':
            current_bot_message = items[message.chat.id][len(items[message.chat.id]) - 1].create_item(message.text)
            bot.send_message(message.chat.id, current_bot_message, reply_markup=remove_button_brand()) # сам вывод сообщения
            items[message.chat.id][len(items[message.chat.id]) - 1].create_item(message.text) # проблема в том что пропускает заполнение референса
        else: # идем дальше по заполнению item
            current_bot_message = items[message.chat.id][len(items[message.chat.id]) - 1].create_item(message.text)
            bot.send_message(message.chat.id, current_bot_message)
    else:
        bot.reply_to(message, states[message.chat.id])


asyncio.run(bot.polling())
