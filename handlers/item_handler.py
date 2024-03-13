from utility.utility import all_brands, other_brands


class NewItem:
    def __init__(self):
        self.id = 0
        self.brand = None
        self.reference = None
        self.price = None
        self.photos = []
        self.box_available = None
        self.document_available = None
        self.comments = None
        self.states = {
            'getBrand': 'Укажи бренд часов, которые хотите выставить на аукцион:',
            'getReference': 'Референс часов:',
            'getPrice': 'Цена (в долларах):',
            'getPhoto': f'Добавьте от 3 до 10 фото часов. Постарайтесь, чтобы на фото были видны следующие объекты:\n'
                        f'-циферблат(обязательно)\n'
                        f'-оборотная сторона(обязательно)\n'
                        f'-застежка(обязательно)\n'
                        f'-обратная сторона застежки\n'
                        f'-коробка(при наличии)\n'
                        f'-документы(при наличии)\n',
            'getBox_available': 'Имеется ли коробка от часов:',
            'getDocument_available': 'Документы от часов:',
            'getComments': 'Можете написать коментарий к часам, если не хотите, напишите "нет":',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBrand'

    def create_item(self, text):
        if self.currentState == 'getBrand':
            self.currentState = 'getReference'
            return self.states['getBrand']
        elif self.currentState == 'getReference':
            self.brand = text
            if self.brand not in all_brands and self.brand not in other_brands:
                self.currentState = 'getBrand'
                return 'Выберете из ячеек', self.states['getBrand']
            self.currentState = 'getPrice'
            return self.states['getReference']
        elif self.currentState == 'getPrice':
            self.reference = text
            self.currentState = 'getPhoto'
            return self.states['getPrice']
        elif self.currentState == 'getPhoto':
            self.price = text
            self.currentState = 'getBox_available'
            return self.states['getPhoto']
        elif self.currentState == 'getBox_available':
            self.currentState = 'getDocument_available'
            return self.states['getBox_available']
        elif self.currentState == 'getDocument_available':
            if text == 'Да':
                self.box_available = True
            elif text == 'Нет':
                self.box_available = False
            elif text == '':
                return ''
            else:
                return 'Необходимо выбрать Да/Нет'
            self.currentState = 'getComments'
            return self.states['getDocument_available']
        elif self.currentState == 'getComments':
            if text == 'Да':
                self.document_available = True
            elif text == 'Нет':
                self.document_available = False
            elif text == '':
                pass
            else:
                return 'Необходимо выбрать Да/Нет'
            self.currentState = 'check'
            return self.states['getComments']
        elif self.currentState == 'check':
            self.comments = text
            auction_inf = self.states['check'] + '\n' + self.auction_info() + 'Все верно?'
            self.currentState = 'end'
            return auction_inf
        elif self.currentState == 'end' and text == 'Да':
            self.currentState = 'anotherOne'
            return 'Отлично! Предмет добавлен. Желаете добавить еще один?'
        elif self.currentState == 'end' and text == 'Нет':
            self.currentState = 'getReference'
            self.photos.clear()
            return self.states['getBrand']
        elif self.currentState == 'anotherOne' and text == 'Да':
            self.currentState = 'getReference'
            return self.states['getBrand']
        return ''

    def auction_info(self):
        box = 'Нет'
        docs = 'Нет'
        if self.document_available:
            docs = 'Да'
        if self.box_available:
            box = 'Да'
        return f'Бренд: {self.brand}\n' \
               f'Референс: {self.reference}\n' \
               f'Цена: {self.price}\n' \
               f'Коробка: {box}\n' \
               f'Документы: {docs}\n' \
               f'Коментарий: {self.comments}\n'

    def append_photo(self, file_info):
        self.photos.append(file_info)
