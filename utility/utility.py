from db.db_models import *
from telebot import types
import telebot

all_brands = ['Audemars Piguet', 'Breguet', 'Breitling', 'Cartier', 'Daniel Roth', 'De Bethune', 'Franck Muller',
              'Hublot', 'IWC', 'Jaeger LeCoultre', 'Omega', 'Patek Philippe', 'Rolex', 'Ulysse Nardin',
              'Vacheron Constantin']

other_brands = ['Alain Silberstein', 'Arnold Son', 'Blancpain', 'Bovet', 'Chopard', 'Chronoswiss', 'Corum', 'Cvstos',
                'Gerald Genta', 'Girard Perregaux', 'HYT', 'Harry Winston', 'Hautlence', 'Jaquet Droz', 'Jorg Hysek',
                'Journe', 'Konstantin Chaykin', 'Lange&Sohne', 'Omega', 'Panerai', 'Parmigiani', 'Piaget',
                'Ressence', 'Roger Dubuis', 'Romain Jerome', 'Tudor', 'Urwerk', 'Zenith']


main_menu_mess = f'Вы находитесь в главном меню, используйте команды для управления ботом:\n' \
                    f'/all_auctions - Просмотр списка приближающихся и начавшихся аукционов, в которых вы еще не участвуете\n' \
                    f'/coming_auctions - Просмотр списка приближающихся и начавшихся аукционов, в которых вы участвуете\n' \
                    f'/add_interest - Добавление фильтра объявлений\n' \
                    f'/interests - Просмотр установленных фильтров объявлений\n' \
                    f'/add_item - Добавление предмета\n' \
                    f'/items - Просмотр добавленных предметов, создание аукциона\n' \
                    f'/profile - Просмотр профиля'


main_menu_message_for_moderator = main_menu_mess + '\n\n' + 'Список команд модератора:\n' \
                                                               '/show_users - открыть список пользователей для блокировки или разблокировки\n'

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


def create_interest_message(interest):
    return f'Бренд: {interest.brand}\n' \
           f'Минимальная стоимость: {interest.min_price}\n' \
           f'Максимальная стоимость: {interest.max_price}'


def create_auction_message(auction):
    item = get_item(auction.item_id)
    auction_info = f'Минимальный шаг: {auction.bid_step}\n' \
                   f'Начало: {auction.start_date}\n' \
                   f'Конец: {auction.duration}\n'
    return f'Предмет:\n' + create_item_text(item) + '\n' + f'Аукцион:\n' + auction_info


def create_item_text(item):
    box = 'Нет'
    docs = 'Нет'
    if item.box_available:
        box = 'Да'
    if item.document_available:
        docs = 'Да'
    return     f'Бренд: {item.brand}\n' \
               f'Референс: {item.reference}\n' \
               f'Цена: {item.price}\n' \
               f'Коробка: ' + box + '\n'\
               f'Документы: ' + docs + '\n'\
               f'Коментарий: {item.comments}\n'


def create_photos_for_item(item):
    photos = get_photos_for_item(item.id)
    medias = []
    for photo in photos:
        medias.append(types.InputMediaPhoto(open(photo.name, 'rb')))
    return medias


