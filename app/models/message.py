from datetime import datetime
from sqlalchemy import text
from ..utils.db import Database

class Message:
    def __init__(self, thread, sender, text, message_id = None, thread_title = None, sender_name = None, sent_time = None):
        self.db = Database()
        self.thread = thread
        self.sender = sender
        self.text = text
        if sent_time:
            self.sent_time = sent_time
        else:
            self.sent_time = datetime.now()
        self.id = message_id
        self.thread_title = thread_title
        self.sender_name = sender_name

    def insert(self):
        sql = text("""INSERT INTO messages (thread, sender, text, sent_time) VALUES (:thread, :sender, :text, :sent_time) RETURNING id""")
        self.id = self.db.execute(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})["id"]
        return self