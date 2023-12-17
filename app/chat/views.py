from flask import request, render_template, redirect, session, Blueprint, url_for, flash
from flask_wtf.csrf import generate_csrf
from ..utils import helpers
from ..models.area import Area
from ..models.thread import Thread
from ..models.user import User
from ..models.message import Message
from ..utils.decorators import login_required, captcha_required
from pathlib import Path
import uuid
import os

# Blueprint setup for chat functionality, enabling modularization and URL prefixing.
chat_blueprint = Blueprint('chat', __name__, url_prefix='/', static_folder='../static')


@chat_blueprint.route("/", methods=['GET'])
@login_required
def index():
    user_id = session["user_id"]
    return render_template("index.html", areas=helpers.get_areas(user_id), is_admin=helpers.is_admin(), turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())

@chat_blueprint.route("/create_area", methods=['POST'])
@login_required
@captcha_required
def create_area():
    # Validate area topic
    if not helpers.is_valid_area_topic(request.form["topic"]):
        flash("Invalid area topic", "error")
        return render_template("index.html", areas=helpers.get_areas(), turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
    
    is_secret = True if helpers.is_admin() and request.form.get("is_secret", "") == "on" else False

    # Create and insert the new discussion area into the database.
    new_area = Area(request.form["topic"], is_secret)
    new_area.insert()

    # Redirect back to home page after creating new area.
    flash("Area created successfully", "success")
    return redirect(url_for("chat.index"))

@chat_blueprint.route("/area/<int:area_id>", methods=['GET'])
@login_required
@captcha_required
def view_area(area_id):
    user_id = session["user_id"]
    area = Area.create_from_db(area_id, user_id)

    if area == None:
        flash("Area does not exist", "error")
        return redirect(url_for("chat.index"))

    # If the area is secret and the user is an admin, fetch a list of users with access.
    access_list = helpers.get_access_list(area.id) if area.is_secret and helpers.is_admin() else []

    # Render the area page with appropriate data and access controls.
    return render_template("area.html", area=area, is_admin=helpers.is_admin(), access_list=access_list, turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())

@chat_blueprint.route("/area/<int:area_id>/create_thread", methods=['POST'])
def create_thread(area_id):
    # Validate title
    if not helpers.is_valid_thread_title(request.form["title"]):
        flash("Invalid thread title", "error")
        return render_template("area.html", area=Area.create_from_db(area_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
    
    # Create a new thread and its first message in the database.
    new_thread = Thread(area_id, request.form["title"], session["user_id"])
    new_thread.insert()
    new_message = Message(new_thread.id, session["user_id"], request.form["message"])
    new_message.insert()

    # Redirect back to the area page after creating a new thread.
    flash("Thread created successfully", "success")
    return redirect(url_for("chat.view_area", area_id=area_id))

@chat_blueprint.route("/thread/<int:thread_id>", methods=['GET'])
@login_required
def view_thread(thread_id):
    # Render the thread page, including all its messages. If thread doesn't exist, redirect back to home page.
    thread = Thread.create_from_db(thread_id)
    if thread == None:
        flash("Thread does not exist", "error")
        return redirect(url_for("chat.index"))
    return render_template("thread.html", thread=thread, turnstile_sitekey = helpers.get_turnstile_sitekey(), is_admin=helpers.is_admin(), csrf_token=generate_csrf())
    
@chat_blueprint.route("/thread/<int:thread_id>/send_message", methods=['POST'])
@login_required
@captcha_required
def send_message(thread_id):
    # Validate message
    if not helpers.is_valid_message(request.form["message"]):
        flash("Invalid message", "error")
        return render_template("thread.html", thread=Thread.create_from_db(thread_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
    
    filename = None
    if "image" in request.files and request.files["image"].filename != "":
        Path("./app/static/uploads").mkdir(parents=True, exist_ok=True)
        image = request.files["image"]
        rand = str(uuid.uuid4())
        filename = "./app/static/uploads/" + rand + ".jpg"
        image.save(filename)
        filename = "/static/uploads/" + rand + ".jpg"

        # Create and insert the new message into the thread.
    new_message = Message(thread_id, session["user_id"], request.form["message"], image_url=filename)
    new_message.insert()

    # Redirect back to the thread page after adding a new message.
    return redirect(url_for("chat.view_thread", thread_id=thread_id))

@chat_blueprint.route("/manage_area_access", methods=['POST'])
@login_required
def manage_area_access():
    username = request.form["username"]
    area_id = request.form["area_id"]
    action = request.form["action"]

    if not helpers.username_exists(username):
        flash("User does not exist", "error")
        return redirect(url_for("chat.view_area", area_id=area_id))

    if action == "add":
        helpers.add_user_to_secret_area(username, area_id)
        flash(f"Added user {username} to access list", "success")
    elif action == "remove":
        helpers.remove_user_from_secret_area(username, area_id)
        flash(f"Removed user {username} from access list", "success")

    return redirect(url_for("chat.view_area", area_id=request.form["area_id"]))

@chat_blueprint.route("/delete_thread/<int:thread_id>", methods=['POST'])
@login_required
def delete_thread(thread_id):
    thread = Thread.create_from_db(thread_id)

    if thread == None:
        flash("Thread does not exist", "error")
        return redirect(url_for("chat.index"))

     # Redirect with to index if not authorized
    if session["user_id"] != thread.owner_id and helpers.is_admin():
        return redirect(url_for("chat.index"))

    helpers.delete_thread(thread_id)

    # Redirect to the area page after deletion
    return redirect(url_for("chat.view_area", area_id=thread.area))

@chat_blueprint.route("/delete_message/<int:message_id>/<int:thread_id>", methods=['POST'])
@login_required
def delete_message(message_id, thread_id):
    image = helpers.get_message_image(message_id)
    if image != None:
        os.remove("./app" + image)

    helpers.delete_message(thread_id, message_id, session["user_id"])

    # Redirect back to the thread view.
    return redirect(url_for("chat.view_thread", thread_id=thread_id))

@chat_blueprint.route("/delete_area/<int:area_id>", methods=['POST'])
@login_required
def delete_area(area_id):
    if not helpers.is_admin():
        return redirect(url_for("chat.index"))

    helpers.delete_area(area_id)
    flash("Area deleted successfully", "success")
    return redirect(url_for("chat.index"))

@chat_blueprint.route("/search", methods=['GET'])
@login_required
def search():
    query = request.args.get('query', '')
    
    areas, threads, messages = helpers.full_search(query)

    return render_template("search_results.html", areas=areas, threads=threads, messages=messages, csrf_token=generate_csrf())

@chat_blueprint.route("/login", methods=['GET', 'POST'])
@captcha_required
def login():
    # Display login form on GET request.
    if request.method == "GET":
        return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
    
    # Handle login form submission on POST request.
    if request.method == "POST":
        if not helpers.username_exists(request.form["username"]):
            flash("Invalid username or password", "error")
            return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())

        # Verify user credentials. If valid, retrieve user_id and admin status.
        user_id, user_type = helpers.verify_login(request)

        if not user_id:
            flash("Invalid username or password", "error")
            return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
        
        # Set user session details on successful login.
        session["user_id"] = user_id
        session["username"] = request.form["username"]
        session["user"] = user_type

        # Redirect to the main page after successful login.
        return redirect(url_for("chat.index"))
    
    
@chat_blueprint.route("/register", methods=['GET', 'POST'])
@captcha_required
def register():
    # Display registration form on GET request.
    if request.method == "GET":
        return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
    
    # Process registration form submission on POST request.
    if request.method == "POST":
        # Check if the username already exists in the database.
        if helpers.username_exists(request.form["username"]):
            flash("Username taken", "error")
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
        
        # Validate the chosen username against specific criteria (e.g., length, characters).
        if not helpers.is_valid_username(request.form["username"]):
            flash("Invalid username", "error")
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())
        
        # Ensure the password meets security standards, such as minimum complexity.
        if not helpers.is_password_secure(request.form["password"]):
            flash("Password too weak", "error")
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())  
         
        # Confirm that the password and confirmation password fields match.
        if request.form["password"] != request.form["confirm_password"]:
            flash("Passwords don't match", "error")
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), csrf_token=generate_csrf())

        # Create and insert a new user into the database.
        new_user = User(request.form["username"], request.form["password"])
        new_user.insert()

        # Redirect the user to the login page after successful registration.
        return redirect(url_for("chat.login"))
    

@chat_blueprint.route("/logout")
def logout():
    # Remove user identification and session data. Uses 'None' as default to avoid KeyError.
    session.pop("user_id", None)  # Remove user_id from session.
    session.pop("username", None)  # Remove username from session.
    session.pop("user", None)  # Clear admin status from session.

    # Redirect to the main page (index) after logging out.
    return redirect(url_for("chat.index"))