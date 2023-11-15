from sqlalchemy import text
from ..utils import helpers
from ..utils.db import Database
from .thread import Thread

class Area:
    def __init__(self):
        self.db = Database()

    @classmethod
    def create_from_db(cls, id):
        instance = cls()
        sql = text("""SELECT a.topic FROM areas a WHERE a.id = :area_id""")
        result = instance.db.fetch_one(sql, {"area_id" : id})["topic"]
        instance.topic = result
        instance.id = id
        return instance
    
    @classmethod
    def create(cls, topic):
        instance = cls()
        instance.topic = topic
        return instance

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
        result = self.db.fetch_one(sql, {"area_id" : self.id})["max"]
        if result != None:
            return helpers.time_ago(result)
        return None
        
    @property
    def threads(self):
        sql = text("""SELECT t.id,t.area,t.title,a.topic FROM threads t, areas a WHERE t.area = :area_id AND t.area = a.id""")
        result = self.db.fetch_all(sql, {"area_id" : self.id})
        threads:list[Thread] = []
        for thread_result in result:
            thread = Thread()
            thread.id = thread_result["id"]
            thread.area = thread_result["area"]
            thread.area_name = thread_result["topic"]
            thread.title = thread_result["title"]
            threads.append(thread)
        return threads
    
    def insert(self):
        sql = text("""INSERT INTO areas (topic) VALUES (:topic) RETURNING id""")
        self.id = self.db.insert_one(sql, {"topic" : self.topic})["id"]