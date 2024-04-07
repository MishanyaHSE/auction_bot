import calendar
import os
from datetime import timedelta
from handlers.registration_handler import RegistrationHandler
from handlers.interests_handler import InterestsHandler
from handlers.item_handler import NewItem
from handlers.auction_handler import AuctionHandler
from telebot.async_telebot import AsyncTeleBot
import aioschedule as schedule
import asyncio
from dotenv import load_dotenv
from utility.utility import *
from db.db_models import *

load_dotenv()
bot = AsyncTeleBot(os.environ.get('BOT_TKN'))

states = {}
reg_handlers = {}
interests = {}
items = {}
messages_to_delete = {}
auction_handler = {}
moderator_id = int(os.environ.get('MODER_ID'))
going_auctions = {}
auction_messages = {}
MINUTES_TO_ENLARGE = 2
TIME_FOR_AUTO_BIDS = 6
ADDITIONAL_MINUTES = 5


async def end_auction(auction_id):
    update_auction_state(auction_id, 'finished')
    buyers = get_auction_buyers(auction_id)
    auction = get_auction(auction_id)
    item = get_item(auction.item_id)
    if get_max_bid(auction_id).amount == item.price:
        await send_and_save(item.owner_id, 'К сожалению, аукцион не состоялся, ни один пользователь не сделал ставку.')
        return
    else:
        await send_and_save(auction.owner_id,
                            f'Ваш аукцион завершен, победная ставка {get_max_bid(auction_id).amount}. Для получения оплаты и отправки свяжитесь с @{get_user_info(auction.winner_id).nick}')
    for buyer in buyers:
        if buyer.buyer_id == auction.winner_id:
            await send_and_save(buyer.buyer_id,
                                f'Вы выиграли аукцион! Ваша ставка {get_max_bid(auction_id).amount}. Для оплаты и получения свяжитесь с @{get_user_info(auction.owner_id).nick}')
        elif buyer.buyer_id != auction.winner_id and buyer.buyer_id != auction.owner_id:
            await send_and_save(buyer.buyer_id,
                                f'Вам не удалось выиграть аукцион, победная ставка {get_max_bid(auction_id).amount}.')
    schedule.clear('end_auction_' + str(auction_id))


async def create_end_auction_task(auction_id):
    time = str(get_auction(auction_id).duration.time())[:-3]
    schedule.every().day.at(time).do(end_auction, auction_id).tag('end_auction_' + str(auction_id))


async def create_autobids_task(auction_id):
    time = str((get_auction(auction_id).duration - timedelta(minutes=TIME_FOR_AUTO_BIDS)).time())[:-3]
    schedule.every().day.at(time).do(use_auto_bids, auction_id).tag('auto_bids_' + str(auction_id))


async def create_notification_task(auction_id):
    time = str((get_auction(auction_id).duration - timedelta(minutes=5)).time())[:-3]
    schedule.every().day.at(time).do(send_notifications_when_auction_is_ending, auction_id).tag('notifications_' + str(auction_id))



async def start_auction(auction_id):
    update_auction_state(auction_id, 'going')
    au = get_auction(auction_id)
    for buyer in get_auction_buyers(auction_id):
        markup = types.InlineKeyboardMarkup()
        if get_auto_bid(buyer.buyer_id, au.id) is None and (
                au.duration - datetime.now()).total_seconds() // 60 > TIME_FOR_AUTO_BIDS:
            markup.add(types.InlineKeyboardButton('Автоставка', callback_data='create_auto_bid_' + str(au.id)))
        if au.state == 'going':
            markup.add(types.InlineKeyboardButton('Войти в аукцион', callback_data='open_auction_' + str(au.id)))
        msges = await bot.send_media_group(buyer.buyer_id, create_photos_for_item(get_item(au.item_id)))
        photos_ids = ''
        for msg in msges:
            photos_ids += '_' + str(msg.id)
            messages_to_delete[buyer.buyer_id].append(msg.id)
        await send_and_save_with_markup(buyer.buyer_id, 'Аукцион начался!\n' + create_auction_message(au), markup)
        is_changeable = True
        if (au.duration - datetime.now()).total_seconds() // 60 <= TIME_FOR_AUTO_BIDS:
            is_changeable = False
        await create_and_send_auto_bid_message(buyer.buyer_id, au.id, is_changeable)
    schedule.clear('start_auction_' + str(auction_id))
    auction_messages[auction_id] = []
    await create_end_auction_task(auction_id)
    await create_autobids_task(auction_id)
    await send_notifications_when_auction_is_ending(auction_id)


async def unblock_users():
    users = get_all_users()
    for user in users:
        if user.ban is not None and datetime.now() >= user.ban:
            unblock_user(user.id)


# async def update_nicks():


async def use_auto_bids(auction_id):
    result, previous_winner = get_valid_auto_bids(auction_id)
    auction = get_auction(auction_id)
    if result != 0:
        for m in auction_messages[auction_id]:
            try:
                text = create_auction_message(get_auction(auction_id)) + '\nТекущая ставка: ' + '*'+str(
                    get_max_bid(auction_id).amount)+'*'
                if m.chat.id == auction.winner_id:
                    text += '\n\n*Вы являетесь лидером аукциона*'
                else:
                    text += '\n\n*Вы не являетесь лидером аукциона*'
                await bot.edit_message_text(chat_id=m.chat.id, message_id=m.id, text=text,
                                            reply_markup=create_back_button(auction_id), parse_mode="Markdown")
            except:
                print("MESSAGE WAS NOT FOUND")
                if m.chat.id == previous_winner and previous_winner != auction.winner_id:
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Перейти',
                                                          callback_data='open_auction_' + str(auction.id)))
                    msges = await bot.send_media_group(previous_winner,
                                                       create_photos_for_item(get_item(auction.item_id)))
                    photos_ids = ''
                    for msg in msges:
                        photos_ids += '_' + str(msg.id)
                        messages_to_delete[previous_winner].append(msg.id)
                    await send_and_save_with_markup(previous_winner,
                                                    "ВАШУ СТАВКУ ПЕРЕБИЛИ\n" + create_auction_message(
                                                        auction), markup)
                    await send_message_to_all_autobidders(auction_id, auction)
    schedule.clear('auto_bids_' + str(auction_id))
    if get_max_bid(auction_id).amount < get_biggest_auto_bid(auction_id):
        schedule.every(10).seconds.do(use_auto_bids, auction_id).tag('auto_bids_' + str(auction_id))


async def send_message_to_all_autobidders(auction_id, auction):
    ids = get_auto_bidders(auction_id)
    for id in ids:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Перейти',
                                              callback_data='open_auction_' + str(auction_id)))
        msges = await bot.send_media_group(id,
                                           create_photos_for_item(get_item(auction.item_id)))
        photos_ids = ''
        for msg in msges:
            photos_ids += '_' + str(msg.id)
            messages_to_delete[id].append(msg.id)
        await send_and_save_with_markup(id,
                                        "ВАШУ АВТОСТАВКУ ПЕРЕБИЛИ\n" + create_auction_message(
                                            auction), markup)


async def give_state_to_all_registered_users():
    users = get_all_users()
    for user in users:
        states[user.id] = 'on_main_menu'
        messages_to_delete[user.id] = []
        messages_to_delete[moderator_id] = []
        await send_and_save(user.id, main_menu_message(user.id))


def start_schedule_for_all_auctions():
    auctions = get_all_not_finished_auctions()
    for auction in auctions:
        if auction.state == 'going':
            update_auction_state(auction.id, 'finished')
        elif auction.state == 'active':
            time = str(auction.start_date.time())[:-3]
            schedule.every().day.at(time).do(start_auction, auction.id).tag('start_auction_' + str(auction.id))


start_schedule_for_all_auctions()
schedule.every().day.at('00:00').do(unblock_users)


async def clear_chat(chat_id):
    if messages_to_delete[chat_id] is not None:
        for m_id in messages_to_delete[chat_id]:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=m_id)
            except:
                pass
        messages_to_delete[chat_id].clear()


async def send_and_save(m_id, text, parse_mode=None):
    res = await bot.send_message(m_id, text, parse_mode=parse_mode)
    if messages_to_delete[m_id] is None:
        messages_to_delete[m_id] = []
    messages_to_delete[m_id].append(res.id)
    return res


async def send_and_save_with_markup(m_id, text, markup, parse_mode=None):
    res = await bot.send_message(m_id, text, reply_markup=markup, parse_mode=parse_mode)
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
        if interest.owner_id not in already_sent and interest.owner_id != get_auction(auction_id).owner_id:
            msges = await bot.send_media_group(interest.owner_id, create_photos_for_item(get_item(get_auction(auction_id).item_id)))
            photos_ids = ''
            for msg in msges:
                photos_ids += '_' + str(msg.id)
                messages_to_delete[interest.owner_id].append(msg.id)
            await send_and_save_with_markup(interest.owner_id,
                                            'Новый аукцион для вас!\n' + create_auction_message(
                                                get_auction(auction_id)),
                                            create_button_to_part_in_auction(auction_id))
            already_sent.append(interest.owner_id)
    ids_without_interests = get_users_without_interests()
    for id in ids_without_interests:
        if id != get_auction(auction_id).owner_id:
            msges = await bot.send_media_group(id,
                                               create_photos_for_item(get_item(get_auction(auction_id).item_id)))
            photos_ids = ''
            for msg in msges:
                photos_ids += '_' + str(msg.id)
                messages_to_delete[id].append(msg.id)
            await send_and_save_with_markup(id,
                                            'Новый аукцион был опубликован!\n' + create_auction_message(
                                                get_auction(auction_id)),
                                            create_button_to_part_in_auction(auction_id))
            # await send_and_save(id, 'Сейчас вам приходят уведомления о всех предстоящих аукционах. Вы можете настроить фильтры при'
            #                     'помощи команд /add_interest и /interests')
            already_sent.append(id)


async def send_user_to_moderation(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Принять', callback_data='allow_' + str(user_id)))
    markup.add(types.InlineKeyboardButton('Отклонить', callback_data='not_allow_' + str(user_id)))
    await send_and_save_with_markup(moderator_id, 'Новый пользователь желает зарегистрироваться.\n' + create_user_info_for_moderation(get_user_info(user_id)), markup)


async def send_auction_to_moderation(auction_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Принять', callback_data='accept_' + str(auction_id)))
    markup.add(types.InlineKeyboardButton('Отклонить', callback_data='decline_' + str(auction_id)))
    msges = await bot.send_media_group(moderator_id, create_photos_for_item(get_item(get_auction(auction_id).item_id)))
    photos_ids = ''
    auction = get_auction(auction_id)
    for msg in msges:
        photos_ids += '_' + str(msg.id)
        messages_to_delete[moderator_id].append(msg.id)
    await send_and_save_with_markup(
        moderator_id,
        f'Владелец часов: @{escape_markdown(get_user_info(auction.owner_id).nick)}\n' + create_auction_message(auction),
        markup, 'Markdown'
    )


async def get_auctions_for_filter(interest):
    auctions_id = get_auctions_for_interest(interest)
    for id in auctions_id:
        await send_and_save_with_markup(interest.owner_id, create_auction_message(get_auction(id)),
                                        create_button_to_part_in_auction(id))


# Обрабатываем команду start, если пользователя нет в бд, начинаем процесс регистрации, создавая соответствующий хэндлер
# и обновляя текущий статус пользователя
@bot.message_handler(commands=['start'])
async def send_welcome_message(message):
    if message.from_user.username is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        messages_to_delete[message.chat.id].append(message.id)
        await send_and_save(message.chat.id, 'Для использования бота необходимо, чтобы у вашего аккаунта был никнейм. Инструкци по созданию: https://uchet-jkh.ru/i/kak-sozdat-nikneim-v-telegrame/\nПосле того, как создадите - возвращайтесь и используйте команду /start')
        return
    if message.chat.id not in states:
        if message.chat.id in messages_to_delete:
            await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id] = []
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'notRegistered'
        reg_handlers[message.chat.id] = RegistrationHandler()
        await send_and_save(message.chat.id, 'Добро пожаловать! Давайте Вас зарегистрируем.')
        await send_and_save(message.chat.id, reg_handlers[message.chat.id].do_registration(''))
    else:
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}.')
            return
        if get_user_info(message.chat.id) is not None:
            states[message.chat.id] = 'on_main_menu'
            await send_and_save(message.chat.id, main_menu_message(message.chat.id))
        else:
            await send_and_save(message.chat.id, 'Пожалуйста, пройдите регистрацию')
        # вывод приветственного сообщения


# @bot.message_handler(commands=['add_interest'])
# async def add_interest(message):
#     if get_user_info(message.chat.id) is None:
#         if message.chat.id not in messages_to_delete:
#             messages_to_delete[message.chat.id] = []
#         await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
#         return
#     if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
#         if is_blocked(message.chat.id):
#             await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
#             return
#         await clear_chat(message.chat.id)
#         messages_to_delete[message.chat.id].append(message.id)
#         states[message.chat.id] = 'on_interest_survey'
#         interests[message.chat.id] = InterestsHandler()
#         current_bot_message = interests[message.chat.id].interest_survey('')
#         await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
#     else:
#         await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())


# Обрабатываем команду profile, выводим информацию о профиле отправившего команду
@bot.message_handler(commands=['profile'])
async def open_profile(message):
    if get_user_info(message.chat.id) is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
        return
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
            return
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        user = get_user_info(message.chat.id)
        current_bot_message = create_user_info_message(user)
        await send_and_save(message.chat.id, current_bot_message)
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



@bot.message_handler(commands=['coming_auctions'])
async def open_coming_auctions(message):
    if get_user_info(message.chat.id) is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        messages_to_delete[message.chat.id].append(message.id)
        await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
        return
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
            return
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        auctions = get_coming_auctions(message.chat.id)
        if len(auctions) > 0:
            for au in auctions:
                markup = types.InlineKeyboardMarkup()
                if get_auto_bid(message.chat.id, au.id) is None and (au.duration - datetime.now()).total_seconds() // 60 > TIME_FOR_AUTO_BIDS:
                    markup.add(types.InlineKeyboardButton('Автоставка', callback_data='create_auto_bid_' + str(au.id)))
                if au.state == 'going':
                    markup.add(types.InlineKeyboardButton('Войти в аукцион', callback_data='open_auction_' + str(au.id)))
                msges = await bot.send_media_group(message.chat.id, create_photos_for_item(get_item(au.item_id)))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                    messages_to_delete[message.chat.id].append(msg.id)
                await send_and_save_with_markup(message.chat.id, create_auction_message(au), markup)
                is_changeable = True
                if (au.duration - datetime.now()).total_seconds() // 60 <= TIME_FOR_AUTO_BIDS:
                    is_changeable = False
                await create_and_send_auto_bid_message(message.chat.id, au.id, is_changeable)
        else:
            await send_and_save(message.chat.id, 'Вы не участвуете ни в одном активном аукционе. Чтобы просмотреть доступные аукционы, используйте команду /all_auctions')
    else:
        messages_to_delete[message.chat.id].append(message.id)
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



@bot.message_handler(commands=['all_auctions'])
async def open_coming_auctions(message):
    if get_user_info(message.chat.id) is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
        return
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
            return
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        au_ids = get_auction_to_participate(message.chat.id)
        if len(au_ids) > 0:
            auctions_available = False
            for id in au_ids:
                auction = get_auction(id)
                auctions_available = True
                msges = await bot.send_media_group(message.chat.id, create_photos_for_item(get_item(auction.item_id)))
                photos_ids = ''
                for msg in msges:
                    photos_ids += '_' + str(msg.id)
                    messages_to_delete[message.chat.id].append(msg.id)
                if auction.owner_id != message.chat.id:
                    await send_and_save_with_markup(message.chat.id, create_auction_message(auction), create_button_to_part_in_auction(id))
                else:
                    await send_and_save(message.chat.id, create_auction_message(auction) + '\n\n*Вы являетесь владельцем аукциона*', 'Markdown')
            if not auctions_available:
                await send_and_save(message.chat.id, 'На данный момент нет доступных аукционов для участия')
        else:
            await send_and_save(message.chat.id, 'На данный момент нет доступных аукционов для участия')
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)


# Отправляем отдельными сообщениями все интересы данного пользователя
# @bot.message_handler(commands=['interests'])
# async def open_interests(message):
#     if get_user_info(message.chat.id) is None:
#         if message.chat.id not in messages_to_delete:
#             messages_to_delete[message.chat.id] = []
#         await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
#         return
#     if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
#         if is_blocked(message.chat.id):
#             await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
#             return
#         await clear_chat(message.chat.id)
#         messages_to_delete[message.chat.id].append(message.id)
#         user_interests = get_interests(message.chat.id)
#         if user_interests.first() is not None:
#             for interest in user_interests:
#                 markup = types.InlineKeyboardMarkup(row_width=1)
#                 markup.add(types.InlineKeyboardButton('Удалить', callback_data='interest_' + str(interest.id)))
#                 await send_and_save_with_markup(message.chat.id, create_interest_message(interest), markup)
#         else:
#             await send_and_save(message.chat.id,
#                                 'У вас нет ни одного фильтра. Чтобы добавить, используйте команду /add_interest')
#             await send_and_save(message.chat.id, main_menu_message(message.chat.id))
#     else:
#         await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



def create_unblock_button(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Разблокировать', callback_data='unblock_' + str(user_id)))
    return markup


def create_block_buttons(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton('Заблокировать на месяц', callback_data='small_block_' + str(user_id)))
    markup.add(types.InlineKeyboardButton('Заблокировать навсегда', callback_data='block_' + str(user_id)))
    return markup


@bot.message_handler(commands=['show_users'])
async def show_users(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu' and message.chat.id == moderator_id:
        users = get_all_users()
        for user in users:
            if user.id != moderator_id:
                text = f'Имя: {escape_markdown(user.username)}\n' \
                       f'Тег: @{escape_markdown(user.nick)}\n' \
                       f'Компания: {escape_markdown(user.company_name)}\n' \
                       f'Сайт: {escape_markdown(user.company_website)}'
                if is_blocked(user.id) and user.ban - datetime.now() <= timedelta(days=366*30):
                    markup = create_unblock_button(user.id)
                    text += f'\n*Заблокирован до {str(user.ban)}*'
                else:
                    markup = create_block_buttons(user.id)
                await send_and_save_with_markup(message.chat.id, text, markup, 'Markdown')
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только в главном меню, обладая правами модератора', create_back_to_main_menu_button())


@bot.message_handler(commands=['waiting_users'])
async def show_users(message):
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu' and message.chat.id == moderator_id:
        users = get_all_users()
        if users is not None:
            for user in users:
                if user.id != moderator_id and user.ban - datetime.now() > timedelta(days=366*30):
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    markup.add(types.InlineKeyboardButton('Принять', callback_data='allow_' + str(user.id)))
                    markup.add(types.InlineKeyboardButton('Отклонить', callback_data='not_allow_' + str(user.id)))
                    await send_and_save_with_markup(moderator_id,
                                                    'Новый пользователь желает зарегистрироваться.\n' + create_user_info_for_moderation(
                                                        user), markup)
        else:
            await send_and_save(moderator_id, 'Сейчас нет пользователей, ожидающих модерации аккаунта!')
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только в главном меню, обладая правами модератора', create_back_to_main_menu_button())

@bot.message_handler(commands=['my_auctions'])
async def open_items(message):
    if get_user_info(message.chat.id) is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
        return
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
            return
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        user_items = get_items(message.chat.id)
        won_auctions = get_won_auctions(message.chat.id)
        if user_items.first() is not None or won_auctions.first() is not None:
            if user_items.first() is not None:
                for item in user_items:
                    # markup = types.InlineKeyboardMarkup(row_width=1)
                    # markup.add(
                    #     types.InlineKeyboardButton('Создать аукцион', callback_data='create_auction_' + str(item.id)))
                    msges = await bot.send_media_group(message.chat.id, create_photos_for_item(item))
                    photos_ids = ''
                    for msg in msges:
                        photos_ids += '_' + str(msg.id)
                        messages_to_delete[message.chat.id].append(msg.id)
                    # markup.add(types.InlineKeyboardButton('Удалить', callback_data='item_' + str(item.id) + photos_ids))
                    if is_item_on_auction(item.id):
                        auction = get_auction_for_item(item.id)
                        if auction.state == 'active':
                            text = f'\n\n*Предмет выставлен на аукционе*\nНачало: {auction.start_date}'
                        elif auction.state == 'going':
                            text = f'\n\n*Предмет в данный момент разыгрывается на аукционе*\nТекущая ставка: *{get_max_bid(auction.id).amount}*\nАукцион закончится: {auction.duration}'
                        elif auction.state == 'finished' and auction.winner_id is not None:
                            text = f'\n\n*Вы продали предмет на аукционе*\nЦена: {get_max_bid(auction.id).amount}\nПокупатель: @{escape_markdown(get_user_info(auction.winner_id).nick)}'
                        elif auction.state == 'finished':
                            text = f'\n\n*Аукцион не состоялся*'
                        else:
                            text = f'\n\n*Предмет на аукционе и ожидает модерации*'
                        await send_and_save(message.chat.id, escape_markdown(create_item_text(item)) + text, 'Markdown')
                    else:
                        await send_and_save(message.chat.id, create_item_text(item))
            if won_auctions.first() is not None:
                for auction in won_auctions:
                    text = f'\n\n*Вы выиграли аукцион*\nВаша победная ставка: {get_max_bid(auction.id)}\nСвяжитесь с \@{escape_markdown(get_user_info(auction.owner_id).nick)} для оплаты и получения часов'
                    await send_and_save(message.chat.id, escape_markdown(create_item_text(get_item(auction.item_id))) + text, 'Markdown')
        else:
            await send_and_save(message.chat.id,
                                'У вас нет ни одного предмета в профиле. Чтобы добавить, используйте команду /add_auction')
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



@bot.message_handler(commands=['add_auction'])
async def add_item(message):
    if get_user_info(message.chat.id) is None:
        if message.chat.id not in messages_to_delete:
            messages_to_delete[message.chat.id] = []
        await send_and_save(message.chat.id, 'Сперва необходимо пройти регистрацию, используйте команду /start')
        return
    if message.chat.id in states and states[message.chat.id] == 'on_main_menu':
        if is_blocked(message.chat.id):
            await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
            return
        await clear_chat(message.chat.id)
        messages_to_delete[message.chat.id].append(message.id)
        states[message.chat.id] = 'on_adding_items'
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    else:
        await send_and_save_with_markup(message.chat.id, 'Данную команду можно использовать только находясь в главном меню.', create_back_to_main_menu_button())



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


def create_back_button(auction_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Назад', callback_data='back_' + str(auction_id)))
    return markup


def get_user_ids_that_not_in_auction(auction_id):
    buyers = get_auction_buyers(auction_id)
    buyers_ids = []
    for buyer in buyers:
        buyers_ids.append(buyer.buyer_id)
    for msg in auction_messages[auction_id]:
        buyers_ids.remove(msg.chat.id)
    return buyers_ids


async def send_notifications_when_auction_is_ending(auction_id):
    ids = get_user_ids_that_not_in_auction(auction_id)
    auction = get_auction(auction_id)
    for id in ids:
        msges = await bot.send_media_group(id, create_photos_for_item(get_item(auction.item_id)))
        photos_ids = ''
        for msg in msges:
            photos_ids += '_' + str(msg.id)
            messages_to_delete[auction.owner_id].append(msg.id)
        await send_and_save(id, 'АУКЦИОН ЗАКОНЧИТСЯ ЧЕРЕЗ 5 МИНУТ!\n\n' + escape_markdown(create_auction_message(auction)) + f'Текущая ставка:*{get_max_bid(auction_id)}*', 'Markdown')
    schedule.clear('end_auction_' + str(auction_id))




def main_menu_message(chat_id):
    if chat_id == moderator_id:
        return main_menu_message_for_moderator
    return main_menu_mess


@bot.callback_query_handler(func=lambda call: True)
async def brand_buttons_action(call):
    if call.message:
        if (call.data in all_brands or call.data in other_brands) and states[call.message.chat.id] == 'on_interest_survey':
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='Вы выбрали: ' + call.data)
            await send_and_save_with_markup(call.message.chat.id, interests[call.message.chat.id].interest_survey(call.data), create_back_to_main_menu_button())
        elif (call.data in all_brands or call.data in other_brands) and states[
            call.message.chat.id] == 'on_adding_items':
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text='Вы выбрали: ' + call.data)
            await send_and_save_with_markup(call.message.chat.id, items[call.message.chat.id].create_item(call.data), create_back_to_main_menu_button())
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
            await clear_chat(call.message.chat.id)
            await send_and_save(auction.owner_id,
                                'Ваш аукцион был опубликован! Опубликованные аукционы можно посмотреть по команде /all_auctions')
            await send_notifications_about_auction(auction_id)
            time = str(auction.start_date.time())[:-3]
            if datetime.now() < auction.start_date:
                schedule.every().day.at(time).do(start_auction, auction_id).tag(
                    'start_auction_' + str(auction_id))
            elif auction.start_date < datetime.now() < auction.duration:
                await start_auction(auction_id)
        elif call.data.find('decline') != -1:
            auction_id = call.data.split('_')[1]
            auction = get_auction(auction_id)
            await clear_chat(call.message.chat.id)
            msges = await bot.send_media_group(auction.owner_id, create_photos_for_item(get_item(auction.item_id)))
            photos_ids = ''
            for msg in msges:
                photos_ids += '_' + str(msg.id)
                messages_to_delete[auction.owner_id].append(msg.id)
            await send_and_save(auction.owner_id, create_auction_message(auction))
            delete_bids_for_auction(auction_id)
            delete_auction(auction_id)
            await send_and_save(
                auction.owner_id,
                'Ваш аукцион был отклонен! Убедитесь, что в объявлении '
                f'не было ошибки или свяжитесь с модератором @{get_user_info(moderator_id).nick}')
        elif call.data.find('participate') != -1:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
            buyers = get_auction_buyers(call.data.split('_')[1])
            is_not_already_buyer = True
            for buyer in buyers:
                if buyer.buyer_id == call.message.chat.id:
                    is_not_already_buyer = False
            if is_not_already_buyer:
                save_buyer(call.data.split('_')[1], call.message.chat.id)
                await send_and_save(call.message.chat.id,
                                    'Вы стали участником аукциона! Просмотреть приближающиеся аукционы можно командой /coming_auctions')
            else:
                await send_and_save(call.message.chat.id,
                                    'Вы уже участвуете в этом аукционе! Просмотреть приближающиеся аукционы можно командой /coming_auctions')
        elif call.data.find('open_auction') != -1:
            auction_id = call.data.split('_')[2]
            if call.message.chat.id == get_auction(auction_id).winner_id:
                state = '\n\n*Вы являетесь лидером аукциона*'
            else:
                state = '\n\n*Вы не являетесь лидером аукциона*'
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text + '\nТекущая ставка: ' + '*' + str(
                                            get_max_bid(auction_id).amount) + '*' + state, reply_markup=create_back_button(auction_id), parse_mode='Markdown')
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
            auction_id = int(call.data.split('_')[1])
            auction_messages[auction_id].remove(call.message)
            await clear_chat(call.message.chat.id)
            await send_and_save(call.message.chat.id, main_menu_message(call.message.chat.id))
        elif call.data.find('small_block_') != -1:
            user_id = call.data.split('_')[2]
            date = datetime.now()
            days_in_month = calendar.monthrange(date.year, date.month)[1]
            date += timedelta(days=days_in_month)
            block_user(user_id, date)
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text + f'\n\n*Заблокирован до {str(date)}*',
                                        reply_markup=create_unblock_button(user_id), parse_mode='Markdown')
        elif call.data.find('unblock') != -1:
            user_id = call.data.split('_')[1]
            unblock_user(user_id)
            text = call.message.text.split('\n')[0] + '\n' + call.message.text.split('\n')[1]
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=text, reply_markup=create_block_buttons(user_id), parse_mode='Markdown')
        elif call.data.find('block') != -1:
            user_id = call.data.split('_')[1]
            date = datetime.now()
            date = date.replace(year=date.year + 30)
            block_user(user_id, date)
            await bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id,
                                        text=call.message.text + f'*\n\nЗаблокирован до {str(date)}*',
                                        reply_markup=create_unblock_button(user_id), parse_mode='Markdown')
        elif call.data.find('not_allow') != -1:
            await send_and_save(int(call.data.split('_')[2]), f'К сожалению, вашу заявку на вступление отклонили. Вы можете связаться с модератором @{get_user_info(moderator_id).nick}.')
            await bot.delete_message(moderator_id, call.message.id)
            delete_user(int(call.data.split('_')[2]))
            states.pop(int(call.data.split('_')[2]), None)
        elif call.data.find('allow') != -1:
            user_id = int(call.data.split('_')[1])
            await send_and_save(user_id, f'Модератор принял вашу заявку на вступление!')
            unblock_user(user_id)
            await clear_chat(user_id)
            await send_and_save(user_id, main_menu_message(user_id))
            await bot.delete_message(moderator_id, call.message.id)
            states[user_id] = 'on_main_menu'


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


def create_back_to_main_menu_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('В главное меню'))
    return markup

def create_accept_rules_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton('Принять'))
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


def create_user(user_id):
    hl = reg_handlers[user_id]
    return User(id=user_id, username=hl.name, company_name=hl.company_name,
                company_website=hl.website, phone=hl.phone, nick=hl.nick, ban=hl.ban)


def create_photo(name, id):
    return Photo(name=name, item_id=id)


def create_interest(user_id):
    hl = interests[user_id]
    return Interest(owner_id=user_id, brand=hl.brand, min_price=hl.minPrice, max_price=hl.maxPrice)


def create_item(user_id):
    hl = items[user_id]
    if hl.comments == 'Пропустить':
        hl.comments = None
        hl.comments = None
    return Item(brand=hl.brand, reference=hl.reference, price=hl.price, box_available=hl.box_available,
                document_available=hl.document_available, comments=hl.comments, owner_id=user_id, city=hl.city)


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
            f_id = message.photo[-1].file_id
            file_info = await bot.get_file(f_id)
            items[message.chat.id].append_photo(file_info)
            if len(items[message.chat.id].photos) == 3:
                current_bot_message = items[message.chat.id].create_item('')
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            await send_and_save(message.chat.id, 'Фото необходимо прикрепить на соответствующем этапе')
    else:
        await send_and_save(message.chat.id, 'Фото необходимо отправлять во время добавления предмета в профиль')


@bot.message_handler(content_types=['video'])
async def handle_video(message):
    messages_to_delete[message.chat.id].append(message.id)
    if is_blocked(message.chat.id):
        await send_and_save(message.chat.id,
                            f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
        return
    if states[message.chat.id] == 'on_adding_items' and items[message.chat.id].currentState == 'getBox_available':
        await send_and_save(message.chat.id, f'К предмету будут добавлены только фото. Пришлите еще {3 - len(items[message.chat.id].photos)} фото')
    else:
        await send_and_save(message.chat.id, f'Бот не поддерживает отправку видео')


# Обработка всех текстовых сообщений, которые не являются командами
@bot.message_handler(content_types=['text'])
async def handle_request(message):
    messages_to_delete[message.chat.id].append(message.id)
    if is_blocked(message.chat.id):
        await send_and_save(message.chat.id, f'К сожалению, вы были заблокированы или еще не прошли модерацию. Обратитесь к модератору @{get_user_info(moderator_id).nick}')
        return
    if message.text == 'Назад' or message.text == 'В главное меню':
        states[message.chat.id] = 'on_main_menu'
        await clear_chat(message.chat.id)
        await send_and_save(message.chat.id, main_menu_message(message.chat.id))
    if states[message.chat.id] == 'notRegistered':
        current_bot_message = reg_handlers[message.chat.id].do_registration(
            message.text)  # По айди чата вызываем функцию регистрации
        if current_bot_message.find('верно') != -1:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        elif current_bot_message.find('Если вы назначили ставку в аукционе') != -1:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_accept_rules_button(), 'Markdown')
        else:
            await send_and_save_with_markup(message.chat.id, current_bot_message, telebot.types.ReplyKeyboardRemove())
        if current_bot_message == 'Отлично! Регистрация завершена. Когда модератор одобрит заявку на вступление, Вам придет уведомление':
            reg_handlers[message.chat.id].nick = message.from_user.username
            if message.chat.id != moderator_id:
                reg_handlers[message.chat.id].ban = datetime.now().replace(year=datetime.now().year + 100)
            save_user(create_user(message.chat.id))
            await send_user_to_moderation(message.chat.id)
            if message.chat.id == moderator_id:
                await clear_chat(message.chat.id)
                states[message.chat.id] = 'on_main_menu'
                await send_and_save(message.chat.id, main_menu_message(message.chat.id))
            # interests[message.chat.id] = InterestsHandler()
            # current_bot_message = interests[message.chat.id].interest_survey('')
            # await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
    elif states[message.chat.id] == 'on_interest_survey':  # по айди чата вызываем функцию добавления интереса
        if message.text == 'Пропустить':
            states[message.chat.id] = 'on_main_menu'
            await clear_chat(message.chat.id)
            await send_and_save_with_markup(message.chat.id, main_menu_message(message.chat.id), telebot.types.ReplyKeyboardRemove())
            return
        current_bot_message = interests[message.chat.id].interest_survey(message.text)
        if interests[message.chat.id].currentState == 'getMinPrice':
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        elif current_bot_message.find('верно') != -1 or current_bot_message.find('Фильтр объявлений добавлен') != -1:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
        else:
            await send_and_save_with_markup(message.chat.id, current_bot_message, create_back_to_main_menu_button())
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
        await send_and_save(message.chat.id, main_menu_message(message.chat.id))
    elif states[message.chat.id] == 'on_adding_items':
        if items[message.chat.id].currentState != 'getBox_available':
            current_bot_message = items[message.chat.id].create_item(message.text)
            if current_bot_message.find('Давайте проверим, что я все верно записал:') != -1:
                items[message.chat.id].comments = message.text
                new_item_id = save_item(create_item(message.chat.id))
                names = await save_photos_to_folder(items[message.chat.id].photos, new_item_id)
                for name in names:
                    save_photo(create_photo(name, new_item_id))
                states[message.chat.id] = 'creating_auction'
                items[message.chat.id].id = new_item_id
                auction_handler[message.chat.id] = AuctionHandler()
                auction_handler[message.chat.id].item_id = new_item_id
                await send_and_save(message.chat.id, auction_handler[message.chat.id].create_auction(''))
                return
            if current_bot_message.find('Имеется ли коробка от часов:') != -1 or current_bot_message.find(
                    'Документы от часов') != -1 or current_bot_message.find('Необходимо') != -1 or \
                    current_bot_message.find('Желаете добавить еще один') != -1 or current_bot_message.find('Все верно?') != -1:
                if current_bot_message.find('Желаете добавить еще один') != -1 and len(items[message.chat.id].photos) < 3:
                    current_bot_message = 'Не удалось добавить предмет. Вы прикрепили меньше 3-х фотографий. Желаете заново добавить предмет?'
                    states[message.chat.id] = 'can_end_item_survey'
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_yes_or_no_button())
            elif current_bot_message.find('Укажи бренд часов, которые хотите выставить на аукцион') != -1:
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
            elif current_bot_message.find('дефекты') != - 1:
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_skip_button())
            else:
                await send_and_save_with_markup(message.chat.id, current_bot_message,
                                                create_back_to_main_menu_button())
        else:
            await send_and_save(message.chat.id, f'Необходимо прикрепить еще {3 - len(items[message.chat.id].photos)} фото(прикреплять видео запрещено, они не будут сохранены).')
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Да' or message.text == 'да'):
        await clear_chat(message.chat.id)
        items[message.chat.id] = NewItem()
        current_bot_message = items[message.chat.id].create_item('')
        await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
        states[message.chat.id] = 'on_adding_items'
    elif states[message.chat.id] == 'can_end_item_survey' and (message.text == 'Нет' or message.text == 'нет'):
        await clear_chat(message.chat.id)
        states[message.chat.id] = 'on_main_menu'
        await send_and_save(message.chat.id, main_menu_message(message.chat.id))
    elif states[message.chat.id] == 'creating_auction':
        current_bot_message = auction_handler[message.chat.id].create_auction(message.text)
        if auction_handler[message.chat.id].currentState == 'end':
            msges = await bot.send_media_group(message.chat.id,
                                               create_photos_for_item(get_item(items[message.chat.id].id)))
            photos_ids = ''
            for msg in msges:
                photos_ids += '_' + str(msg.id)
                messages_to_delete[message.chat.id].append(msg.id)
            msg = "*Часы:* \n" + escape_markdown(create_item_text(
                get_item(auction_handler[message.chat.id].item_id))) + '*Аукцион:*\n' + current_bot_message
            await send_and_save_with_markup(message.chat.id, msg, create_yes_or_no_button(), 'Markdown')
        else:
            if current_bot_message == 'Укажите минимальный шаг ставки:': # очень плохо, переделать
                delete_item(items[message.chat.id].id)
                items[message.chat.id] = NewItem()
                current_bot_message = items[message.chat.id].create_item('')
                states[message.chat.id] = 'on_adding_items'
                await send_and_save_with_markup(message.chat.id, current_bot_message, create_brand_buttons())
                return
            await send_and_save(message.chat.id, current_bot_message)
        if current_bot_message == 'Отлично! Аукцион создан и отправлен на модерацию':
            await clear_chat(message.chat.id)
            states[message.chat.id] = 'on_main_menu'
            await send_and_save(message.chat.id, main_menu_message(message.chat.id))
            new_auction_id = save_auction(create_auction(message.chat.id))
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
                    save_bid(create_bid(int(message.text), message.chat.id, auction_id))
                    delta = get_auction(auction_id).duration - datetime.now()
                    if delta.total_seconds() // 60 <= MINUTES_TO_ENLARGE:
                        update_auction_time(auction_id, ADDITIONAL_MINUTES)
                        schedule.clear('end_auction_' + str(auction_id))
                        schedule.clear('auto_bids_' + str(auction_id))
                        await create_autobids_task(auction_id)
                        await create_end_auction_task(auction_id)
                    previous_winner = auction.winner_id
                    update_winner_id(auction_id, message.chat.id)
                    auction = get_auction(auction_id)
                    for m in auction_messages[auction_id]:
                        try:
                            text = create_auction_message(get_auction(auction_id)) + '\nТекущая ставка: ' + '*' + str(get_max_bid(auction_id).amount) + '*'
                            if m.chat.id == auction.winner_id:
                                text += '\n\n*Вы являетесь лидером аукциона*'
                            else:
                                text += '\n\n*Вы не являетесь лидером аукциона*'
                            await bot.edit_message_text(chat_id=m.chat.id, message_id=m.id, text=text, reply_markup=create_back_button(auction_id), parse_mode="Markdown")
                        except:
                            print("MESSAGE WAS NOT FOUND")
                    markup = types.InlineKeyboardMarkup()
                    markup.add(types.InlineKeyboardButton('Перейти',
                                                          callback_data='open_auction_' + str(auction.id)))
                    msges = await bot.send_media_group(previous_winner,
                                                       create_photos_for_item(get_item(auction.item_id)))
                    photos_ids = ''
                    for msg in msges:
                        photos_ids += '_' + str(msg.id)
                        messages_to_delete[previous_winner].append(msg.id)
                    await send_and_save_with_markup(previous_winner,
                                                    "ВАШУ СТАВКУ ПЕРЕБИЛИ\n" + escape_markdown(create_auction_message(
                                                        auction)) + '\nТекущая ставка: ' + '*' + str(get_max_bid(auction_id).amount) + '*', markup, 'Markdown')
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
                    await send_and_save(message.chat.id, main_menu_message(message.chat.id))
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
                    await send_and_save(message.chat.id, main_menu_message(message.chat.id))
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
    await give_state_to_all_registered_users()
    await asyncio.gather(bot.infinity_polling(), scheduler())


if __name__ == '__main__':
    asyncio.run(main())
