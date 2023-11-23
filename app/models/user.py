from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database

class User:
    def __init__(self, username, password, is_admin = False):
        self.db = Database()
        self.username = username
        self.password = helpers.hash_password(password)
        self.is_admin = is_admin

    def insert(self):
        sql = text("""INSERT INTO users (username, password, is_admin) VALUES (:username, :password, :is_admin) RETURNING id""")
        self.id = self.db.execute(sql, {"username" : self.username, "password" : self.password, "is_admin" : self.is_admin})["id"]