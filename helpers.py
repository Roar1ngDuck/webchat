from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import app
from sqlalchemy import text
import random
import models
import bcrypt

def create_test_data():
    for i in range(10):
        msg = models.Message.create(random.randint(0, 3), random.randint(0, 3), "Test message hello!")
        msg.insert()

        thread = models.Thread.create(random.randint(0, 3), f"Test thread {i}")
        thread.insert()

        area = models.Area.create(f"Test topic {i}")
        area.insert()

    user = models.User.create("test", "test")
    user.insert()

def get_areas():
    sql = text("""SELECT * FROM areas""")
    areas:list[models.Area] = []

    for result in app.db.session.execute(sql).fetchall():
        area = models.Area.create_from_sql_result(result)
        area.query_thread_count()
        area.query_message_count()
        area.query_last_message()
        areas.append(area)

    return areas

def username_exists(username):
    sql = text("""SELECT COUNT(*) FROM users u WHERE u.username = :username""")
    result = app.db.session.execute(sql, {"username" : username})
    fetched = result.fetchone()[0]
    if fetched == 0:
        return False

    return True

def verify_login(request):
    username = request.form["username"]
    sql = text("""SELECT u.id, u.password FROM users u WHERE u.username = :username""")
    result = app.db.session.execute(sql, {"username" : username})
    fetched = result.fetchone()

    if fetched == None:
        return None

    id = fetched[0]
    password_hash = fetched[1].tobytes()

    if check_password(password_hash, request.form["password"]):
        return id

    return None

def hash_password(password):
    password_bytes = password.encode('utf-8')

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    return hashed_password

def check_password(hashed_password, user_password):
    password_bytes = user_password.encode('utf-8')

    if bcrypt.checkpw(password_bytes, hashed_password):
        return True
    else:
        return False