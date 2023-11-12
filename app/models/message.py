from datetime import datetime
from sqlalchemy import text
from ..utils import db

class Message:
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
        result = db.connection.execute(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})
        db.connection.commit()
        self.id = result.fetchone()[0]