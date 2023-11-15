from sqlalchemy import text
from datetime import datetime
from ..utils import helpers
from ..utils.db import Database
from .message import Message

class Thread:
    def __init__(self):
        self.db = Database()

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
        for row in instance.db.fetch_all(sql, {"thread_id" : id}):
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
        return self.db.fetch_one(sql, {"thread_id" : self.id})["count"]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread = :thread_id""")
        result = self.db.fetch_one(sql, {"thread_id" : self.id})["max"]
        if result != None:
            return helpers.time_ago(result)
        return result
    
    def insert(self):
        sql = text("""INSERT INTO threads (area, title) VALUES (:area, :title) RETURNING id""")
        self.id = self.db.insert_one(sql, {"area" : self.area, "title" : self.title})["id"]