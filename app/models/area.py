from sqlalchemy import text
from ..utils import helpers, db
from .thread import Thread

class Area:
    @classmethod
    def create_from_db(cls, id):
        sql = text("""SELECT a.topic FROM areas a WHERE a.id = :area_id""")
        result = db.connection.execute(sql, {"area_id" : id})
        topic = result.fetchone()[0]
        instance = cls()
        instance.topic = topic
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
        return db.connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        return db.connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        result = db.connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
        if result != None:
            return helpers.time_ago(result)
        return None
        
    @property
    def threads(self): # TODO: Make create_from_sql_result for all models to not be used. Get las_message with SQL directly.
        sql = text("""SELECT t.id,t.area,t.title,a.topic FROM threads t, areas a WHERE t.area = :area_id AND t.area = a.id""")
        result = db.connection.execute(sql, {"area_id" : self.id}).fetchall()
        threads:list[Thread] = []
        for thread_result in result:
            thread = Thread()
            thread.id = thread_result[0]
            thread.area = thread_result[1]
            thread.area_name = thread_result[3]
            thread.title = thread_result[2]
            threads.append(thread)
        return threads
    
    def insert(self):
        sql = text("""INSERT INTO areas (topic) VALUES (:topic) RETURNING id""")
        result = db.connection.execute(sql, {"topic" : self.topic})
        db.connection.commit()
        self.id = result.fetchone()[0]