from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database

class User:
    def __init__(self):
        self.db = Database()

    @classmethod
    def create(cls, username, password):
        instance = cls()
        instance.username = username
        instance.password = helpers.hash_password(password)
        return instance

    def insert(self):
        sql = text("""INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id""")
        self.id = self.db.insert_one(sql, {"username" : self.username, "password" : self.password})["id"]