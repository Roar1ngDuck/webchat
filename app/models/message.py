from datetime import datetime
from sqlalchemy import text
from ..utils.db import Database

class Message:
    def __init__(self):
        self.db = Database()

    @classmethod
    def create(cls, thread, sender, text):
        instance = cls()
        instance.thread = thread
        instance.sender = sender
        instance.text = text
        instance.sent_time = datetime.now()
        return instance

    def insert(self):
        sql = text("""INSERT INTO messages (thread, sender, text, sent_time) VALUES (:thread, :sender, :text, :sent_time) RETURNING id""")
        self.id = self.db.insert_one(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})["id"]