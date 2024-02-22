class NewItem:
    def __init__(self):
        self.id = 0
        self.brand = None
        self.reference = None
        self.price = None
        self.photo = None
        self.box_availible = None
        self.document_availible = None
        self.comments = None
        self.states = {
            'getBrand': 'Укажи бренд часов, которые хотите выставить на аукцион:',
            'getReference': 'Референс часов:',
            'getPrice': 'Цена (в долларах):',
            'getPhoto': 'Добавьте фото часов',
            'getBox_availible': 'Имеется ли коробка от часов:',
            'getDocument_availible': 'Документы от часов:',
            'getComments': 'Можете написать коментарий к часам, если не хотите, напишите "нет":',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBrand'
        self.all_brand = ['Cartier', 'Breguet', 'Vacheron Constantin', 'Daniel Wellington', 'Audemars Piguet',
                     'Jaeger-lecoultre', 'Chanel', 'Rolex', 'Franck Muller', 'Patek Philippe', 'Ulysse Nardin',
                     'Hublot', 'Chopard', 'Parmigiani Fleurier', 'H. Moser & Cie', 'Montblanc', 'Jaeger-LeCoultre',
                     'Gérald Genta', 'Omega', 'Breitling', 'Bovet', 'Urwerk', 'Gérald Genta', 'Piaget', 'Longines',
                     'Iwc', 'Bulgari', 'Blancpain', 'Tudor', 'TAG Heuer', 'Girard-Perregaux', 'Arnold & Son',
                     'Roger Dubuis', 'Ikepod', 'Romain Jerome', 'Harry Winston', 'Cvstos', 'Alain Silberstein',
                     'Zenith', 'A. Lange & Söhne', 'A. Lange & Söhne', 'Corum', 'Panerai', 'H. Moser & Cie',
                     'Chronoswiss', 'Glashütte Original', 'MB&F', 'Glashütte Original', 'Dewitt', 'Trilobe',
                     'Bell & Ross', 'Junghans', 'Maurice Lacroix']

    def create_item(self, text):
        if self.currentState == 'getBrand':
            self.currentState = 'getReference'
        elif self.currentState == 'getReference':
            self.brand = text
            if self.brand not in self.all_brand:
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
            self.currentState = 'getBox_availible'
            return self.states['getPhoto']
        elif self.currentState == 'getBox_availible':
            self.photo = text
            self.currentState = 'getDocument_availible'
            return self.states['getBox_availible']
        elif self.currentState == 'getDocument_availible':
            self.box_availible = text
            self.currentState = 'getComments'
            return self.states['getDocument_availible']
        elif self.currentState == 'getComments':
            self.document_availible = text
            self.currentState = 'check'
            return self.states['getComments']
        elif self.currentState == 'check':
            self.comments = text
            auction_inf = self.states['check'] + '\n' + self.auction_info() + 'Все верно?'
            self.currentState = 'end'
            return auction_inf
        elif self.currentState == 'end' and text == 'да':
            self.currentState = 'anotherOne'
            return 'Отлично! Аукцион создан. Желаете создать еще один?'
        elif self.currentState == 'end' and text == 'нет':
            self.currentState = 'getReference'
            return self.states['getBrand']
        elif self.currentState == 'anotherOne' and text == 'да':
            self.currentState = 'getReference'
            return self.states['getBrand']
        return ''

    def auction_info(self):
        return f'Бренд: {self.brand}\n' \
               f'Референс: {self.reference}\n' \
               f'Цена: {self.price}\n' \
               f'Фото: {self.photo}\n'\
               f'Коробка: {self.box_availible}\n' \
               f'Документы: {self.document_availible}\n' \
               f'Коментарий: {self.comments}\n'
