from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import app
from sqlalchemy import text

class Message:
    def __init__(self, thread:int, sender:int, text:str):
        self.thread = thread
        self.sender = sender
        self.text = text
        self.sent_time = datetime.now()

    def insert(self):
        sql = text("""INSERT INTO messages (thread, sender, text, sent_time) VALUES (:thread, :sender, :text, :sent_time)""")
        app.db.session.execute(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})
        app.db.session.commit()

class Thread:
    def __init__(self, area:int, title:str):
        self.area = area
        self.title = title

    def insert(self):
        sql = text("""INSERT INTO threads (area, title) VALUES (:area, :title)""")
        app.db.session.execute(sql, {"area" : self.area, "title" : self.title})
        app.db.session.commit()

class Area:
    def __init__(self, topic:str, id=0):
        self.topic = topic
        self.id = id

    def query_thread_count(self):
        sql = text("""SELECT COUNT(*) FROM threads t WHERE t.area = :area_id""")
        result = app.db.session.execute(sql, {"area_id" : self.id})
        count = result.fetchone()
        self.thread_count = count[0]
        return count
    
    def query_message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        result = app.db.session.execute(sql, {"area_id" : self.id})
        count = result.fetchone()
        self.message_count = count[0]
        return count
    
    def query_last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        result = app.db.session.execute(sql, {"area_id" : self.id})
        last = result.fetchone()
        if last[0] != None:
            self.last_message = datetime.strftime(last[0], "%d.%m.%Y %H:%M")
        return last
        

    def insert(self):
        sql = text("""INSERT INTO areas (topic) VALUES (:topic)""")
        app.db.session.execute(sql, {"topic" : self.topic})
        app.db.session.commit()
