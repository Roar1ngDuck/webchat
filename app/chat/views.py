from flask import request, render_template, redirect, session, Blueprint
from ..utils import helpers
from faker import Faker
import random
from ..models.area import Area
from ..models.thread import Thread
from ..models.user import User
from ..models.message import Message

chat_blueprint = Blueprint('chat', __name__)

@chat_blueprint.route("/generate")
def generate_test_data():
    fake = Faker()

    # Create some users
    users = []
    for i in range(10):
        username = fake.user_name()
        password = fake.password(length=10, special_chars=True, digits=True, upper_case=True, lower_case=True)
        user = User(username, password)
        user.insert()
        users.append(user)

    # Create some areas
    areas = []
    for i in range(5):
        topic = fake.unique.word().title()
        area = Area(topic)
        area.insert()
        areas.append(area)

    # Create some threads within those areas
    threads = []
    for i in range(20):
        area_index = random.randint(1, len(areas))
        title = fake.sentence(nb_words=6).rstrip('.')
        thread = Thread(area_index, title)
        thread.insert()
        threads.append(thread)

    # Create some messages within those threads
    for i in range(1, len(threads)):
        for _ in range(random.randint(5, 15)):
            thread_index = i
            sender_index = random.randint(0, len(users) - 1)
            msg = Message(thread_index, sender_index, fake.paragraph(nb_sentences=3))
            msg.insert()

    return redirect("/")
    

@chat_blueprint.route("/", methods=['GET', 'POST'])
def index():
    if "user_id" not in session:
        return redirect("/login")
    
    # TODO: List recently active threads on the right side of the flex box, only on desktop.

    if request.method == "POST":
        Area(request.form["topic"]).insert()

    return render_template("index.html", areas=helpers.get_areas())

@chat_blueprint.route("/area/<int:area_id>", methods=['GET', 'POST'])
def view_area(area_id):
    if "user_id" not in session:
        return redirect("/login")

    # TODO: List recent messages on the right side of the flex box, only on desktop.

    if request.method == "POST":
        thread_id = Thread(area_id, request.form["title"]).insert().id

        Message(thread_id, session["user_id"], request.form["message"]).insert()

    return render_template("area.html", area=Area.create_from_db(area_id))

@chat_blueprint.route("/thread/<int:thread_id>", methods=['GET', 'POST'])
def view_thread(thread_id):
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        Message(thread_id, session["user_id"], request.form["message"]).insert()

    return render_template("thread.html", thread=Thread.create_from_db(thread_id))
    

@chat_blueprint.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        user_id = helpers.verify_login(request)
        if user_id == None:
            return render_template("login.html", error=True)
        session["user_id"] = user_id
        session["username"] = request.form["username"]
        return redirect("/")
    
@chat_blueprint.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        if helpers.username_exists(request.form["username"]):
            return render_template("register.html", error="Username taken")
        if helpers.is_password_secure(request.form["password"]) == False:
            return render_template("register.html", error="Password is too weak")   
        if request.form["password"] != request.form["confirm_password"]:
            return render_template("register.html", error="Passwords don't match")

        User(request.form["username"], request.form["password"]).insert()

        return redirect("/login")
    
@chat_blueprint.route("/logout")
def logout():
    session.pop("user_id")
    return redirect("/")