from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database
from .thread import Thread

class Area:
    def __init__(self, topic, is_secret = False, id = None):
        self.db = Database()
        self.topic = topic
        self.is_secret = is_secret
        self.id = id

    @classmethod
    def create_from_db(cls, area_id, user_id):
        sql = text("""
        SELECT a.topic, a.is_secret
        FROM areas a
        LEFT JOIN secret_area_privileges sap ON a.id = sap.area_id AND sap.user_id = :user_id
        WHERE a.id = :area_id AND (a.is_secret = false OR sap.user_id IS NOT NULL)
        """)

        result = Database().fetch_one(sql, {"area_id": area_id, "user_id": user_id})

        if result:
            instance = cls(result["topic"], result["is_secret"], area_id)
            return instance
        else:
            return None
    
    @property
    def thread_count(self):
        sql = text("""SELECT COUNT(*) FROM threads t WHERE t.area = :area_id""")
        return self.db.fetch_one(sql, {"area_id" : self.id})["count"]
    
    @property
    def message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        return self.db.fetch_one(sql, {"area_id" : self.id})["count"]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        last_message_time = self.db.fetch_one(sql, {"area_id" : self.id})["max"]
        if last_message_time != None:
            return helpers.time_ago(last_message_time)
        return None
        
    @property
    def threads(self):
        sql = text("""SELECT t.id,t.area,t.title,a.topic FROM threads t, areas a WHERE t.area = :area_id AND t.area = a.id""")
        threads:list[Thread] = []
        for thread_result in self.db.fetch_all(sql, {"area_id" : self.id}):
            thread = Thread(thread_result["area"], thread_result["title"], thread_result["id"], thread_result["topic"])
            threads.append(thread)
        return threads
    
    def insert(self):
        sql = text("""INSERT INTO areas (topic, is_secret) VALUES (:topic, :is_secret) RETURNING id""")
        self.id = self.db.insert_one(sql, {"topic" : self.topic, "is_secret" : self.is_secret})["id"]
        return self