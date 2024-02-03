class InterestsHandler:

    def __init__(self):
        self.id = 0
        self.minPrice = None
        self.maxPrice = None
        self.brand = None
        self.states = {
            'getBrand': 'Укажите интересующий вас бренд:',
            'getMinPrice': 'Минимальную стоимость(в долларах) часов данного бренда, которые вам были бы интересны:',
            'getMaxPrice': 'Максимальную стоимость:',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBrand'

    def interest_survey(self, text):
        if self.currentState == 'getBrand':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        elif self.currentState == 'getMinPrice':
            self.brand = text
            self.currentState = 'getMaxPrice'
            return self.states['getMinPrice']
        elif self.currentState == 'getMaxPrice':
            self.minPrice = text
            self.currentState = 'check'
            return self.states['getMaxPrice']
        elif self.currentState == 'check':
            self.maxPrice = text
            user_information = self.states['check'] + '\n' + self.interest_info() + f'Все верно?'
            self.currentState = 'end'
            return user_information
        elif self.currentState == 'end' and text == 'да':
            self.currentState = 'anotherOne'
            return 'Отлично! Фильтр объявлений добавлен. Желаете создать еще один?'
        elif self.currentState == 'end' and text == 'нет':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        elif self.currentState == 'anotherOne' and text == 'да':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        return ''

    def interest_info(self):
        return f'Бренд: {self.brand}\n' \
               f'Минимальная стоимость: {self.minPrice}\n' \
               f'Максимальная стоимость: {self.maxPrice}\n'
