from datetime import timedelta
from handlers.registration_handler import RegistrationHandler
from handlers.interests_handler import InterestsHandler
from handlers.item_handler import NewItem
from handlers.auction_handler import AuctionHandler
from telebot.async_telebot import AsyncTeleBot
import aioschedule as schedule
import asyncio
from utility.utility import *
from db.db_models import *

bot = AsyncTeleBot("6885951107:AAH6BJaLwZmO5L4Scf6F3IEt_Wdvdbm3nDk")

states = {}
reg_handlers = {}
interests = {}
items = {}
messages_to_delete = {}
auction_handler = {}
moderator_id = 436911675
going_auctions = {}
auction_messages = {}
minutes_to_end = 1


async def end_auction(auction_id):
    buyers = get_auction_buyers(auction_id)
    auction = get_auction(auction_id)
    item = get_item(auction.item_id)
    update_auction_state(auction_id, 'finished')
    if get_max_bid(auction_id) == item.price:
        await send_and_save(item.owner_id, 'К сожалению, аукцион не состоялся, ни один пользователь не сделал ставку.')
        return
    for buyer in buyers:
        if buyer.buyer_id == auction.winner_id:
            await send_and_save(buyer.buyer_id,
                                f'Вы выиграли аукцион! Ваша ставка {get_max_bid(auction_id).amount}. Для оплаты и получения свяжитесь с @{get_user_info(auction.owner_id).nick}')
        if buyer.buyer_id == auction.owner_id:
            await send_and_save(buyer.buyer_id,
                                f'Ваш аукцион завершен, победная ставка {get_max_bid(auction_id).amount}. Для получения оплаты и отправки свяжитесь с @{get_user_info(auction.winner_id).nick}')
        if buyer.buyer_id != auction.winner_id and buyer.buyer_id != auction.owner_id:
            await send_and_save(buyer.buyer_id,
                                f'Вам не удалось выиграть аукцион, победная ставка {get_max_bid(auction_id).amount}.')
    schedule.clear('end_auction_' + str(auction_id))


async def create_end_auction_task(auction_id):
    time = str(get_auction(auction_id).duration.time())[:-3]
    schedule.every().day.at(time).do(end_auction, auction_id).tag('end_auction_' + str(auction_id))


async def create_autobids_task(auction_id):
    time = str((get_auction(auction_id).duration - timedelta(minutes=1)).time())[:-3]
    schedule.every().day.at(time).do(use_auto_bids, auction_id).tag('auto_bids_' + str(auction_id))


async def start_auction(auction_id):
    update_auction_state(auction_id, 'going')
    print(f'Auction {auction_id} has been started!')
    print(get_auction(auction_id).state)
    schedule.clear('start_auction_' + str(auction_id))
    await create_end_auction_task(auction_id)
    await create_autobids_task(auction_id)


async def use_auto_bids(auction_id):
    get_valid_auto_bids(auction_id)
    schedule.clear('auto_bids_' + str(auction_id))


def give_state_to_all_registered_users():
    users = get_all_users()
    for user in users:
        states[user.id] = 'on_main_menu'
        messages_to_delete[user.id] = []


def start_schedule_for_all_auctions():
    auctions = get_all_not_finished_auctions()
    for auction in auctions:
        if auction.state == 'going':
            update_auction_state(auction.id, 'finished')
        elif auction.state == 'active':
            time = str(auction.start_date.time())[:-3]
            schedule.every().day.at(time).do(start_auction, auction.id).tag('start_auction_' + str(auction.id))


give_state_to_all_registered_users()
start_schedule_for_all_auctions()


async def clear_chat(chat_id):
    for m_id in messages_to_delete[chat_id]:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=m_id)
        except:
            pass
    messages_to_delete[chat_id].clear()


async def send_and_save(m_id, text):
    res = await bot.send_message(m_id, text)
    if messages_to_delete[m_id] is None:
        messages_to_delete[m_id] = []
    messages_to_delete[m_id].append(res.id)
    return res


async def send_and_save_with_markup(m_id, text, markup):
    res = await bot.send_message(m_id, text, reply_markup=markup)
    if messages_to_delete[m_id] is None:
        messages_to_delete[m_id] = []
    messages_to_delete[m_id].append(res.id)


def create_button_to_part_in_auction(auction_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Участвовать', callback_data='participate_' + str(auction_id)))
    return markup


async def send_notifications_about_auction(auction_id):
    interests = get_interests_for_auction(auction_id)
    already_sent = []
    for interest in interests:
        if interest.owner_id not in already_sent:
            await send_and_save_with_markup(interest.owner_id,
                                            'Новый аукцион для вас!\n' + create_auction_message(
                                                get_auction(auction_id)),
                                            create_button_to_part_in_auction(auction_id))
            already_sent.append(interest.owner_id)


async def send_auction_to_moderation(auction_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Принять', callback_data='accept_' + str(auction_id)))
    markup.add(types.InlineKeyboardButton('Отклонить', callback_data='decline_' + str(auction_id)))
    await send_and_save_with_markup(moderator_id, create_auction_message(get_auction(auction_id)), markup)


async def get_auctions_for_filter(interest):
    auctions_id = get_auctions_for_interest(interest)
    for id in auctions_id:
        await send_and_save_with_markup(interest.owner_id, create_auction_message(get_auction(id)),
                                        create_button_to_part_in_auction(id))


# Обрабатываем команду start, если пользователя нет в бд, начинаем процесс регистрации, создавая соответствующий хэндлер
# и обновляя текущий статус пользователя
@bot.message_handler(commands=['start'])
async def send_welcome_message(message):
    if message.chat.id not in states:
        messages_to_delete[message.chat.id] = []
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'notRegistered'
        reg_handlers[message.chat.id] = RegistrationHandler()
        await send_and_save(message.chat.id, 'Добро пожаловать! Давайте Вас зарегистрируем.')
        await send_and_save(message.chat.id, reg_handlers[message.chat.id].do_registration(''))
    else:
        await send_and_save(message.chat.id, main_menu_message)
        # вывод приветственного сообщения


@bot.message_handler(commands=['add_interest'])
async def add_interest(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'on_interest_survey'
        interests[message.chat.id] = InterestsHandler()
        current_bot_message = interests[message.chat.id].interest_survey('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


# Обрабатываем команду profile, выводим информацию о профиле отправившего команду
@bot.message_handler(commands=['profile'])
async def open_profile(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        user = get_user_info(message.chat.id)
        current_bot_message = create_user_info_message(user)
        await send_and_save(message.chat.id, current_bot_message)
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только после регистрации, находясь в главном меню.')


@bot.message_handler(commands=['coming_auctions'])
async def open_coming_auctions(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        auctions = get_coming_auctions(message.chat.id)
        if len(auctions) > 0:
            for au in auctions:
                markup = types.InlineKeyboardMarkup()
                if get_auto_bid(message.chat.id, au.id) is None:
                    markup.add(types.InlineKeyboardButton('Автоставка', callback_data='create_auto_bid_' + str(au.id)))
                if au.state == 'going':
                    markup.add(types.InlineKeyboardButton('Перейти', callback_data='open_auction_' + str(au.id)))
                msges = await bot.send_media_group(message.chat.id, create_photos_for_item(get_item(au.item_id)))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                    messages_to_delete[message.chat.id].append(msg.id)
                await send_and_save_with_markup(message.chat.id, create_auction_message(au), markup)
                is_changeable = True
                if (au.duration - datetime.now()).total_seconds() // 60 <= minutes_to_end:
                    is_changeable = False
                await create_and_send_auto_bid_message(message.chat.id, au.id, is_changeable)
        else:
            await send_and_save(message.chat.id, 'Вы не участвуете ни в одном активном аукционе. Чтобы просмотреть доступные аукционы, используйте команду /all_auctions')
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


@bot.message_handler(commands=['all_auctions'])
async def open_coming_auctions(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        au_ids = get_auction_to_participate(message.chat.id)
        if len(au_ids) > 0:
            for id in au_ids:
                auction = get_auction(id)
                msges = await bot.send_media_group(message.chat.id, create_photos_for_item(get_item(auction.item_id)))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                    messages_to_delete[message.chat.id].append(msg.id)
                await send_and_save_with_markup(message.chat.id, create_auction_message(auction), create_button_to_part_in_auction(id))
        else:
            await send_and_save(message.chat.id, 'На данный момент нет доступных аукционов для участия')
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


# Отправляем отдельными сообщениями все интересы данного пользователя
@bot.message_handler(commands=['interests'])
async def open_interests(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        user_interests = get_interests(message.chat.id)
        if user_interests.first() is not None:
            for interest in user_interests:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(types.InlineKeyboardButton('Удалить', callback_data='interest_' + str(interest.id)))
                await send_and_save_with_markup(message.chat.id, create_interest_message(interest), markup)
        else:
            await send_and_save(message.chat.id,
                                'У вас нет ни одного фильтра. Чтобы добавить, используйте команду /add_interest')
            await send_and_save(message.chat.id, main_menu_message)
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


@bot.message_handler(commands=['items'])
async def open_items(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        user_items = get_items(message.chat.id)
        if user_items.first() is not None:
            for item in user_items:
                markup = types.InlineKeyboardMarkup(row_width=1)
                markup.add(
                    types.InlineKeyboardButton('Создать аукцион', callback_data='create_auction_' + str(item.id)))
                msges = await bot.send_media_group(message.chat.id, create_photos_for_item(item))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                    messages_to_delete[message.chat.id].append(msg.id)
                print(photos_ids)
                markup.add(types.InlineKeyboardButton('Удалить', callback_data='item_' + str(item.id) + photos_ids))
                await send_and_save_with_markup(message.chat.id, create_item_text(item), markup)
        else:
            await send_and_save(message.chat.id,
                                'У вас нет ни одного предмета в профиле. Чтобы добавить, используйте команду /add_item')
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


@bot.message_handler(commands=['add_item'])
async def add_item(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'on_adding_items'
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    else:
        await send_and_save(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.')


async def create_and_send_auto_bid_message(chat_id, auction_id, is_changable):
    auto_bid = get_auto_bid(chat_id, auction_id)
    if auto_bid is not None:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Изменить', callback_data='change_auto_bid_' + str(auto_bid.id)))
        markup.add(types.InlineKeyboardButton('Удалить', callback_data='delete_auto_bid_' + str(auto_bid.id)))
        text = f'Автоставка: {auto_bid.amount}'
        if is_changable:
            await send_and_save_with_markup(chat_id, text, markup)
        else:
            await send_and_save(chat_id, text)
    else:
        return


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


def create_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Назад', callback_data='back'))
    return markup


@bot.callback_query_handler(func=lambda call: True)
async def brand_buttons_action(call):
    if call.message:
        if (call.data in all_brands or call.data in other_brands) and states[
            call.message.chat.id] == 'on_interest_survey':
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='Вы выбрали: ' + call.data)
            await send_and_save(call.message.chat.id, interests[call.message.chat.id].interest_survey(call.data))
        elif (call.data in all_brands or call.data in other_brands) and states[
            call.message.chat.id] == 'on_adding_items':
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='Вы выбрали: ' + call.data)
            await send_and_save(call.message.chat.id, items[call.message.chat.id].create_item(call.data))
        elif call.data.find('interest') != -1:
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            delete_interest(call.data.split('_')[1])
        elif call.data.find('item') != -1:
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            ids = call.data.split('_')[2:]
            for ph_id in ids:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=ph_id)
            delete_item(call.data.split('_')[1])
            # Удаление фото!!!
        elif call.data.find("open_other_brands") != -1:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text,
                                        reply_markup=create_additional_brands())
        elif call.data.find('open_main_brands') != -1:
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text,
                                        reply_markup=create_brand_buttons())
        elif call.data.find('create_auction_') != -1:
            auction_handler[call.message.chat.id] = AuctionHandler()
            auction_handler[call.message.chat.id].item_id = int(call.data.split('_')[2])
            await send_and_save(call.message.chat.id, "Давайте создадим аукцион!")
            await send_and_save(call.message.chat.id, auction_handler[call.message.chat.id].create_auction(''))
            states[call.message.chat.id] = 'creating_auction'
        elif call.data.find('accept') != -1:
            auction_id = call.data.split('_')[1]
            auction = get_auction(auction_id)
            update_auction_state(auction_id, 'active')
            await send_and_save(auction.owner_id,
                                'Ваш аукцион был опубликован! Опубликованные аукционы можно посмотреть по команде /all_auctions')
            await send_notifications_about_auction(auction_id)
            print(str(auction.start_date.time()))
            time = str(auction.start_date.time())[:-3]
            print(time)
            schedule.every().day.at(time).do(start_auction, auction_id).tag(
                'start_auction_' + str(auction_id))
        elif call.data.find('participate') != -1:
            save_buyer(call.data.split('_')[1], call.message.chat.id)
            await send_and_save(call.message.chat.id,
                                'Вы стали участником аукциона! Просмотреть приближающиеся аукционы можно командой /coming_auctions')
        elif call.data.find('open_auction') != -1:
            auction_id = call.data.split('_')[2]
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text + '\nТекущая ставка: ' + str(
                                            get_max_bid(auction_id).amount), reply_markup=create_back_button())
            # msges = await bot.send_media_group(call.message.chat.id, create_photos_for_item(get_item(auction.item_id)))
            # photos_ids = ''
            # for msg in msges:
            #     photos_ids += '_' + str(msg.id)
            #     messages_to_delete[message.chat.id].append(msg.id)
            # await send_and_save_with_markup(message.chat.id, create_auction_message(au), markup)
            # auct_message = await send_and_save(call.message.chat.id, )
            # asd;,as[dk]
            going_auctions[call.message.chat.id] = auction_id
            if auction_id not in auction_messages:
                auction_messages[auction_id] = []
            auction_messages[auction_id].append(call.message)
            states[call.message.chat.id] = 'on_auction_' + str(auction_id)
        elif call.data.find('create_auto_bid_') != -1:
            auction_id = call.data.split('_')[3]
            states[call.message.chat.id] = 'creating_auto_bid_' + str(auction_id)
            await send_and_save(call.message.chat.id, 'Введите сумму автоставки:')
        elif call.data.find('change_auto_bid') != -1:
            auto_bid_id = call.data.split('_')[3]
            states[call.message.chat.id] = 'changing_auto_bid_' + auto_bid_id
            await send_and_save(call.message.chat.id, 'Введите новую сумму автоставки:')
        elif call.data.find('delete_auto_bid') != -1:
            auto_bid_id = int(call.data.split('_')[3])
            await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
            delete_auto_bid(auto_bid_id)
        elif call.data.find('back') != -1:
            states[call.message.chat.id] = 'on_main_menu'
            await clear_chat(call.message.chat.id)
            await send_and_save(call.message.chat.id, main_menu_message)


def create_yes_or_no_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    yes = types.KeyboardButton('Да')
    no = types.KeyboardButton('Нет')
    markup.add(yes, no)
    return markup


def create_skip_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Пропустить'))
    return markup


async def save_photos_to_folder(info_list, item_id):
    counter = 0
    item_photos = []
    for info in info_list:
        d_f = await bot.download_file(info.file_path)
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
                company_website=hl.website, phone=hl.phone, nick=hl.nick)


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


def create_auto_bid(amount, user_id, auction_id):
    return AutoBid(amount=amount, bid_time=datetime.now(), bidder_id=user_id, auction_id=auction_id)


@bot.message_handler(content_types=['photo'])
async def get_item_photos(message):
    messages_to_delete[message.chat.id].append(message.id)
    if states[message.chat.id] == 'on_adding_items':
        if items[message.chat.id].currentState == 'getDocument_available' or items[
            message.chat.id].currentState == 'getBox_available':
            if len(items[message.chat.id].photos) == 0:
                await send_and_save(message.chat.id, items[message.chat.id].create_item(''))
            f_id = message.photo[-1].file_id
            file_info = await bot.get_file(f_id)
            items[message.chat.id].append_photo(file_info)
        else:
            await send_and_save(message.chat.id, 'Фото необходимо прикрепить на соответствующем этапе')
            print(items[message.chat.id].currentState)
    else:
        await send_and_save(message.chat.id, 'Фото необходимо отправлять во время добавления предмета в профиль')


# Обработка всех текстовых сообщений, которые не являются командами
@bot.message_handler(func=lambda message: True)
async def handle_request(message):
    messages_to_delete[message.chat.id].append(message.id)
    if message.text == 'Назад':
        states[message.chat.id] = 'on_main_menu'
        await clear_chat(message.chat.id)
        await send_and_save(message.chat.id, main_menu_message)
    if states[
        message.chat.id] == 'notRegistered':  # Данный статус только в том случае, если человек не завершил регистрацию и зашел в бота впервые
        current_bot_message = reg_handlers[message.chat.id].do_registration(
            message.text)  # По айди чата вызываем функцию регистрации
        if current_bot_message.find('верно') != -1:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            await send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
        if current_bot_message == 'Отлично! Регистрация завершена':  # Если пользователь завершил регистрацию - меняем статус на сбор интересов
            reg_handlers[message.chat.id].nick = message.from_user.username
            print(message.from_user.username)
            save_user(create_user(message.chat.id))
            await clear_chat(message.chat.id)
            states[message.chat.id] = 'on_interest_survey'
            await send_and_save_with_markup(message.chat.id,
                                            'Теперь давайте поговорим о ваших интересах! Вы можете нажать '
                                            '"пропустить" '
                                            'и заполнить эту информацию позже в профиле.',
                                            create_skip_button())
            interests[message.chat.id] = InterestsHandler()
            current_bot_message = interests[message.chat.id].interest_survey(
                '')  # Для каждого айди создаем массив интересов, после добавленя бд - переписать
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    elif states[message.chat.id] == 'on_interest_survey':  # по айди чата вызываем функцию добавления интереса
        if message.text == 'Пропустить':
            states[message.chat.id] = 'on_main_menu'
            await clear_chat(message.chat.id)
            await send_and_save_with_markup(message.chat.id, main_menu_message, telebot.types.ReplyKeyboardRemove())
            return
        current_bot_message = interests[message.chat.id].interest_survey(message.text)
        if interests[message.chat.id].currentState == 'getMinPrice':
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        elif current_bot_message.find('верно') != -1 or current_bot_message.find('Фильтр объявлений добавлен') != -1:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            await send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
        if current_bot_message == 'Отлично! Фильтр объявлений добавлен. Желаете создать еще один?':
            save_interest(create_interest(message.chat.id))
            states[message.chat.id] = 'can_end_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Да' or message.text == 'да'):
        await clear_chat(message.chat.id)
        interests[message.chat.id] = InterestsHandler()
        current_bot_message = interests[message.chat.id].interest_survey('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        states[message.chat.id] = 'on_interest_survey'
    elif states[message.chat.id] == 'can_end_interest_survey' and (message.text == 'Нет' or message.text == 'нет'):
        await clear_chat(message.chat.id)
        states[message.chat.id] = 'on_main_menu'
        await send_and_save(message.chat.id, main_menu_message)
    elif states[message.chat.id] == 'on_adding_items':
        if items[message.chat.id].currentState != 'getBox_available':
            current_bot_message = items[message.chat.id].create_item(message.text)
            if current_bot_message.find('коробка') != -1 or current_bot_message.find(
                    'Документы') != -1 or current_bot_message.find('Необходимо') != -1 or \
                    current_bot_message.find('Желаете добавить еще один') != -1:
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
            else:
                await send_and_save_with_markup(message.chat.id, current_bot_message,
                                                telebot.types.ReplyKeyboardRemove())
            if current_bot_message == 'Отлично! Предмет добавлен. Желаете добавить еще один?':
                new_item_id = save_item(create_item(message.chat.id))
                names = await save_photos_to_folder(items[message.chat.id].photos, new_item_id)
                for name in names:
                    save_photo(create_photo(name, new_item_id))
                states[message.chat.id] = 'can_end_item_survey'
        else:
            await send_and_save(message.chat.id, 'Необходимо прикрепить хотя бы одно фото')
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Да' or message.text == 'да'):
        await clear_chat(message.chat.id)
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        states[message.chat.id] = 'on_item_survey'
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Нет' or message.text == 'нет'):
        await clear_chat(message.chat.id)
        states[message.chat.id] = 'on_main_menu'
        await send_and_save(message.chat.id, main_menu_message)
    elif states[message.chat.id] == 'creating_auction':
        current_bot_message = auction_handler[message.chat.id].create_auction(message.text)
        if auction_handler[message.chat.id].currentState == 'end':
            msg = "Предмет: \n" + create_item_text(
                get_item(auction_handler[message.chat.id].item_id)) + 'Аукцион:\n' + current_bot_message
            await send_and_save_with_markup(message.chat.id, msg, create_yes_or_no_button())
        else:
            await send_and_save(message.chat.id, current_bot_message)
        if current_bot_message == 'Отлично! Аукцион создан и отправлен на модерацию':
            await clear_chat(message.chat.id)
            states[message.chat.id] = 'on_main_menu'
            await send_and_save(message.chat.id, main_menu_message)
            new_auction_id = save_auction(create_auction(message.chat.id))
            auction = get_auction(new_auction_id)
            save_bid(
                create_bid(get_item(auction_handler[message.chat.id].item_id).price, message.chat.id, new_auction_id))
            await send_auction_to_moderation(new_auction_id)
    elif states[message.chat.id].find('on_auction') != -1:
        if is_positive_number(message.text):
            auction_id = states[message.chat.id].split('_')[2]
            auction = get_auction(auction_id)
            current_bid = get_max_bid(auction_id).amount
            if int(message.text) - current_bid >= get_auction(auction_id).bid_step:
                if int(message.text) % get_auction(auction_id).bid_step == 0:
                    flag = False
                    save_bid(create_bid(int(message.text), message.chat.id, auction_id))
                    delta = get_auction(auction_id).duration - datetime.now()
                    if delta.total_seconds() // 60 <= minutes_to_end:
                        print(delta.total_seconds() // 60)
                        update_auction_time(auction_id, 1)
                        print(get_auction(auction_id).duration)
                        schedule.clear('end_auction_' + str(auction_id))
                        schedule.clear('auto_bids_' + str(auction_id))
                        await create_autobids_task(auction_id)
                        await create_end_auction_task(auction_id)
                    previous_winner = auction.winner_id
                    update_winner_id(auction_id, message.chat.id)
                    auction = get_auction(auction_id)
                    for m in auction_messages[auction_id]:
                        try:
                            text = create_auction_message(get_auction(auction_id)) + '\nТекущая ставка: ' + str(get_max_bid(auction_id).amount)
                            if m.chat.id == auction.winner_id:
                                text += '\n\nВы являетесь лидером аукциона'
                            else:
                                text += '\n\nВы не являетесь лидером аукциона'
                            await bot.edit_message_text(chat_id=m.chat.id, message_id=m.id, text=text, reply_markup=create_back_button())
                        except:
                            print("MESSAGE WAS NOT FOUND")
                            if m.chat.id == previous_winner:
                                flag = True
                    if flag:
                        markup = types.InlineKeyboardMarkup()
                        markup.add(types.InlineKeyboardButton('Перейти', callback_data='open_auction_' + str(auction.id)))
                        msges = await bot.send_media_group(previous_winner,
                                                           create_photos_for_item(get_item(auction.item_id)))
                        photos_ids = ''
                        for msg in msges:
                            photos_ids += '_' + str(msg.id)
                            messages_to_delete[message.chat.id].append(msg.id)
                        await send_and_save_with_markup(previous_winner, "ВАШУ СТАВКУ ПЕРЕБИЛИ\n" + create_auction_message(auction), markup)
                else:
                    await send_and_save(message.chat.id, 'Ставка должна быть кратна шагу аукциона')
            else:
                await send_and_save(message.chat.id, 'Ставка должна превышать текущую минимум на шаг аукциона')
        else:
            await send_and_save(message.chat.id, 'Необходимо указать целую ставку - количество долларов')
    elif states[message.chat.id].find('creating_auto_bid_') != -1:
        auction_id = int(states[message.chat.id].split('_')[3])
        auction = get_auction(auction_id)
        if is_positive_number(message.text):
            if int(message.text) >= get_item(auction.item_id).price + auction.bid_step:
                if int(message.text) % auction.bid_step == 0:
                    save_auto_bid(create_auto_bid(int(message.text), message.chat.id, auction_id))
                    states[message.chat.id] = 'on_main_menu'
                    await clear_chat(message.chat.id)
                    await send_and_save(message.chat.id, f'Автоставка успешно добавлена, сумма - {message.text}')
                    await send_and_save(message.chat.id, main_menu_message)
                else:
                    await send_and_save(message.chat.id, 'Сумма автоставки должна быть кратна шагу аукциона')
            else:
                await send_and_save(message.chat.id, 'Сумма ставки должна превышать цену как минимум на шаг аукциона')
        else:
            await send_and_save(message.chat.id, 'Сумма ставки должна быть положительным числом')
    elif states[message.chat.id].find('changing_auto_bid_') != -1:
        auto_bid_id = states[message.chat.id].split('_')[3]
        auto_bid = get_auto_bid_by_id(auto_bid_id)
        auction_id = auto_bid.auction_id
        auction = get_auction(auction_id)
        if is_positive_number(message.text):
            if int(message.text) >= get_item(auction.item_id).price + auction.bid_step:
                if int(message.text) % auction.bid_step == 0:
                    change_auto_bid(auto_bid_id, int(message.text))
                    states[message.chat.id] = 'on_main_menu'
                    await clear_chat(message.chat.id)
                    await send_and_save(message.chat.id, f'Автоставка успешно изменена, сумма - {message.text}')
                    await send_and_save(message.chat.id, main_menu_message)
                else:
                    await send_and_save(message.chat.id, 'Сумма автоставки должна быть кратна шагу аукциона')
            else:
                await send_and_save(message.chat.id, 'Сумма ставки должна превышать цену как минимум на шаг аукциона')
        else:
            await send_and_save(message.chat.id, 'Сумма ставки должна быть положительным числом')
    else:
        await bot.reply_to(message, states[message.chat.id])


async def scheduler():
    while True:
        await schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    await asyncio.gather(bot.infinity_polling(), scheduler())


if __name__ == '__main__':
    asyncio.run(main())
