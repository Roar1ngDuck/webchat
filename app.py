from flask import Flask, request, jsonify, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import os
from models import *
import helpers
from os import getenv

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/webchat'
app.secret_key = getenv("SECRET_KEY")
db = SQLAlchemy(app)

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("index.html", areas=helpers.get_areas())

@app.route("/area/<int:area_id>")
def view_area(area_id):
    if "user_id" not in session:
        return redirect("/login")

    area = Area.create_from_db(area_id)
    threads = area.query_threads()

    return render_template("area.html", threads=threads)

@app.route("/thread/<int:thread_id>")
def view_thread(thread_id):
    if "user_id" not in session:
        return redirect("/login")

    thread = Thread.create_from_db(thread_id)

    return render_template("thread.html", messages=thread.messages)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        user_id = helpers.verify_login(request)
        if user_id == None:
            return render_template("login.html", error=True)
        session["user_id"] = user_id
        return redirect("/")