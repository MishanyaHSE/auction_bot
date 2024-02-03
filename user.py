class User:

    def __init__(self, name, surname, phone, company_name, website):
        self.id = 0
        self.surname = surname
        self.name = name
        self.phone = phone
        self.company_name = company_name
        self.website = website

    def __init__(self, surname):
        self.id = 0
        self.surname = surname
        self.name = None
        self.phone = None
        self.company_name = None
        self.website = None
