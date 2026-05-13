from src.db import DB_connection

class User:
    def __init__(self, username, id):
        self.username = username
        self.id = id

    @classmethod
    def create(cls, db: DB_connection):
        username = input('Введіть унікальний username: ')

        id = db.create_user(username)
        if id is None:
            return None

        return cls(username, id)

    @classmethod
    def login(cls, db: DB_connection):
        username = input('Введіть ваш username: ')

        id = db.find_user(username)

        if id is None:
            return None

        return cls(username, id)
