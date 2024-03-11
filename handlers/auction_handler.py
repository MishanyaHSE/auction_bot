from datetime import date, time, datetime

from utility.utility import is_positive_number, all_brands, other_brands


class AuctionHandler:
    def __init__(self):
        self.id = 0
        self.bid_step = None
        self.start_date = None
        self.start_time = None
        self.start_date_time = None
        self.duration = 1
        self.end_date_time = None
        self.item_id = None
        self.owner_id = None
        self.states = {
            'getBidStep': 'Укажите минимальный шаг ставки:',
            'getStartDate': 'Укажите дату начала аукциона:',
            'getStartTime': 'Укажите время начала аукциона',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBidStep'

    def create_auction(self, text):
        if self.currentState == 'getBidStep':
            self.currentState = 'getStartDate'
            return self.states['getBidStep']
        elif self.currentState == 'getStartDate':
            if is_positive_number(text):
                self.bid_step = int(text)
                self.currentState = 'getStartTime'
            else:
                return "Необходимо указать целое положительное число\n" + self.states['getBidStep']
            return self.states['getStartDate']
        elif self.currentState == 'getStartTime':
            self.start_date = date(2024, int(text.split('.')[1]), int(text.split('.')[0]))
            self.currentState = 'check'
            return self.states['getStartTime']
        elif self.currentState == 'check':
            # self.start_time = time(int(text.split(':')[0]), int(text.split(':')[1]))
            self.start_time = time(int(text.split(':')[0]), int(text.split(':')[1]))
            end_time = time(int(text.split(':')[0]), int(text.split(':')[1]) + 3)
            self.end_date_time = datetime.combine(self.start_date, end_time)
            self.start_date_time = datetime.combine(self.start_date, self.start_time)
            self.currentState = 'end'
            auction_inf = self.auction_info() + 'Все верно?'
            return auction_inf
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
               f'Дата и время окончания: {self.end_date_time}\n' \
