import utility.utility
from utility.utility import all_text_messages, get_message, language

class RegistrationHandler:

    def __init__(self):
        self.id = 0
        self.name = None
        self.phone = None
        self.company_name = None
        self.website = None
        self.nick = None
        self.ban = None
        self.language = None
        self.states = {
            'getLanguage': 'Пожалуйста, выберите язык бота/Please, select bot language:',
            'getName': 'Пожалуйста, укажите ваше имя:',
            'getPhone': 'Теперь укажите Ваш номер телефона:',
            # 'getCompanyName': 'Записал, теперь название вашей компании:',
            # 'getWebsite': 'Сайт вашей компании:',
            'check': 'Давайте проверим, что я все верно записал:',
            'rules': f'*Правила:*\n- Если вы назначили ставку в аукционе, то вы должны купить часы по этой ставке\n- Если вы выставляете часы на аукцион, то начальной ценой должна быть цена, за которую вы готовы продать данные часы\n- Выставлять на аукцион можно только оригинальные часы и прозрачной историей\n- Нужно предупреждать в описании о всех серьезных дефектах (забоинах, ржавчине, изменении хода более 15сек/сутки, неработоспособности и тд)',
            'end': ''
        }
        self.currentState = 'getLanguage'

    def do_registration(self, text, id):
        if self.currentState == 'getLanguage':
            self.currentState = 'getName'
            return self.states['getLanguage']
        elif self.currentState == 'getName':
            if text == 'Русский':
                self.language = 0
                utility.utility.language[id] = 0
            elif text == 'English':
                self.language = 1
                utility.utility.language[id] = 1
            else:
                return self.states['getLanguage'] + '\nНажмите на одну из кнопок/Choose language with buttons'
            self.currentState = 'getPhone'
            return get_message(self.states['getName'], id)
            # return self.states['getName']
        elif self.currentState == 'getPhone':
            self.name = text
            self.currentState = 'check'
            return get_message(self.states['getPhone'], id)
        elif self.currentState == 'getCompanyName':
            self.phone = text
            self.currentState = 'getWebsite'
            return get_message(self.states['getCompanyName'], id)
        # elif self.currentState == 'getWebsite':
        #     self.company_name = text
        #     self.currentState = 'check'
        #     return self.states['getWebsite']
        elif self.currentState == 'check':
            # self.website = text
            self.phone = text
            user_information = get_message(self.states['check'], id) + '\n' + self.get_user_profile(id) + get_message('Все верно?', id)
            self.currentState = 'end'
            return user_information
        elif self.currentState == 'end' and (text == 'Да' or text == 'Yes'):
            self.currentState = 'rules'
            return get_message(self.states['rules'], id)
        elif self.currentState == 'end' and (text == 'Нет' or text == 'No'):
            self.currentState = 'getPhone'
            return get_message(self.states['getName'], id)
        elif self.currentState == 'end':
            return get_message(self.states['check'], id) + '\n' + self.get_user_profile(id) + get_message('Все верно?', id) + '\n' + get_message('Необходимо нажать на одну из кнопок.', id)
        elif self.currentState == 'rules' and (text == 'Принять' or text == 'Accept'):
            return get_message('Отлично! Регистрация завершена. Когда модератор одобрит заявку на вступление, Вам придет уведомление', id)
        elif self.currentState == 'rules':
            return get_message('Чтобы получить доступ к боту, вы должны принять правила использования бота. Отправьте "Принять" или нажмите на кнопку.\n\n', id) + get_message(self.states['rules'], id)
        return ''

    def get_user_profile(self, id):
        s1 = 'Ваше имя:'
        s2 = 'Ваш номер телефона:'
        return f'{get_message(s1, id)} {self.name}\n' \
               f'{get_message(s2, id)} {self.phone}\n' \
               # f'Название вашей компании: {self.company_name}\n' \
               # f'Вебсайт компании: {self.website}\n'
