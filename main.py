import telebot
from apscheduler.triggers.date import DateTrigger

from handlers.registration_handler import RegistrationHandler
from handlers.interests_handler import InterestsHandler
from handlers.item_handler import NewItem
from handlers.auction_handler import AuctionHandler

import asyncio
from telebot import types
from utility.utility import *
from db.db_models import *
from apscheduler.schedulers.asyncio import AsyncIOScheduler

bot = telebot.TeleBot("6885951107:AAH6BJaLwZmO5L4Scf6F3IEt_Wdvdbm3nDk")
scheduler = AsyncIOScheduler()

states = {}
reg_handlers = {}
interests = {}
items = {}
messages_to_delete = {}
auction_handler = {}
moderator_id = 436911675
going_auctions = {}
auction_messages = {}
minutes_to_end = 59


def end_auction(auction_id):
    buyers = get_auction_buyers(auction_id)
    auction = get_auction(auction_id)
    for buyer in buyers:
        if buyer.id == auction.winner_id:
            send_and_save(buyer.id,
                          f'Вы выиграли аукцион! Ваша ставка {get_max_bid(auction_id).amount}. Для оплаты и получения свяжитесь с {auction.owner_id}')
        elif buyer.id == auction.owner_id:
            send_and_save(buyer.id,
                          f'Вам аукцион завершен, победная ставка {get_max_bid(auction_id).amount}. Для получения оплаты и отправки свяжитесь с {auction.winner_id}')
        else:
            send_and_save(buyer.id,
                          f'Вам не удалось выиграть аукцион, победная ставка {get_max_bid(auction_id).amount}.')


def start_auction(auction_id):
    update_auction_state(auction_id, 'going')
    print(f'Auction {auction_id} has been started!')
    print(get_auction(auction_id).state)


def give_state_to_all_registered_users():
    users = get_all_users()
    for user in users:
        states[user.id] = 'on_main_menu'
        messages_to_delete[user.id] = []


give_state_to_all_registered_users()


def clear_chat(chat_id):
    for m_id in messages_to_delete[chat_id]:
        try:
            bot.delete_message(chat_id=chat_id, message_id=m_id)
        except:
            pass
    messages_to_delete[chat_id].clear()


def send_and_save(m_id, text):
    res = bot.send_message(m_id, text)
    if messages_to_delete[m_id] is None:
        messages_to_delete[m_id] = []
    messages_to_delete[m_id].append(res.id)


def send_and_save_with_markup(m_id, text, markup):
    res = bot.send_message(m_id, text, reply_markup=markup)
    if messages_to_delete[m_id] is None:
        messages_to_delete[m_id] = []
    messages_to_delete[m_id].append(res.id)


def create_button_to_part_in_auction(auction_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Участвовать', callback_data='participate_' + str(auction_id)))
    return markup


def send_notifications_about_auction(auction_id):
    interests = get_interests_for_auction(auction_id)
    already_sent = []
    for interest in interests:
        if interest.owner_id not in already_sent:
            send_and_save_with_markup(interest.owner_id,
                                      'Новый аукцион для вас!\n' + create_auction_message(get_auction(auction_id)),
                                      create_button_to_part_in_auction(auction_id))
            already_sent.append(interest.owner_id)


def send_auction_to_moderation(auction_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Принять', callback_data='accept_' + str(auction_id)))
    markup.add(types.InlineKeyboardButton('Отклонить', callback_data='decline_' + str(auction_id)))
    send_and_save_with_markup(moderator_id, create_auction_message(get_auction(auction_id)), markup)


def get_auctions_for_filter(interest):
    auctions_id = get_auctions_for_interest(interest)
    for id in auctions_id:
        send_and_save_with_markup(interest.owner_id, create_auction_message(get_auction(id)),
                                  create_button_to_part_in_auction(id))


# Обрабатываем команду start, если пользователя нет в бд, начинаем процесс регистрации, создавая соответствующий хэндлер
# и обновляя текущий статус пользователя
@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    if message.chat.id not in states:
        messages_to_delete[message.chat.id] = []
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'notRegistered'
        reg_handlers[message.chat.id] = RegistrationHandler()
        send_and_save(message.chat.id, 'Добро пожаловать! Давайте Вас зарегистрируем.')
        send_and_save(message.chat.id, reg_handlers[message.chat.id].do_registration(''))
    else:
        pass
        # вывод приветственного сообщения


@bot.message_handler(commands=['add_interest'])
def add_interest(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        states[message.chat.id] = 'on_interest_survey'
        interests[message.chat.id] = InterestsHandler()
        current_bot_message = interests[message.chat.id].interest_survey('')
        send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    else:
        send_and_save(message.chat.id, 'Сперва необходимо завершить регистрацию')


# Обрабатываем команду profile, выводим информацию о профиле отправившего команду
@bot.message_handler(commands=['profile'])
def open_profile(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        user = get_user_info(message.chat.id)
        current_bot_message = create_user_info_message(user)
        send_and_save(message.chat.id, current_bot_message)
    else:
        send_and_save(message.chat.id, 'Вы еще не зарегистрированы')


@bot.message_handler(commands=['coming_auctions'])
def open_coming_auctions(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    auctions = get_coming_auctions(message.chat.id)
    for au in auctions:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Автоставка', callback_data='auto_bid_' + str(au.id)))
        if au.start_date <= datetime.now() <= au.duration:
            markup.add(types.InlineKeyboardButton('Перейти', callback_data='open_auction_' + str(au.id)))
        send_and_save_with_markup(message.chat.id, create_auction_message(au), markup)


# Отправляем отдельными сообщениями все интересы данного пользователя
@bot.message_handler(commands=['interests'])
def open_interests(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        user_interests = get_interests(message.chat.id)
        if user_interests.first() is not None:
            send_and_save(message.chat.id, 'Список ваших фильтров:')
            for interest in user_interests:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(types.InlineKeyboardButton('Удалить', callback_data='interest_' + str(interest.id)))
                send_and_save_with_markup(message.chat.id, create_interest_message(interest), markup)
        else:
            send_and_save(message.chat.id,
                          'У вас нет ни одного фильтра. Чтобы добавить, используйте команду /add_interest')
    else:
        send_and_save(message.chat.id, 'Необходимо зарегестрироваться и указать интересы')


@bot.message_handler(commands=['items'])
def open_items(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        user_items = get_items(message.chat.id)
        if user_items.first() is not None:
            send_and_save(message.chat.id, 'Список ваших предметов:')
            for item in user_items:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton('Создать аукцион', callback_data='create_auction_' + str(item.id)))
                msges = bot.send_media_group(message.chat.id, create_photos_for_item(item))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                print(photos_ids)
                markup.add(types.InlineKeyboardButton('Удалить', callback_data='item_' + str(item.id) + photos_ids))
                send_and_save_with_markup(message.chat.id, create_item_text(item), markup)
        else:
            send_and_save(message.chat.id,
                          'У вас нет ни одного предмета в профиле. Чтобы добавить, используйте команду /add_item')
    else:
        send_and_save(message.chat.id, 'Необходимо зарегестрироваться и добавить предметы интересы')


@bot.message_handler(commands=['add_item'])
def add_item(message):
    clear_chat(message.chat.id)
    messages_to_delete[message.chat.id].append(message.id)
    if message.chat.id in states and states[message.chat.id] != 'notRegistered':
        states[message.chat.id] = 'on_adding_items'
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    else:
        send_and_save(message.chat.id, 'Сперва необходимо завершить регистрацию')


def create_brand_buttons():
    markup = types.InlineKeyboardMarkup(row_width=3)
    for brand in all_brands:
        markup.add(types.InlineKeyboardButton(brand, callback_data=brand))
    markup.add(types.InlineKeyboardButton('Остальное', callback_data='open_other_brands'))
    return markup


def create_additional_brands():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for brand in other_brands:
        markup.add(types.InlineKeyboardButton(brand, callback_data=brand))
    markup.add(types.InlineKeyboardButton('Назад', callback_data='open_main_brands'))
    return markup


@bot.callback_query_handler(func=lambda call: True)
def brand_buttons_action(call):
    if call.message:
        if (call.data in all_brands or call.data in other_brands) and states[
            call.message.chat.id] == 'on_interest_survey':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text='Вы выбрали: ' + call.data)
            send_and_save(call.message.chat.id, interests[call.message.chat.id].interest_survey(call.data))
        elif (call.data in all_brands or call.data in other_brands) and states[
            call.message.chat.id] == 'on_adding_items':
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text='Вы выбрали: ' + call.data)
            send_and_save(call.message.chat.id,
                          items[call.message.chat.id].create_item(call.data))
        elif call.data.find('interest') != -1:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            delete_interest(call.data.split('_')[1])
        elif call.data.find('item') != -1:
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            ids = call.data.split('_')[2:]
            for ph_id in ids:
                bot.delete_message(chat_id=call.message.chat.id, message_id=ph_id)
            delete_item(call.data.split('_')[1])
            # Удаление фото!!!
        elif call.data.find("open_other_brands") != -1:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=call.message.text,
                                  reply_markup=create_additional_brands())
        elif call.data.find('open_main_brands') != -1:
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=call.message.text,
                                  reply_markup=create_brand_buttons())
        elif call.data.find('create_auction_') != -1:
            auction_handler[call.message.chat.id] = AuctionHandler()
            auction_handler[call.message.chat.id].item_id = int(call.data.split('_')[2])
            send_and_save(call.message.chat.id, "Давайте создадим аукцион!")
            send_and_save(call.message.chat.id, auction_handler[call.message.chat.id].create_auction(''))
            states[call.message.chat.id] = 'creating_auction'
        elif call.data.find('accept') != -1:
            auction_id = call.data.split('_')[1]
            auction = get_auction(auction_id)
            update_auction_state(auction_id, 'active')
            send_and_save(auction.owner_id,
                          'Ваш аукцион был опубликован! Опубликованные аукционы можно посмотреть по команде ')
            send_notifications_about_auction(auction_id)
            scheduler.add_job(start_auction, 'date', run_date=auction.start_date, args=[auction_id],
                              id='start_auction_' + str(auction_id))
            scheduler.add_job(end_auction, 'date', run_date=get_auction(auction_id).duration, args=[auction_id],
                              id='end_auction_' + str(auction_id))
            scheduler.print_jobs()
        elif call.data.find('participate') != -1:
            save_buyer(call.data.split('_')[1], call.message.chat.id)
            send_and_save(call.message.chat.id,
                          'Вы стали участником аукциона! Просмотреть приближающиеся аукционы можно командой /coming_auctions')
        elif call.data.find('open_auction') != -1:
            auction_id = call.data.split('_')[2]
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                  text=call.message.text + '\n Текущая ставка: ' + str(get_max_bid(auction_id).amount))
            going_auctions[call.message.chat.id] = auction_id
            if auction_id not in auction_messages:
                auction_messages[auction_id] = []
            auction_messages[auction_id].append(call.message)
            states[call.message.chat.id] = 'on_auction_' + str(auction_id)


def create_yes_or_no_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    yes = types.KeyboardButton('Да')
    no = types.KeyboardButton('Нет')
    markup.add(yes, no)
    return markup


def save_photos_to_folder(info_list, item_id):
    counter = 0
    item_photos = []
    for info in info_list:
        d_f = bot.download_file(info.file_path)
        path = f"photos/image{item_id}_{counter}.jpg"
        with open(path, 'wb') as new_file:
            new_file.write(d_f)
            counter += 1
        item_photos.append(path)
    return item_photos


# вынести часть создания бренда (сообщение) в add_item, туда прикрепить кнопки, и вынести вывод последнего сообщения, на прикрепить удаление клавиатуры
def create_user(user_id):
    hl = reg_handlers[user_id]
    return User(id=user_id, username=hl.name + ' ' + hl.surname, company_name=hl.company_name,
                company_website=hl.website, phone=hl.phone)


def create_photo(name, id):
    return Photo(name=name, item_id=id)


def create_interest(user_id):
    hl = interests[user_id]
    return Interest(owner_id=user_id, brand=hl.brand, min_price=hl.minPrice, max_price=hl.maxPrice)


def create_item(user_id):
    hl = items[user_id]
    return Item(brand=hl.brand, reference=hl.reference, price=hl.price, box_available=hl.box_available,
                document_available=hl.document_available, comments=hl.comments, owner_id=user_id)


def create_auction(user_id):
    hl = auction_handler[user_id]
    return Auction(bid_step=hl.bid_step, start_date=hl.start_date_time, duration=hl.end_date_time, item_id=hl.item_id,
                   owner_id=user_id, state='on_moderation')


def create_bid(amount, user_id, auction_id):
    return Bid(amount=amount, time=datetime.now(), bidder_id=user_id, auction_id=auction_id)


@bot.message_handler(content_types=['photo'])
def get_item_photos(message):
    messages_to_delete[message.chat.id].append(message.id)
    if states[message.chat.id] == 'on_adding_items':
        if items[message.chat.id].currentState == 'getDocument_available' or items[
            message.chat.id].currentState == 'getBox_available':
            if len(items[message.chat.id].photos) == 0:
                send_and_save(message.chat.id, items[message.chat.id].create_item(''))
            f_id = message.photo[-1].file_id
            file_info = bot.get_file(f_id)
            items[message.chat.id].append_photo(file_info)
        else:
            send_and_save(message.chat.id, 'Фото необходимо прикрепить на соответствующем этапе')
            print(items[message.chat.id].currentState)
    else:
        send_and_save(message.chat.id, 'Фото необходимо отправлять во время добавления предмета в профиль')


# Обработка всех текстовых сообщений, которые не являются командами
@bot.message_handler(func=lambda message: True)
def handle_request(message):
    messages_to_delete[message.chat.id].append(message.id)
    if states[
        message.chat.id] == 'notRegistered':  # Данный статус только в том случае, если человек не завершил регистрацию и зашел в бота впервые
        current_bot_message = reg_handlers[message.chat.id].do_registration(
            message.text)  # По айди чата вызываем функцию регистрации
        if current_bot_message.find('верно') != -1:
            send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
        if current_bot_message == 'Отлично! Регистрация завершена':  # Если пользователь завершил регистрацию - меняем статус на сбор интересов
            save_user(create_user(message.chat.id))
            clear_chat(message.chat.id)
            states[message.chat.id] = 'on_interest_survey'
            send_and_save_with_markup(message.chat.id, 'Теперь давайте поговорим о ваших интересах! Вы можете нажать '
                                                       '"пропустить" '
                                                       'и заполнить эту информацию позже в профиле.',
                                      telebot.types.ReplyKeyboardRemove())
            interests[message.chat.id] = InterestsHandler()
            current_bot_message = interests[message.chat.id].interest_survey(
                '')  # Для каждого айди создаем массив интересов, после добавленя бд - переписать
            send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    elif states[message.chat.id] == 'on_interest_survey':  # по айди чата вызываем функцию добавления интереса
        current_bot_message = interests[message.chat.id].interest_survey(message.text)
        if interests[message.chat.id].currentState == 'getMinPrice':
            send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        elif current_bot_message.find('верно') != -1:
            send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
        if current_bot_message == 'Отлично! Фильтр объявлений добавлен. Желаете создать еще один?':
            save_interest(create_interest(message.chat.id))
            states[message.chat.id] = 'can_end_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Да' or message.text == 'да'):
        clear_chat(message.chat.id)
        interests[message.chat.id] = InterestsHandler()
        current_bot_message = interests[message.chat.id].interest_survey('')
        send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        states[message.chat.id] = 'on_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Нет' or message.text == 'нет'):
        clear_chat(message.chat.id)
        states[message.chat.id] = 'on_main_menu'
    elif states[message.chat.id] == 'on_adding_items':
        if items[message.chat.id].currentState != 'getBox_available':
            current_bot_message = items[message.chat.id].create_item(message.text)
            if current_bot_message.find('коробка') != -1 or current_bot_message.find(
                    'Документы') != -1 or current_bot_message.find('Необходимо') != -1:
                send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
            else:
                send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
            if current_bot_message == 'Отлично! Предмет добавлен. Желаете добавить еще один?':
                new_item_id = save_item(create_item(message.chat.id))
                names = save_photos_to_folder(items[message.chat.id].photos, new_item_id)
                for name in names:
                    save_photo(create_photo(name, new_item_id))
                states[message.chat.id] = 'can_end_item_survey'
        else:
            send_and_save(message.chat.id, 'Необходимо прикрепить хотя бы одно фото')
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Да' or message.text == 'да'):
        clear_chat(message.chat.id)
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        states[message.chat.id] = 'on_item_survey'
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Нет' or message.text == 'нет'):
        clear_chat(message.chat.id)
        states[message.chat.id] = 'on_main_menu'
    elif states[message.chat.id] == 'creating_auction':
        current_bot_message = auction_handler[message.chat.id].create_auction(message.text)
        if auction_handler[message.chat.id].currentState == 'end':
            msg = "Предмет: \n" + create_item_text(
                get_item(auction_handler[message.chat.id].item_id)) + 'Аукцион:\n' + current_bot_message
            send_and_save_with_markup(message.chat.id, msg, create_yes_or_no_button())
        else:
            send_and_save(message.chat.id, current_bot_message)
        if current_bot_message == 'Отлично! Аукцион создан и отправлен на модерацию':
            states[message.chat.id] = 'on_main_menu'
            new_auction_id = save_auction(create_auction(message.chat.id))
            auction = get_auction(new_auction_id)
            save_bid(
                create_bid(get_item(auction_handler[message.chat.id].item_id).price, message.chat.id, new_auction_id))
            send_auction_to_moderation(new_auction_id)
    elif states[message.chat.id].find('on_auction') != -1:
        if is_positive_number(message.text):
            auction_id = states[message.chat.id].split('_')[2]
            current_bid = get_max_bid(auction_id).amount
            if int(message.text) - current_bid >= get_auction(auction_id).bid_step:
                save_bid(create_bid(int(message.text), message.chat.id, auction_id))
                delta = get_auction(auction_id).duration - datetime.now()
                if delta.total_seconds() // 60 <= minutes_to_end:
                    print(delta.total_seconds() // 60)
                    update_auction_time(auction_id, 2)
                    print(get_auction(auction_id).duration)
                    scheduler.print_jobs()
                    scheduler.reschedule_job('end_auction_' + str(auction_id), 'date', run_date=get_auction(auction_id).duration)
                    scheduler.print_jobs()
                for m in auction_messages[auction_id]:
                    try:
                        bot.edit_message_text(chat_id=m.chat.id, message_id=m.id,
                                              text=m.text + '\n Текущая ставка: ' + str(get_max_bid(auction_id).amount))
                    except:
                        print("MESSAGE WAS NOT FOUND")
            else:
                send_and_save(message.chat.id, 'Ставка должна превышать текущую минимум на шаг аукциона')
        else:
            send_and_save(message.chat.id, 'Необходимо указать целую ставку - количество долларов')
    else:
        bot.reply_to(message, states[message.chat.id])


scheduler.start()
bot.polling()
