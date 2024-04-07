class RegistrationHandler:

    def __init__(self):
        self.id = 0
        self.name = None
        self.phone = None
        self.company_name = None
        self.website = None
        self.nick = None
        self.ban = None
        self.states = {
            'getName': 'Пожалуйста, укажите ваше имя:',
            'getPhone': 'Теперь укажите Ваш номер телефона:',
            'getCompanyName': 'Записал, теперь название вашей компании:',
            'getWebsite': 'Сайт вашей компании:',
            'check': 'Давайте проверим, что я все верно записал:',
            'rules': f'*Правила:*\n- Если вы назначили ставку в аукционе, то вы должны купить часы по этой ставке\n- Если вы выставляете часы на аукцион, то начальной ценой должна быть цена, за которую вы готовы продать данные часы\n- Выставлять на аукцион можно только оригинальные часы и прозрачной историей\n- Нужно предупреждать в описании о всех серьезных дефектах (забоинах, ржавчине, изменении хода более 15сек/сутки, неработоспособности и тд)',
            'end': ''
        }
        self.currentState = 'getName'

    def do_registration(self, text):
        if self.currentState == 'getName':
            self.currentState = 'getPhone'
            return self.states['getName']
        elif self.currentState == 'getPhone':
            self.name = text
            self.currentState = 'getCompanyName'
            return self.states['getPhone']
        elif self.currentState == 'getCompanyName':
            self.phone = text
            self.currentState = 'getWebsite'
            return self.states['getCompanyName']
        elif self.currentState == 'getWebsite':
            self.company_name = text
            self.currentState = 'check'
            return self.states['getWebsite']
        elif self.currentState == 'check':
            self.website = text
            user_information = self.states['check'] + '\n' + self.get_user_profile() + f'Все верно?'
            self.currentState = 'end'
            return user_information
        elif self.currentState == 'end' and text == 'Да':
            self.currentState = 'rules'
            return self.states['rules']
        elif self.currentState == 'end' and text == 'Нет':
            self.currentState = 'getSurname'
            return self.states['getName']
        elif self.currentState == 'end':
            return self.states['check'] + '\n' + self.get_user_profile() + f'Все верно?\n' + 'Необходимо нажать на одну из кнопок.'
        elif self.currentState == 'rules' and text == 'Принять':
            return 'Отлично! Регистрация завершена. Когда модератор одобрит заявку на вступление, Вам придет уведомление'
        elif self.currentState == 'rules':
            return 'Чтобы получить доступ к боту, вы должны принять правила использования бота. Отправьте "Принять" или нажмите на кнопку.\n\n' + self.states['rules']
        return ''

    def get_user_profile(self):
        return f'Ваше имя: {self.name}\n' \
               f'Ваш номер телефона: {self.phone}\n' \
               f'Название вашей компании: {self.company_name}\n' \
               f'Вебсайт компании: {self.website}\n'
