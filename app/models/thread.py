from sqlalchemy import text
from datetime import datetime
from ..utils import helpers, db
from .message import Message

class Thread:
    @classmethod
    def create_from_db(cls, id):
        instance = cls()
        instance.id = id
        sql = text("""
SELECT m.id, t.title, u.id as sender_id, u.username, m.text, m.sent_time, t.area, a.topic FROM messages m 
JOIN users u ON m.sender = u.id 
JOIN threads t ON m.thread = t.id 
JOIN areas a on t.area = a.id WHERE m.thread = :thread_id""")
        instance.messages:list[Thread] = []
        for row in db.connection.execute(sql, {"thread_id" : id}).mappings():
            instance.title = row["title"]
            instance.area = row["area"]
            instance.area_name = row["topic"]

            message = Message()
            message.id = row["id"]
            message.thread = id
            message.thread_title = row["title"]
            message.sender = row["sender_id"]
            message.sender_name = row["username"]
            message.text = row["text"]
            message.sent_time = datetime.strftime(row["sent_time"], "%d.%m.%Y %H:%M")
            
            instance.messages.append(message)
        return instance

    @classmethod
    def create(cls, area, title):
        instance = cls()
        instance.area = area
        instance.title = title
        return instance
    
    @property
    def message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread = :thread_id""")
        return db.connection.execute(sql, {"thread_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread = :thread_id""")
        result = db.connection.execute(sql, {"thread_id" : self.id}).fetchone()[0]
        if result != None:
            self.last_message = helpers.time_ago(result)
        return result
    
    def insert(self):
        sql = text("""INSERT INTO threads (area, title) VALUES (:area, :title) RETURNING id""")
        result = db.connection.execute(sql, {"area" : self.area, "title" : self.title})
        db.connection.commit()
        self.id = result.fetchone()[0]