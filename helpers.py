from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
import app
from sqlalchemy import text
from models import *

def get_areas():
    sql = text("""SELECT * FROM areas""")
    areas:list[Area] = []

    for result in app.db.session.execute(sql).fetchall():
        area = Area(result[1], result[0])
        area.query_thread_count()
        area.query_message_count()
        area.query_last_message()
        areas.append(area)

    return areas