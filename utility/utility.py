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
                 f'/profile - Просмотр профиля\n' \
                 f'/change_language - Сменить язык на английский'

main_menu_mess_eng = f'You are in the main menu, use the commands to control the bot:\n' \
                     f'/add_auction - Put the watch up for auction.\n' \
                     f'/all_auctions - View all auctions.\n' \
                     f'/coming_auctions - View the auctions you are bidding on.\n' \
                     f'/my_auctions - View your auctions.\n' \
                     f'/profile - View your profile\n' \
                     f'/change_language - Change language to Russian'
# f'/add_interest - Создание фильтра уведомлений об аукционах\n' \
# f'/interests - Просмотр ваших уведомлений по бренду и цене\n' \

main_menu_message_for_moderator = main_menu_mess + '\n\n' + 'Список команд модератора:\n' \
                                                            '/show_users - открыть список пользователей для блокировки или разблокировки\n' \
                                                            '/waiting_users - открыть список пользователей, отправивших заявку на вступление\n'

all_text_messages = {'Пожалуйста, укажите ваше имя:': ['Пожалуйста, укажите ваше имя:', 'Please, enter your name:'],
                     'Теперь укажите Ваш номер телефона:': ['Теперь укажите Ваш номер телефона:',
                                                            'Now enter your phone number:'],
                     'Давайте проверим, что я все верно записал:': ['Давайте проверим, что я все верно записал:',
                                                                    'Let\'s make sure I got it right:'],
                     '*Правила:*\n- Если вы назначили ставку в аукционе, то вы должны купить часы по этой ставке\n- '
                     'Если вы выставляете часы на аукцион, то начальной ценой должна быть цена, за которую вы готовы '
                     'продать данные часы\n- Выставлять на аукцион можно только оригинальные часы и прозрачной '
                     'историей\n- Нужно предупреждать в описании о всех серьезных дефектах (забоинах, ржавчине, '
                     'изменении хода более 15сек/сутки, неработоспособности и тд)': ['*Правила:*\n- Если вы назначили '
                                                                                     'ставку в аукционе, то вы должны '
                                                                                     'купить часы по этой ставке\n- '
                                                                                     'Если вы выставляете часы на '
                                                                                     'аукцион, то начальной ценой '
                                                                                     'должна быть цена, за которую вы '
                                                                                     'готовы продать данные часы\n- '
                                                                                     'Выставлять на аукцион можно '
                                                                                     'только оригинальные часы и '
                                                                                     'прозрачной историей\n- Нужно '
                                                                                     'предупреждать в описании о всех '
                                                                                     'серьезных дефектах (забоинах, '
                                                                                     'ржавчине, изменении хода более '
                                                                                     '15сек/сутки, неработоспособности '
                                                                                     'и тд)', '*Rules:*\n- If you '
                                                                                              'place a bid in an '
                                                                                              'auction, you must buy '
                                                                                              'the watch at that '
                                                                                              'bid\n- If you place a '
                                                                                              'watch in an auction, '
                                                                                              'the starting price must '
                                                                                              'be the price you are '
                                                                                              'willing to sell the '
                                                                                              'watch for\n- Only '
                                                                                              'original watches with a '
                                                                                              'transparent history can '
                                                                                              'be auctioned\n- All '
                                                                                              'serious defects (nicks, '
                                                                                              'rust, '
                                                                                              'movement variation over '
                                                                                              '15sec/day, inoperable, '
                                                                                              'etc.) must be mentioned '
                                                                                              'in the description.'],
                     'Ваше имя:': ['Ваше имя:', 'Your name:'],
                     'Ваш номер телефона:': ['Ваш номер телефона:', 'Your phone number'],
                     'Все верно?': ['Все верно?', 'Is that right?'],
                     'Необходимо нажать на одну из кнопок.': ['Необходимо нажать на одну из кнопок.', 'You need to press one of the buttons.'],
                     'Отлично! Регистрация завершена. Когда модератор одобрит заявку на вступление, Вам придет уведомление': ['Отлично! Регистрация завершена. Когда модератор одобрит заявку на вступление, Вам придет уведомление', 'Great! Registration is complete. You will be notified when the moderator approves your application for membership'],
                     'Чтобы получить доступ к боту, вы должны принять правила использования бота. Отправьте "Принять" или нажмите на кнопку.\n\n': ['Чтобы получить доступ к боту, вы должны принять правила использования бота. Отправьте "Принять" или нажмите на кнопку.\n\n', 'To access the bot, you must accept the rules for using the bot. Send "Accept" or click the button.\n\n'],
                     'Принять': ['Принять', 'Accept'],
                     'Да': ['Да', 'Yes'],
                     'Нет': ['Нет', 'No'],
                     'Модератор принял вашу заявку на вступление!': ['Модератор принял вашу заявку на вступление!', 'The moderator has accepted your application to join!'],
                     'Пропустить': ['Пропустить', 'Skip'],
                     'В главное меню': ['В главное меню', 'Main menu'],
                     'Язык бота был изменен на русский!': ['Язык бота был изменен на русский!', 'The language of the bot has been changed to English!'],
                     'Пожалуйста, пройдите регистрацию': ['Пожалуйста, пройдите регистрацию', 'Please register'],
                     'К сожалению, аукцион не состоялся, ни один пользователь не сделал ставку.': ['К сожалению, аукцион не состоялся, ни один пользователь не сделал ставку.', 'Unfortunately the auction did not take place, no user bid.'],
                     'Имя:': ['Имя:', 'Name:'],
                     'Номер телефона:': ['Номер телефона:', 'Phone number:'],
                     'Тег:': ['Тег:', 'Username:'],
                     'Бренд:': ['Бренд:', 'Brand:'],
                     'Минимальная стоимость:': ['Минимальная стоимость:', 'Minimum cost:'],
                     'Максимальная стоимость:': ['Максимальная стоимость:', 'Maximum cost:'],
                     'Референс:': ['Референс:', 'Reference:'],
                     'Коробка:': ['Коробка:', 'Box:'],
                     'Документы:': ['Документы:', 'Documents:'],
                     'Город:': ['Город:', 'City:'],
                     'Комментарий:': ['Комментарий:', 'Comment:'],
                     'Начальная цена, $:': ['Начальная цена, $:', 'Starting price, $:'],
                     'МСК': ['МСК', 'MSK'],
                     'Минимальный шаг:': ['Минимальный шаг:', 'Minimum step:'],
                     'Начало:': ['Начало:', 'Beginning:'],
                     'Конец:': ['Конец:', 'End'],
                     'Аукцион:': ['Аукцион:', 'Auction:'],
                     'Укажите бренд часов, которые хотите выставить на аукцион:': ['Укажите бренд часов, которые хотите выставить на аукцион:', 'Specify the brand of watch you wish to auction:'],
                     'Референс часов:': ['Референс часов:', 'Watch reference:'],
                     'Стартовая цена в $:': ['Стартовая цена в $:', 'Starting price in $:'],
                     'Имеется ли коробка от часов:("Да"/"Нет")': ['Имеется ли коробка от часов:("Да"/"Нет")', 'Is the watch box available: (“Yes”/“No”)'],
                     'Документы от часов:("Да"/"Нет")': ['Документы от часов:("Да"/"Нет")', 'Watch documents: (“Yes”/“No”)'],
                     'Укажите город, из которого будет произвдена отправка предмета:': ['Укажите город, из которого будет произвдена отправка предмета:', 'Specify the city from which the watch will be shipped:'],
                     'Опишите дефекты своих часов, если их нет, нажмите "Пропустить":': ['Опишите дефекты своих часов, если их нет, нажмите "Пропустить":', 'Describe the defects of your watch, if there are none, click “Skip”:'],
                     'Добавьте от 3 до 10 фото часов. Постарайтесь, чтобы на фото были видны следующие объекты:\n-циферблат(обязательно)\n-оборотная сторона(обязательно)\n-застежка(обязательно)\n-обратная сторона застежки\n-коробка(при наличии)\n-документы(при наличии)\n': ['Добавьте от 3 до 10 фото часов. Постарайтесь, чтобы на фото были видны следующие объекты:\n-циферблат(обязательно)\n-оборотная сторона(обязательно)\n-застежка(обязательно)\n-обратная сторона застежки\n-коробка(при наличии)\n-документы(при наличии)\n', 'Add 3 to 10 photos of the clock. Try to make sure that the photo shows the following objects:\n-dial(mandatory)\n-backside(mandatory)\n-clasp(mandatory)\n-backside of the clasp\n-box(if available)\n-documents(if available)\n'],
                     'Выберете из ячеек': ['Выберете из ячеек', 'Select from the cells'],
                     'Цена должна быть целым положительным числом!\n': ['Цена должна быть целым положительным числом!\n', 'The price must be a positive integer!\n'],
                     'Необходимо выбрать Да/Нет': ['Необходимо выбрать Да/Нет', 'You need select Yes/No'],
                     'Вы ввели слишком длинное название. Введите название города, из которого отправите часы, комментарии можно указать позже': ['Вы ввели слишком длинное название. Введите название города, из которого отправите часы, комментарии можно указать позже', 'You have entered a name that is too long. Enter the name of the city from which you are sending the watch, comments can be entered later'],
                     'Отлично! Предмет добавлен. Желаете добавить еще один?': ['Отлично! Предмет добавлен. Желаете добавить еще один?', 'All right! The item has been added. Would you like to add another one?'],
                     'Укажите минимальный шаг ставки:': ['Укажите минимальный шаг ставки:', 'Specify a minimum bid step:'],
                     'Укажите дату начала аукциона(в формате ДД.ММ):': ['Укажите дату начала аукциона(в формате ДД.ММ):', 'Specify the auction start date(in DD.MM format):'],
                     'Укажите время начала аукциона(в формате ЧЧ:ММ, время по МСК!):': ['Укажите время начала аукциона(в формате ЧЧ:ММ, время по МСК!):', 'Specify the start time of the auction (in the format HH:MM, MSC time!):'],
                     'Некорректная дата аукциона. Сегодня': ['Некорректная дата аукциона. Сегодня', 'Incorrect auction date. Today'],
                     'Дата должна быть указана в формате ДД.ММ(например, 12.03)': ['Дата должна быть указана в формате ДД.ММ(например, 12.03)', 'The date should be specified in the format DD.MM(e.g. 12.03)'],
                     'Некорректное время начала аукциона.\n': ['Некорректное время начала аукциона.\n', 'Incorrect auction start time. \n'],
                     'Время должно быть указано в формате ЧЧ:ММ(например, 15:10 или 06:03)': ['Время должно быть указано в формате ЧЧ:ММ(например, 15:10 или 06:03)', 'The time should be specified in HH:MM format(e.g., 15:10 or 06:03)'],
                     'Дата и время окончания:': ['Дата и время окончания:', 'End Date & Time:'],
                     'Дата и время начала:': ['Дата и время начала:', 'Start Date & Time:'],
                     'Минимальный шаг ставки:': ['Минимальный шаг ставки:', 'Minimum bid step:'],
                     'Отлично! Аукцион создан и отправлен на модерацию': ['Отлично! Аукцион создан и отправлен на модерацию', 'Great! The auction has been created and sent for moderation'],
                     'Не удалось добавить предмет. Вы прикрепили меньше 3-х фотографий. Желаете заново добавить предмет?': ['Не удалось добавить предмет. Вы прикрепили меньше 3-х фотографий. Желаете заново добавить предмет?', 'Failed to add an item. You have attached less than 3 photos. Would you like to add the item again?'],
                     'Необходимо прикрепить еще': ['Необходимо прикрепить еще', 'You need to attach'],
                     'фото(прикреплять видео запрещено, они не будут сохранены).': ['фото(прикреплять видео запрещено, они не будут сохранены).', 'photos (attach videos are not allowed, they will not be saved).'],
                     '*Часы:*\n': ['*Часы:*\n', '*Watch:*\n'],
                     '*Аукцион:*\n': ['*Аукцион:*\n', '*Auction:*\n'],
                     'Текущая ставка:': ['Текущая ставка:', 'Current bid:'],
                     'Количество участников:': ['Количество участников:', 'Number of participants:'],
                     '*Вы являетесь лидером аукциона*': ['*Вы являетесь лидером аукциона*', '*You are the auction leader*'],
                     '*Вы не являетесь лидером аукциона*': ['*Вы не являетесь лидером аукциона*', '*You are not the auction leader*'],
                     'Чтобы поднять ставку введите число выше текущей ставки': ['Чтобы поднять ставку введите число выше текущей ставки', 'To raise the bid, enter a number above the current bid'],
                     'Перейти': ['Перейти', 'Open'],
                     'ВАШУ СТАВКУ ПЕРЕБИЛИ\n': ['ВАШУ СТАВКУ ПЕРЕБИЛИ\n', 'YOUR BET HAS BEEN OUTBID\n'],
                     'Необходимо указать целую ставку - количество долларов': ['Необходимо указать целую ставку - количество долларов', 'You need to specify the integer bid- the number of dollars'],
                     'Ставка должна превышать текущую минимум на шаг аукциона': ['Ставка должна превышать текущую минимум на шаг аукциона', 'The bid must exceed the current bid by at least one auction step'],
                     'Ставка должна быть кратна шагу аукциона': ['Ставка должна быть кратна шагу аукциона', 'The bid must be a multiple of the auction step'],
                     '': ['', ''],
                     }


language = {}




def get_message(message_text, user_id):
    return all_text_messages[message_text][language[user_id]]


def escape_markdown(text):
    escape_chars = '_*[]()~`>#+-=|{}!'
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
    return f'{get_message("Ваше имя:", user.id)} {user.username}\n' \
           f'{get_message("Ваш номер телефона:", user.id)} {user.phone}\n' \
        # f'Название вашей компании: {user.company_name}\n' \
    # f'Вебсайт компании: {user.company_website}\n'


def create_user_info_for_moderation(user):
    return f'{get_message("Имя:", user.id)} {user.username}\n' \
           f'{get_message("Номер телефона:", user.id)} {user.phone}\n' \
           f'{get_message("Тег:", user.id)} @{user.nick}\n'
    # f'Название компании: {user.company_name}\n' \
    # f'Вебсайт компании: {user.company_website}\n' \


def create_interest_message(interest):
    return f'Бренд: {interest.brand}\n' \
           f'Минимальная стоимость: {interest.min_price}\n' \
           f'Максимальная стоимость: {interest.max_price}'


def create_auction_message(auction, user_id, is_markdown=False):
    item = get_item(auction.item_id)
    auction_info = f'{get_message("Минимальный шаг:", user_id)} {auction.bid_step}\n' \
                   f'{get_message("Начало:", user_id)} {auction.start_date} {get_message("МСК", user_id)}\n' \
                   f'{get_message("Конец:", user_id)} {auction.duration} {get_message("МСК", user_id)}\n'
    item_info = create_item_text(item, user_id)
    if is_markdown:
        item_info = escape_markdown(item_info)
    return get_message('Предмет:', user_id) + '\n' + item_info + '\n' + get_message('Аукцион:', user_id) + '\n' + auction_info


def create_item_text(item, user_id, is_markdown=False):
    box = 'Нет'
    docs = 'Нет'
    if item.box_available:
        box = 'Да'
    if item.document_available:
        docs = 'Да'
    box = get_message(box, user_id)
    docs = get_message(docs, user_id)
    text = f'{get_message("Бренд:", user_id)} {item.brand}\n' \
           f'{get_message("Референс:", user_id)} {item.reference}\n' \
           f'{get_message("Коробка:", user_id)} ' + box + '\n' \
           f'{get_message("Документы:", user_id)} ' + docs + '\n' \
           f'{get_message("Город:", user_id)} {item.city}\n'
    if get_auction_for_item(item.id) is None or get_auction_for_item(
            item.id).state == 'on_moderation' or get_auction_for_item(item.id).state == 'active':
        text += f'{get_message("Начальная цена, $:", user_id)} {item.price}\n'
    if item.comments is not None:
        text += f'{get_message("Комментарий:", user_id)} {item.comments}\n'
    if is_markdown:
        text = escape_markdown(text)
    return text


def create_photos_for_item(item):
    photos = get_photos_for_item(item.id)
    medias = []
    for photo in photos:
        medias.append(types.InputMediaPhoto(open(photo.name, 'rb')))
    return medias
