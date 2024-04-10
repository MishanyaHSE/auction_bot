from db.db_models import *
from telebot import types
import telebot

all_brands = ['Audemars Piguet', 'Breguet', 'Breitling', 'Cartier', 'Daniel Roth', 'De Bethune', 'Franck Muller',
              'Hublot', 'IWC', 'Jaeger LeCoultre', 'Omega', 'Patek Philippe', 'Rolex', 'Ulysse Nardin',
              'Vacheron Constantin']

other_brands = ['Alain Silberstein', 'Arnold Son', 'Blancpain', 'Bovet', 'Chopard', 'Chronoswiss', 'Corum', 'Cvstos',
                'Gerald Genta', 'Girard Perregaux', 'HYT', 'Harry Winston', 'Hautlence', 'Jaquet Droz', 'Jorg Hysek',
                'F.P.Journe', 'Konstantin Chaykin', 'A. Lange&Sohne', 'Omega', 'Panerai', 'Parmigiani', 'Piaget',
                'Ressence', 'Roger Dubuis', 'Romain Jerome', 'Tudor', 'Urwerk', 'Zenith']

main_menu_mess = f'Вы находитесь в главном меню, используйте команды для управления ботом:\n' \
                 f'/add_auction - Выставить часы на аукцион\n' \
                 f'/all_auctions - Просмотр всех аукционов\n' \
                 f'/coming_auctions - Просмотр аукционов, в которых вы участвуете\n' \
                 f'/my_auctions - Просмотр ваших аукционов\n' \
                 f'/profile - Просмотр профиля'
                 # f'/add_interest - Создание фильтра уведомлений об аукционах\n' \
                 # f'/interests - Просмотр ваших уведомлений по бренду и цене\n' \

main_menu_message_for_moderator = main_menu_mess + '\n\n' + 'Список команд модератора:\n' \
                                                            '/show_users - открыть список пользователей для блокировки или разблокировки\n' \
                                                            '/waiting_users - открыть список пользователей, отправивших заявку на вступление\n'
def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}.!'
    return ''.join('\\' + char if char in escape_chars else char for char in text)


def is_positive_number(s):
    try:
        int(s)
        if int(s) >= 0:
            return True
        return False
    except ValueError:
        return False


def create_user_info_message(user):
    return f'Ваше имя: {user.username}\n' \
           f'Ваш номер телефона: {user.phone}\n' \
           f'Название вашей компании: {user.company_name}\n' \
           f'Вебсайт компании: {user.company_website}\n'


def create_user_info_for_moderation(user):
    return f'Имя: {user.username}\n' \
           f'Номер телефона: {user.phone}\n' \
           f'Название компании: {user.company_name}\n' \
           f'Вебсайт компании: {user.company_website}\n' \
           f'Тег: @{user.nick}\n'


def create_interest_message(interest):
    return f'Бренд: {interest.brand}\n' \
           f'Минимальная стоимость: {interest.min_price}\n' \
           f'Максимальная стоимость: {interest.max_price}'


def create_auction_message(auction, is_markdown=False):
    item = get_item(auction.item_id)
    auction_info = f'Минимальный шаг: {auction.bid_step}\n' \
                   f'Начало: {auction.start_date} МСК\n' \
                   f'Конец: {auction.duration} МСК\n'
    item_info = create_item_text(item)
    if is_markdown:
        item_info = escape_markdown(item_info)
    return f'Предмет:\n' + item_info + '\n' + f'Аукцион:\n' + auction_info


def create_item_text(item, is_markdown=False):
    box = 'Нет'
    docs = 'Нет'
    if item.box_available:
        box = 'Да'
    if item.document_available:
        docs = 'Да'
    text = f'Бренд: {item.brand}\n' \
               f'Референс: {item.reference}\n' \
               f'Коробка: ' + box + '\n'\
               f'Документы: ' + docs + '\n'\
               f'Город: {item.city}\n'
    if get_auction_for_item(item.id).state == 'on_moderatiion' or get_auction_for_item(item.id).state == 'finished':
        text += f'Начальная цена: {item.price}\n'
    if item.comments is not None:
        text += f'Комментарий: {item.comments}\n'
    if is_markdown:
        text = escape_markdown(text)
    return text


def create_photos_for_item(item):
    photos = get_photos_for_item(item.id)
    medias = []
    for photo in photos:
        medias.append(types.InputMediaPhoto(open(photo.name, 'rb')))
    return medias
