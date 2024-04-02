from datetime import date, time, datetime, timedelta

from utility.utility import is_positive_number, all_brands, other_brands


AUCTION_LENGTH_MINUTES = 3

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
        self.currentState = 'getStartDate'

    def create_auction(self, text):
        if self.currentState == 'getStartDate':
            self.currentState = 'getStartTime'
            return self.states['getStartDate']
        elif self.currentState == 'getStartTime':
            if len(text) == 5 and text[2] == '.':
                self.start_date = date(2024, int(text.split('.')[1]), int(text.split('.')[0]))
                if self.start_date < datetime.now().date():
                    return f'Некорректная дата аукциона. Сегодня {datetime.now().date()}\n' + self.states['getStartDate']
                self.currentState = 'check'
                return self.states['getStartTime']
            else:
                return 'Дата должна быть указана в формате ДД.ММ(например, 12.03)'
        elif self.currentState == 'check':
            if len(text) == 5 and text[2] == ':':
                hours = text.split(':')[0]
                if hours[0] == 0:
                    hours = hours[1]
                minutes = text.split(':')[1]
                if minutes[0] == 0:
                    minutes = minutes[1]
                hours = int(hours)
                minutes = int(minutes)
                if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                    return "Некорректное время начала аукциона.\n" + self.states['getStartTime']
                self.start_time = time(hours, minutes)
                if minutes + AUCTION_LENGTH_MINUTES <= 59:
                    end_time = time(hours, minutes + AUCTION_LENGTH_MINUTES)
                else:
                    if hours + 1 <= 23:
                        end_time = time(hours + 1, (minutes + AUCTION_LENGTH_MINUTES) % 60)
                    else:
                        end_time = time(0, (minutes + AUCTION_LENGTH_MINUTES) % 60)

                self.end_date_time = datetime.combine(self.start_date, end_time) + timedelta(days=1 if not end_time.hour else 0)
                self.start_date_time = datetime.combine(self.start_date, self.start_time)
                if self.start_date_time <= datetime.now():
                    return "Некорректное время начала аукциона.\n" + self.states['getStartTime']
                self.currentState = 'end'
                auction_inf = self.auction_info() + 'Все верно?'
                return auction_inf
            else:
                return 'Время должно быть указано в формате ЧЧ:ММ(например, 15:10 или 06:03)'
        elif self.currentState == 'end' and text == 'Да':
            self.currentState = 'anotherOne'
            return 'Отлично! Аукцион создан и отправлен на модерацию'
        elif self.currentState == 'end' and text == 'Нет':
            self.currentState = 'getStartDate'
            return self.states['getBidStep']
        return ''

    def auction_info(self):
        return f'Минимальный шаг ставки: {self.bid_step}\n' \
               f'Дата и время начала: {self.start_date_time}\n' \
               f'Дата и время окончания: {self.end_date_time}\n'
