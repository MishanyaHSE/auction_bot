from utility.utility import is_positive_number, all_brands, other_brands


class InterestsHandler:

    def __init__(self):
        self.id = 0
        self.minPrice = None
        self.maxPrice = None
        self.brand = None
        self.states = {
            'getBrand': 'Укажите интересующий вас бренд:',
            'getMinPrice': 'Укажите минимальную стоимость(в долларах) часов данного бренда, которые вам были бы интересны:',
            'getMaxPrice': 'Укажите максимальную стоимость:',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBrand'

    def interest_survey(self, text):
        if self.currentState == 'getBrand':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        elif self.currentState == 'getMinPrice':
            if text in all_brands or text in other_brands:
                self.brand = text
                self.currentState = 'getMaxPrice'
                return self.states['getMinPrice']
            else:
                return 'Необходимо выбрать бренд из списка'
        elif self.currentState == 'getMaxPrice':
            if is_positive_number(text):
                self.minPrice = int(text)
                self.currentState = 'check'
                return self.states['getMaxPrice']
            else:
                return 'Необходимо указать целое число - цену в долларах.\n' + self.states['getMinPrice']
        elif self.currentState == 'check':
            if is_positive_number(text):
                self.maxPrice = int(text)
                if self.maxPrice >= self.minPrice:
                    user_information = self.states['check'] + '\n' + self.interest_info() + f'Все верно?'
                    self.currentState = 'end'
                    return user_information
                else:
                    return "Максимальная цена должна быть больше или равна минимальной.\n" + self.states['getMaxPrice']
            else:
                return 'Необходимо указать целое число - цену в долларах.\n' + self.states['getMaxPrice']
        elif self.currentState == 'end' and text == 'Да':
            self.currentState = 'anotherOne'
            return 'Отлично! Фильтр объявлений добавлен. Желаете создать еще один?'
        elif self.currentState == 'end' and text == 'Нет':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        elif self.currentState == 'anotherOne' and text == 'Да':
            self.currentState = 'getMinPrice'
            return self.states['getBrand']
        return ''

    def interest_info(self):
        return f'Бренд: {self.brand}\n' \
               f'Минимальная стоимость: {self.minPrice}\n' \
               f'Максимальная стоимость: {self.maxPrice}\n'
