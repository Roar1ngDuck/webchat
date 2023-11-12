from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import app
from sqlalchemy import text
import bcrypt
import helpers

# TODO: Refactor a lot of this code

engine = create_engine("postgresql://postgres:postgres@localhost/webchat")
connection = engine.connect()

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
        result = connection.execute(sql, {"thread" : self.thread, "sender" : self.sender, "text" : self.text, "sent_time" : self.sent_time})
        connection.commit()
        self.id = result.fetchone()[0]

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
        for row in connection.execute(sql, {"thread_id" : id}).mappings():
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
        return connection.execute(sql, {"thread_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread = :thread_id""")
        result = connection.execute(sql, {"thread_id" : self.id}).fetchone()[0]
        if result != None:
            self.last_message = helpers.time_ago(result)
        return result
    
    def insert(self):
        sql = text("""INSERT INTO threads (area, title) VALUES (:area, :title) RETURNING id""")
        result = connection.execute(sql, {"area" : self.area, "title" : self.title})
        connection.commit()
        self.id = result.fetchone()[0]

class Area:
    @classmethod
    def create_from_db(cls, id):
        sql = text("""SELECT a.topic FROM areas a WHERE a.id = :area_id""")
        result = connection.execute(sql, {"area_id" : id})
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
        return connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def message_count(self):
        sql = text("""SELECT COUNT(*) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        return connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
    
    @property
    def last_message(self):
        sql = text("""SELECT MAX(m.sent_time) FROM messages m WHERE m.thread in (SELECT t.id FROM threads t WHERE t.area = :area_id)""")
        result = connection.execute(sql, {"area_id" : self.id}).fetchone()[0]
        if result != None:
            return helpers.time_ago(result)
        return None
        
    @property
    def threads(self): # TODO: Make create_from_sql_result for all models to not be used. Get las_message with SQL directly.
        sql = text("""SELECT t.id,t.area,t.title,a.topic FROM threads t, areas a WHERE t.area = :area_id AND t.area = a.id""")
        result = connection.execute(sql, {"area_id" : self.id}).fetchall()
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
        result = connection.execute(sql, {"topic" : self.topic})
        connection.commit()
        self.id = result.fetchone()[0]

class User:
    @classmethod
    def create(cls, username, password):
        instance = cls()
        instance.username = username
        instance.password = helpers.hash_password(password)
        return instance

    def insert(self):
        sql = text("""INSERT INTO users (username, password) VALUES (:username, :password) RETURNING id""")
        result = connection.execute(sql, {"username" : self.username, "password" : self.password})
        connection.commit()
        self.id = result.fetchone()[0]