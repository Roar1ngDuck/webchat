from flask import request, render_template, redirect, session, Blueprint, url_for
from ..utils import helpers
from ..models.area import Area
from ..models.thread import Thread
from ..models.user import User
from ..models.message import Message
from ..utils.decorators import login_required

# Blueprint setup for chat functionality, enabling modularization and URL prefixing.
chat_blueprint = Blueprint('chat', __name__, url_prefix='/', static_folder='../static')


# Route for the main page, handling both display and creation of discussion areas.
@chat_blueprint.route("/", methods=['GET', 'POST'])
@login_required
def index():
    # Handling area creation on POST request, with various validations.
    if request.method == "POST":
        # Verify Turnstile (CAPTCHA) response to prevent automated submissions.
        if not helpers.verify_turnstile(request):
            return render_template("index.html", areas=helpers.get_areas(), turnstile_sitekey = helpers.get_turnstile_sitekey(), turnstile_error=True)
        
        # Ensure that the area topic meets validation criteria (e.g., length, format).
        if not helpers.is_valid_area_topic(request.form["topic"]):
            return render_template("index.html", areas=helpers.get_areas(), turnstile_sitekey = helpers.get_turnstile_sitekey(), error=True)
        
        # Secret areas can only be created by admins, controlled by a checkbox in the form.
        is_secret = False
        if session["is_admin"] == "True" and request.form.get("is_secret", "") == "on":
            is_secret = True

        # Create and insert the new discussion area into the database.
        new_area = Area(request.form["topic"], is_secret)
        new_area.insert()

        # Redirect back to home page after creating new area.
        return redirect(url_for("chat.index"))

    # Display areas based on user credentials and area access rights.
    user_id = session["user_id"]
    return render_template("index.html", areas=helpers.get_areas(user_id), is_admin=session["is_admin"] == "True", turnstile_sitekey = helpers.get_turnstile_sitekey())


# Route for viewing and interacting with a specific discussion area.
@chat_blueprint.route("/area/<int:area_id>", methods=['GET', 'POST'])
@login_required
def view_area(area_id):
    # Handle POST requests for creating a new thread within a discussion area.
    if request.method == "POST":
        # Verify Turnstile (CAPTCHA) response to prevent automated submissions.
        if not helpers.verify_turnstile(request):
            return render_template("area.html", area=Area.create_from_db(area_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), turnstile_error=True)
        
        # Ensure that the thread title meets validation criteria (e.g., length, format).
        if not helpers.is_valid_thread_title(request.form["title"]):
            return render_template("area.html", area=Area.create_from_db(area_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), error=True)
        
        # Create a new thread and its first message in the database.
        new_thread = Thread(area_id, request.form["title"], session["user_id"])
        new_thread.insert()
        new_message = Message(new_thread.id, session["user_id"], request.form["message"])
        new_message.insert()

        # Redirect back to the area page after creating a new thread.
        return redirect(url_for("chat.view_area", area_id=area_id))

    # Retrieve user_id from session for access control and personalization.
    user_id = session["user_id"]
    # Fetch details of the area, including access control for secret areas.
    area = Area.create_from_db(area_id, user_id)

    # If the area is secret and the user is an admin, fetch a list of users with access.
    access_list = []
    if area.is_secret and session["is_admin"] == "True":
        access_list = helpers.get_access_list(area.id)

    # Render the area page with appropriate data and access controls.
    return render_template("area.html", area=area, is_admin=session["is_admin"] == "True", access_list=access_list, turnstile_sitekey = helpers.get_turnstile_sitekey())


# Route for viewing and interacting with a specific thread.
@chat_blueprint.route("/thread/<int:thread_id>", methods=['GET', 'POST'])
@login_required
def view_thread(thread_id):
    # Handle POST requests for adding new messages to the thread.
    if request.method == "POST":
        # Verify Turnstile (CAPTCHA) response to prevent automated submissions.
        if not helpers.verify_turnstile(request):
            return render_template("thread.html", thread=Thread.create_from_db(thread_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), turnstile_error=True)
        
        # Ensure that the message content meets validation criteria (e.g., length, format).
        if not helpers.is_valid_message(request.form["message"]):
            return render_template("thread.html", thread=Thread.create_from_db(thread_id), turnstile_sitekey = helpers.get_turnstile_sitekey(), error=True)
        
         # Create and insert the new message into the thread.
        new_message = Message(thread_id, session["user_id"], request.form["message"])
        new_message.insert()

        # Redirect back to the thread page after adding a new message.
        return redirect(url_for("chat.view_thread", thread_id=thread_id))

    # Render the thread page, including all its messages. If thread doesn't exist, redirect back to home page.
    thread = Thread.create_from_db(thread_id)
    if thread == None:
        return redirect(url_for("chat.index"))
    return render_template("thread.html", thread=thread, turnstile_sitekey = helpers.get_turnstile_sitekey(), is_admin=session["is_admin"] == "True")
    

@chat_blueprint.route("/manage_area_access", methods=['POST'])
@login_required
def manage_area_access():
    # Handle POST request to manage user access to secret areas.
    if request.method == "POST":
        # Extract necessary data from the form.
        username = request.form["username"]
        area_id = request.form["area_id"]
        action = request.form["action"]

        # Add or remove a user's access to a secret area based on the action specified.
        if action == "add":
            helpers.add_user_to_secret_area(username, area_id)
        elif action == "remove":
            helpers.remove_user_from_secret_area(username, area_id)

        # Redirect back to the area management page after updating access controls.
        return redirect(url_for("chat.view_area", area_id=request.form["area_id"]))

@chat_blueprint.route("/delete_thread/<int:thread_id>", methods=['POST'])
@login_required
def delete_thread(thread_id):
    thread = Thread.create_from_db(thread_id)

     # Redirect with to index if not authorized
    if session["user_id"] != thread.owner_id and session["is_admin"] != "True":
        return redirect(url_for("chat.index"))

    helpers.delete_thread(thread_id)

    # Redirect to the area page after deletion
    return redirect(url_for("chat.view_area", area_id=thread.area))

@chat_blueprint.route("/delete_message/<int:message_id>/<int:thread_id>", methods=['POST'])
@login_required
def delete_message(message_id, thread_id):
    # Handle POST request to delete a message.
    helpers.delete_message(thread_id, message_id, session["user_id"])

    # Redirect back to the thread view.
    return redirect(url_for("chat.view_thread", thread_id=thread_id))

@chat_blueprint.route("/login", methods=['GET', 'POST'])
def login():
    # Display login form on GET request.
    if request.method == "GET":
        return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey())
    
    # Handle login form submission on POST request.
    if request.method == "POST":
        # Verify Turnstile (CAPTCHA) response to prevent automated submissions.
        if not helpers.verify_turnstile(request):
            return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), turnstile_error=True)
        
        # Verify user credentials. If valid, retrieve user_id and admin status.
        user_id, is_admin = helpers.verify_login(request)

        if not user_id:
            return render_template("login.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), error=True)
        
        # Set user session details on successful login.
        session["user_id"] = user_id
        session["username"] = request.form["username"]
        session["is_admin"] = "True" if is_admin else "False"

        # Redirect to the main page after successful login.
        return redirect(url_for("chat.index"))
    
    
@chat_blueprint.route("/register", methods=['GET', 'POST'])
def register():
    # Display registration form on GET request.
    if request.method == "GET":
        return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey())
    
    # Process registration form submission on POST request.
    if request.method == "POST":
        # Verify Turnstile (CAPTCHA) response to prevent automated submissions.
        if not helpers.verify_turnstile(request):
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), turnstile_error=True)
        
        # Check if the username already exists in the database.
        if helpers.username_exists(request.form["username"]):
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), error="Username taken")
        
        # Validate the chosen username against specific criteria (e.g., length, characters).
        if not helpers.is_valid_username(request.form["username"]):
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), error="Invalid username")
        
        # Ensure the password meets security standards, such as minimum complexity.
        if not helpers.is_password_secure(request.form["password"]):
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), error="Password is too weak")  
         
        # Confirm that the password and confirmation password fields match.
        if request.form["password"] != request.form["confirm_password"]:
            return render_template("register.html", turnstile_sitekey = helpers.get_turnstile_sitekey(), error="Passwords don't match")

        # Create and insert a new user into the database.
        new_user = User(request.form["username"], request.form["password"])
        new_user.insert()

        # Redirect the user to the login page after successful registration.
        return redirect(url_for("chat.login"))
    

# Handle user logout, clearing session data.
@chat_blueprint.route("/logout")
def logout():
    # Remove user identification and session data. Uses 'None' as default to avoid KeyError.
    session.pop("user_id", None)  # Remove user_id from session.
    session.pop("username", None)  # Remove username from session.
    session.pop("is_admin", None)  # Clear admin status from session.

    # Redirect to the main page (index) after logging out.
    return redirect(url_for("chat.index"))