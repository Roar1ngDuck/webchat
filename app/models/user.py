from sqlalchemy import text
from ..utils import helpers, db

class User:
    @classmethod
    def create(cls, username, password):
        instance = cls()
        instance.username = username
        instance.password = helpers.hash_password(password)
        return instance

    def insert(self):
        sql = text("""INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id""")
        result = db.connection.execute(sql, {"username" : self.username, "password" : self.password})
        db.connection.commit()
        self.id = result.fetchone()[0]