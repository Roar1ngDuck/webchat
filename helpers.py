from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import app
from sqlalchemy import text
from models import *
import random

def get_areas():
    sql = text("""SELECT * FROM areas""")
    areas:list[Area] = []

    for result in app.db.session.execute(sql).fetchall():
        area = Area.create_from_sql_result(result)
        area.query_thread_count()
        area.query_message_count()
        area.query_last_message()
        areas.append(area)

    return areas

def verify_login(request):
    username = request.form["username"]
    password = request.form["password"]
    if username == "test" and password == "test":
        return 0
    return None
    

def create_test_data():
    for i in range(10):
        msg = Message.create(random.randint(0, 3), random.randint(0, 3), "Test message hello!")
        msg.insert()

        thread = Thread.create(random.randint(0, 3), f"Test thread {i}")
        thread.insert()

        area = Area.create(f"Test topic {i}")
        area.insert()