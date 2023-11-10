from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import app
from sqlalchemy import text
import bcrypt
import helpers

# TODO: Refactor a lot of this code

class Message:
    @classmethod
    def create_from_sql_result(cls, sql_result):
        instance = cls()
        instance.id = sql_result[0]
        instance.thread = sql_result[1]
        instance.sender = sql_result[2]
        instance.text = sql_result[3]
        instance.sent_time = datetime.strftime(sql_result[4], "%d.%m.%Y %H:%M")
        return instance
    
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
        result = app.db.session.execute(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})
        app.db.session.commit()
        self.id = result.fetchone()[0]

class Thread:
    @classmethod
    def create_from_sql_result(cls, sql_result):
        instance = cls()
        instance.id = sql_result[0]
        instance.area = sql_result[1]
        instance.title = sql_result[2]
        return instance
    
    @classmethod
    def create_from_db(cls, id):
        instance = cls()
        instance.id = id
        sql = text("""SELECT M.id, T.title, U.username, M.text, M.sent_time FROM messages M JOIN users U ON M.sender = U.id JOIN threads T ON M.thread = T.id WHERE M.thread = :thread_id""")
        result = app.db.session.execute(sql, {"thread_id" : id})
        message_results = result.fetchall()
        instance.title = message_results[0][1]
        instance.messages:list[Thread] = []
        for message_result in message_results:
            message = Message.create_from_sql_result(message_result)
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
        return app.db.session.execute(sql, {"thread_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread = :thread_id""")
        result = app.db.session.execute(sql, {"thread_id" : self.id}).fetchone()[0]
        if result != None:
            self.last_message = helpers.time_ago(result)
        return result
    
    @property
    def area_name(self):
        sql = text("""SELECT a.topic FROM areas a, threads t WHERE a.id = t.area AND t.id = :thread_id""")
        return app.db.session.execute(sql, {"thread_id" : self.id}).fetchone()[0]
    
    @property
    def area_id(self):
        sql = text("""SELECT t.area FROM threads t WHERE t.id = :thread_id""")
        return app.db.session.execute(sql, {"thread_id" : self.id}).fetchone()[0]
    
    def insert(self):
        sql = text("""INSERT INTO threads (area, title) VALUES (:area, :title) RETURNING id""")
        result = app.db.session.execute(sql, {"area" : self.area, "title" : self.title})
        app.db.session.commit()
        self.id = result.fetchone()[0]

class Area:
    @classmethod
    def create_from_sql_result(cls, sql_result):
        instance = cls()
        instance.id = sql_result[0]
        instance.topic = sql_result[1]
        return instance
    
    @classmethod
    def create_from_db(cls, id):
        sql = text("""SELECT a.topic FROM areas a WHERE a.id = :area_id""")
        result = app.db.session.execute(sql, {"area_id" : id})
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
        return app.db.session.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        return app.db.session.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        result = app.db.session.execute(sql, {"area_id" : self.id}).fetchone()[0]
        if result != None:
            return helpers.time_ago(result)
        return None
        
    @property
    def threads(self): # TODO: Make create_from_sql_result for all models to not be used. Get las_message with SQL directly.
        sql = text("""SELECT * FROM threads t WHERE t.area = :area_id""")
        result = app.db.session.execute(sql, {"area_id" : self.id}).fetchall()
        threads:list[Thread] = []
        for thread_result in result:
            thread = Thread.create_from_sql_result(thread_result)
            threads.append(thread)
        return threads
    
    def insert(self):
        sql = text("""INSERT INTO areas (topic) VALUES (:topic) RETURNING id""")
        result = app.db.session.execute(sql, {"topic" : self.topic})
        app.db.session.commit()
        self.id = result.fetchone()[0]

class User:
    @classmethod
    def create(cls, username, password):
        instance = cls()
        instance.username = username
        instance.password = helpers.hash_password(password)
        return instance

    def insert(self):
        sql = text("""INSERT INTO users (username, password) VALUES (:username, :password)""")
        app.db.session.execute(sql, {"username" : self.username, "password" : self.password})
        app.db.session.commit()