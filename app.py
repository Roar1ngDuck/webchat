from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
from models import *
import helpers

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/webchat'
db = SQLAlchemy(app)

@app.route("/")
def index():
    # msg = Message(1, 1, "hello")
    # msg.insert()

    # thread = Thread(1, "Test thread")
    # thread.insert()

    # area = Area("test topic 123")
    # area.insert()

    return render_template("index.html", areas=helpers.get_areas())