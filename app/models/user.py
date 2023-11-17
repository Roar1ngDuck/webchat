from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database

class User:
    def __init__(self, username, password):
        self.db = Database()
        self.username = username
        self.password = helpers.hash_password(password)

    def insert(self):
        sql = text("""INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id""")
        self.id = self.db.insert_one(sql, {"username" : self.username, "password" : self.password})["id"]