from flask import request, render_template, redirect, session, Blueprint, url_for
from ..utils import helpers
from ..models.area import Area
from ..models.thread import Thread
from ..models.user import User
from ..models.message import Message
from ..utils.decorators import login_required

chat_blueprint = Blueprint('chat', __name__, url_prefix='/', static_folder='../static')
    
@chat_blueprint.route("/", methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        if not helpers.verify_turnstile(request):
            return render_template("index.html", areas=helpers.get_areas(), turnstile_error=True)
        if not helpers.is_valid_area_topic(request.form["topic"]):
            return render_template("index.html", areas=helpers.get_areas(), error=True)
        
        new_area = Area(request.form["topic"])
        new_area.insert()

    return render_template("index.html", areas=helpers.get_areas())

@chat_blueprint.route("/area/<int:area_id>", methods=['GET', 'POST'])
@login_required
def view_area(area_id):
    if request.method == "POST":
        if not helpers.verify_turnstile(request):
            return render_template("area.html", area=Area.create_from_db(area_id), turnstile_error=True)
        if not helpers.is_valid_thread_title(request.form["title"]):
            return render_template("area.html", area=Area.create_from_db(area_id), error=True)
        
        new_thread = Thread(area_id, request.form["title"])
        new_thread.insert()

        new_message = Message(new_thread.id, session["user_id"], request.form["message"])
        new_message.insert()

    return render_template("area.html", area=Area.create_from_db(area_id))

@chat_blueprint.route("/thread/<int:thread_id>", methods=['GET', 'POST'])
@login_required
def view_thread(thread_id):
    if request.method == "POST":
        if not helpers.verify_turnstile(request):
            return render_template("thread.html", thread=Thread.create_from_db(thread_id), turnstile_error=True)
        if not helpers.is_valid_message(request.form["message"]):
            return render_template("thread.html", thread=Thread.create_from_db(thread_id), error=True)
        
        new_message = Message(thread_id, session["user_id"], request.form["message"])
        new_message.insert()

    return render_template("thread.html", thread=Thread.create_from_db(thread_id))
    
@chat_blueprint.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        if not helpers.verify_turnstile(request):
            return render_template("login.html", turnstile_error=True)
        
        user_id = helpers.verify_login(request)

        if not user_id:
            return render_template("login.html", error=True)
        
        session["user_id"] = user_id
        session["username"] = request.form["username"]

        return redirect(url_for("chat.index"))
    
@chat_blueprint.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        if not helpers.verify_turnstile(request):
            return render_template("register.html", turnstile_error=True)
        if helpers.username_exists(request.form["username"]):
            return render_template("register.html", error="Username taken")
        if not helpers.is_password_secure(request.form["password"]):
            return render_template("register.html", error="Password is too weak")   
        if request.form["password"] != request.form["confirm_password"]:
            return render_template("register.html", error="Passwords don't match")

        new_user = User(request.form["username"], request.form["password"])
        new_user.insert()

        return redirect(url_for("chat.login"))
    
@chat_blueprint.route("/logout")
def logout():
    session.pop("user_id")
    return redirect(url_for("chat.index"))