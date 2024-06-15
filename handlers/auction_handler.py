from datetime import date, time, datetime, timedelta
from utility.utility import is_positive_number, all_brands, other_brands, get_message
from utility.constants import AUCTION_LENGTH_MINUTES


class AuctionHandler:
    def __init__(self):
        self.id = 0
        self.bid_step = 100
        self.start_date = None
        self.start_time = None
        self.start_date_time = None
        self.duration = 1
        self.end_date_time = None
        self.item_id = None
        self.owner_id = None
        self.states = {
            'getBidStep': 'Укажите минимальный шаг ставки:',
            'getStartDate': 'Укажите дату начала аукциона(в формате ДД.ММ):',
            'getStartTime': 'Укажите время начала аукциона(в формате ЧЧ:ММ, время по МСК!):',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'check'

    def create_auction(self, text, user_id):
        if self.currentState == 'getStartDate':
            self.currentState = 'getStartTime'
            return get_message(self.states['getStartDate'], user_id)
        elif self.currentState == 'getStartTime':
            if len(text) == 5 and text[2] == '.':
                self.start_date = date(2024, int(text.split('.')[1]), int(text.split('.')[0]))
                if self.start_date < datetime.now().date():
                    return f'{get_message("Некорректная дата аукциона.Сегодня", user_id)} {datetime.now().date()}\n' + get_message(
                        self.states['getStartDate'], user_id)
                self.currentState = 'check'
                return get_message(self.states['getStartTime'], user_id)
            else:
                return get_message('Дата должна быть указана в формате ДД.ММ(например, 12.03)', user_id)
        elif self.currentState == 'check':
            # if len(text) == 5 and text[2] == ':':
            #     hours = text.split(':')[0]
            #     if hours[0] == 0:
            #         hours = hours[1]
            #     minutes = text.split(':')[1]
            #     if minutes[0] == 0:
            #         minutes = minutes[1]
            #     hours = int(hours)
            #     minutes = int(minutes)
            #     if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
            #         return get_message("Некорректное время начала аукциона.\n", user_id) + get_message(
            #             self.states['getStartTime'], user_id)
            #     self.start_time = time(hours, minutes)
            #     if minutes + AUCTION_LENGTH_MINUTES <= 59:
            #         end_time = time(hours, minutes + AUCTION_LENGTH_MINUTES)
            #     else:
            #         if hours + 1 <= 23:
            #             end_time = time(hours + 1, (minutes + AUCTION_LENGTH_MINUTES) % 60)
            #         else:
            #             end_time = time(0, (minutes + AUCTION_LENGTH_MINUTES) % 60)
            #
            #     self.end_date_time = datetime.combine(self.start_date, end_time) + timedelta(
            #         days=1 if not end_time.hour else 0)
            #     self.start_date_time = datetime.combine(self.start_date, self.start_time)
            #     if self.start_date_time <= datetime.now():
            #         return get_message("Некорректное время начала аукциона.\n", user_id) + get_message(
            #             self.states['getStartTime'], user_id)
            #     self.currentState = 'end'
            #     auction_inf = self.auction_info(user_id) + get_message('Все верно?', user_id)
            #     return auction_inf
            # else:
            #     return get_message('Время должно быть указано в формате ЧЧ:ММ(например, 15:10 или 06:03)', user_id)
            self.start_date = datetime.now().date()
            self.start_time = time(int(datetime.now().hour), (datetime.now().minute))
            self.start_date_time = datetime.combine(self.start_date, self.start_time)
            self.end_date_time = self.start_date_time + timedelta(minutes=AUCTION_LENGTH_MINUTES - 1)
            self.currentState = 'end'
            auction_inf = self.auction_info(user_id) + get_message('Все верно?', user_id)
            return auction_inf
        elif self.currentState == 'end' and text in ['Да', 'Yes']:
            self.currentState = 'anotherOne'
            return get_message('Отлично! Аукцион создан и опубликован', user_id)
        elif self.currentState == 'end' and text in ['Нет', 'No']:
            self.currentState = 'check'
            return get_message(self.states['getBidStep'], user_id)
        return ''

    def auction_info(self, user_id):
        return f'{get_message("Минимальный шаг ставки:", user_id)} {self.bid_step}\n' \
               f'{get_message("Дата и время начала:", user_id)} {self.start_date_time}\n' \
               f'{get_message("Дата и время окончания:", user_id)} {self.end_date_time}\n'
