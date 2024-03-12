class RegistrationHandler:

    def __init__(self):
        self.id = 0
        self.surname = None
        self.name = None
        self.phone = None
        self.company_name = None
        self.website = None
        self.states = {
            'getName': 'Пожалуйста, укажите ваше имя:',
            'getSurname': 'Теперь ваша Фамилия:',
            'getPhone': 'Теперь укажите Ваш номер телефона:',
            'getCompanyName': 'Записал, теперь название вашей копании:',
            'getWebsite': 'Сайт вашей компании:',
            'check': 'Давайте проверим, что я все верно записал:',
            'end': ''
        }
        self.nick = None
        self.currentState = 'getName'

    def do_registration(self, text):
        if self.currentState == 'getName':
            self.currentState = 'getSurname'
            return self.states['getName']
        elif self.currentState == 'getSurname':
            self.name = text
            self.currentState = 'getPhone'
            return self.states['getSurname']
        elif self.currentState == 'getPhone':
            self.surname = text
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
            return 'Отлично! Регистрация завершена'
        elif self.currentState == 'end' and text == 'Нет':
            self.currentState = 'getSurname'
            return self.states['getName']
        elif self.currentState == 'end':
            return self.states['check'] + '\n' + self.get_user_profile() + f'Все верно?\n' + 'Необходимо нажать на одну из кнопок.'
        return ''

    def get_user_profile(self):
        return f'Ваше имя: {self.name} {self.surname}\n' \
               f'Ваш номер телефона: {self.phone}\n' \
               f'Название вашей компании: {self.company_name}\n' \
               f'Вебсайт компании: {self.website}\n'
