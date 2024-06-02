from utility.utility import all_brands, other_brands, is_positive_number, get_message


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
        self.city = None
        self.states = {
            'getBrand': 'Укажите бренд часов, которые хотите выставить на аукцион:',
            'getReference': 'Референс часов:',
            'getPrice': 'Стартовая цена в $:',
            'getPhoto': f'Добавьте от 3 до 10 фото часов. Постарайтесь, чтобы на фото были видны следующие объекты:\n'
                        f'-циферблат(обязательно)\n'
                        f'-оборотная сторона(обязательно)\n'
                        f'-застежка(обязательно)\n'
                        f'-обратная сторона застежки\n'
                        f'-коробка(при наличии)\n'
                        f'-документы(при наличии)\n',
            'getBox_available': 'Имеется ли коробка от часов:("Да"/"Нет")',
            'getDocument_available': 'Документы от часов:("Да"/"Нет")',
            'getLocation': 'Укажите город, из которого будет произвдена отправка предмета:',
            'getComments': 'Опишите дефекты своих часов, если их нет, нажмите "Пропустить":',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.currentState = 'getBrand'

    def create_item(self, text, user_id):
        if self.currentState == 'getBrand':
            self.currentState = 'getReference'
            return get_message(self.states['getBrand'], user_id)
        elif self.currentState == 'getReference':
            self.brand = text
            if self.brand not in all_brands and self.brand not in other_brands:
                self.currentState = 'getBrand'
                return get_message('Выберете из ячеек', user_id), get_message(self.states['getBrand'], user_id)
            self.currentState = 'getPrice'
            return get_message(self.states['getReference'], user_id)
        elif self.currentState == 'getPrice':
            self.reference = text
            self.currentState = 'getPhoto'
            return get_message(self.states['getPrice'], user_id)
        elif self.currentState == 'getPhoto':
            if is_positive_number(text):
                self.price = text
                self.currentState = 'getBox_available'
                return get_message(self.states['getPhoto'], user_id)
            return get_message('Цена должна быть целым положительным числом!\n', user_id) + get_message(
                self.states['getPrice'], user_id)
        elif self.currentState == 'getBox_available':
            self.currentState = 'getDocument_available'
            return get_message(self.states['getBox_available'], user_id)
        elif self.currentState == 'getDocument_available':
            if text in ['Yes', 'Да']:
                self.box_available = True
            elif text in ['Нет', 'No']:
                self.box_available = False
            else:
                return get_message('Необходимо выбрать Да/Нет', user_id)
            self.currentState = 'getLocation'
            return get_message(self.states['getDocument_available'], user_id)
        elif self.currentState == 'getLocation':
            if text in ['Yes', 'Да']:
                self.document_available = True
            elif text in ['Нет', 'No']:
                self.document_available = False
            else:
                return get_message('Необходимо выбрать Да/Нет', user_id)
            self.currentState = 'getComments'
            return get_message(self.states['getLocation'], user_id)
        elif self.currentState == 'getComments':
            if len(text) > 30:
                return get_message(
                    'Вы ввели слишком длинное название. Введите название города, из которого отправите часы, комментарии можно указать позже',
                    user_id)
            else:
                self.currentState = 'check'
                self.city = text
                return get_message(self.states['getComments'], user_id)
        elif self.currentState == 'check':
            self.comments = text
            if self.comments in ['Пропустить', 'Skip']:
                self.comments = None
            auction_inf = get_message(self.states['check'], user_id) + '\n' + self.auction_info(user_id) + get_message(
                'Все верно?', user_id)
            self.currentState = 'end'
            return auction_inf
        elif self.currentState == 'end' and (text == 'Да' or text == 'Yes'):
            self.currentState = 'anotherOne'
            return get_message('Отлично! Предмет добавлен. Желаете добавить еще один?', user_id)
        elif self.currentState == 'end' and (text == 'Нет' or text == 'No'):
            self.currentState = 'getReference'
            self.photos.clear()
            return self.states['getBrand']
        elif self.currentState == 'anotherOne' and (text == 'Да' or text == 'Yes'):
            self.currentState = 'getReference'
            return self.states['getBrand']
        return ''

    def auction_info(self, user_id):
        box = 'Нет'
        docs = 'Нет'
        if self.box_available:
            box = 'Да'
        if self.document_available:
            docs = 'Да'
        box = get_message(box, user_id)
        docs = get_message(docs, user_id)
        text = f'{get_message("Бренд:", user_id)} {self.brand}\n' \
               f'{get_message("Референс:", user_id)} {self.reference}\n' \
               f'{get_message("Коробка:", user_id)} ' + box + '\n' \
                                                              f'{get_message("Документы:", user_id)} ' + docs + '\n' \
                                                                                                                f'{get_message("Город:", user_id)} {self.city}\n'
        if self.comments is not None:
            text += f'{get_message("Комментарий:", user_id)} {self.comments}\n'
        return text

    def append_photo(self, file_info):
        self.photos.append(file_info)
