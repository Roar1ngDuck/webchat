from sqlalchemy import text
from datetime import datetime
from ..utils import helpers
from ..utils.db import Database
from .message import Message

class Thread:
    def __init__(self, area, title, owner_id, id = None, area_name = None):
        self.db = Database()
        self.area = area
        self.title = title
        self.id = id
        self.area_name = area_name
        self.owner_id = owner_id
        self.messages:list[Thread] = []

    @classmethod
    def create_from_db(cls, id):
        sql = text("""
SELECT m.id, t.title, t.owner_id, u.id as sender_id, u.username, m.text, m.image_url, m.sent_time, t.area, a.topic FROM messages m 
JOIN users u ON m.sender = u.id 
JOIN threads t ON m.thread = t.id 
JOIN areas a on t.area = a.id WHERE m.thread = :thread_id ORDER BY m.sent_time""")
        instance = None
        for row in Database().fetch_all(sql, {"thread_id" : id}):
            if not instance:
                instance = cls(row["area"], row["title"], row["owner_id"], id, row["topic"])
            instance.messages.append(Message(id, row["sender_id"], row["text"], image_url=row["image_url"], message_id=row["id"], thread_title=row["title"], sender_name=row["username"], sent_time=row["sent_time"]))
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
        sql = text("""INSERT INTO threads (area, title, owner_id) VALUES (:area, :title, :owner_id) RETURNING id""")
        self.id = self.db.execute(sql, {"area" : self.area, "title" : self.title, "owner_id" : self.owner_id})["id"]
        return self