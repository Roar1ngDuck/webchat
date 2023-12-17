from sqlalchemy import text
from datetime import datetime
from ..models.area import Area
import bcrypt
from zxcvbn import zxcvbn
from ..utils.db import Database
import requests
from os import getenv
from flask import session

def get_areas(user_id):
    """
    Fetches a list of discussion areas accessible to the given user.
    It includes areas open to all users and secret areas for which the user has privileges.
    This function supports access control by filtering areas based on user privileges and admin status.
    """

    areas:list[Area] = []

    # Construct SQL query to fetch areas based on user privileges and admin status.
    sql = text("""
        SELECT a.id, a.topic, a.is_secret
        FROM areas a
        LEFT JOIN secret_area_privileges sap ON a.id = sap.area_id AND sap.user_id = :user_id
        INNER JOIN users u ON u.id = :user_id
        WHERE u.is_admin = true OR a.is_secret = false OR sap.user_id IS NOT NULL
    """)

    # Query the database and create Area objects for each result.
    for result in Database().fetch_all(sql, {"user_id": user_id}):
        area = Area(result["topic"], result["is_secret"], result["id"])
        areas.append(area)

    return areas

def username_exists(username):
    """
    Checks if the given username already exists in the database.
    This is used to prevent duplicate usernames during registration.
    """

    # Query the database and return a boolean based on the existence of the username.
    sql = text("""SELECT COUNT(*) FROM users u WHERE u.username = :username""")
    return Database().fetch_one(sql, {"username" : username})["count"] != 0

def verify_login(request):
    """
    Verifies user credentials against the database during login.
    Utilizes bcrypt for secure password comparison.
    Returns user ID and admin status if credentials are valid.
    """

    # Query to fetch user data for authentication.
    username = request.form["username"]
    sql = text("""SELECT u.id, u.password, is_admin FROM users u WHERE u.username = :username""")
    result = Database().fetch_one(sql, {"username" : username})

    if not result:
        return (None, None)

    # Check password validity with bcrypt and return user details if authentication succeeds.
    if bcrypt.checkpw(request.form["password"].encode('utf-8'), result["password"].tobytes()):
        return (result["id"], "admin" if result["is_admin"] else "user")

    return (None, None)

def hash_password(password):
    """
    Hashes a password using bcrypt.
    This is a security measure to ensure that stored passwords are not in plain text.
    """

    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def is_password_secure(password):
    """
    Evaluates the security of a password using the zxcvbn library.
    Ensures users choose strong passwords.
    """

    return zxcvbn(password)["score"] >= 4

def verify_turnstile(request):
    """
    Verifies the Turnstile (CAPTCHA) response to prevent automated submissions.
    Enhances security by mitigating bot-based attacks and spam.
    """

    if getenv("USE_TURNSTILE", "") != "True":
        return True

    # Prepare data for Turnstile verification request.
    turnstile_response = request.form.get("cf-turnstile-response", "")
    remote_ip = request.form.get("CF-Connecting-IP", "")
    data = {
    'secret': getenv("TURNSTILE_SECRET", ""),
    'response': turnstile_response,
    'remoteip': remote_ip
    }

    # Send verification request and interpret the outcome.
    response = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=data).json()

    return response.get('success')

def time_ago(date):
    """
    Converts a datetime object to a human-readable time-ago format.
    """

    now = datetime.now()
    diff = now - date

    seconds = diff.total_seconds()
    minutes = seconds / 60
    hours = minutes / 60
    days = diff.days
    months = days / 30.44  # Average days per month
    years = days / 365.25  # Average days per year

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif minutes < 60:
        return f"{int(minutes)} minutes ago"
    elif hours < 24:
        return f"{int(hours)} hours ago"
    elif days < 30:
        return f"{int(days)} days ago"
    elif days < 365:
        return f"{int(months)} months ago"
    else:
        return f"{int(years)} years ago"
    
def is_valid_area_topic(topic):
    """
    Validates the topic of a discussion area.
    Ensures that the topic name adheres to predefined length constraints.
    """

    return len(topic) > 0 and len(topic) < 64

def is_valid_thread_title(title):
    """
    Validates the title of a thread.
    Ensures that the thread title adheres to predefined length constraints.
    """

    return len(title) > 0 and len(title) < 64

def is_valid_message(message):
    """
    Checks if a message meets length requirements.
    Prevents overly verbose or empty messagess.
    """

    return len(message) > 0 and len(message) < 1024

def is_valid_username(username):
    """
    Validates a username based on length and character composition.
    Ensures usernames are of an appropriate length and contain only alphanumeric characters.
    """

    if len(username) <= 0 or len(username) > 32:
        return False
    
    if not username.isalnum():
        return False

    return True

def add_user_to_secret_area(username, area_id):
    """
    Grants a user access to a secret discussion area.
    Allows administrators to manage user access.
    """

    sql = text("""INSERT INTO secret_area_privileges (area_id, user_id) VALUES (:area_id, (SELECT id FROM users WHERE username = :username))""")
    Database().execute(sql, {"username" : username, "area_id" : area_id}, False)

def remove_user_from_secret_area(username, area_id):
    """
    Revokes a user's access to a secret discussion area.
    Allows administrators to manage user access.
    """

    sql = text("""DELETE FROM secret_area_privileges WHERE area_id = :area_id AND user_id = (SELECT id FROM users WHERE username = :username)""")
    Database().execute(sql, {"area_id": area_id, "username": username}, False)

def get_access_list(area_id):
    """
    Retrieves a list of users who have access to a specific secret area.
    Useful for admins to view and manage access to restricted sections.
    """

    sql = text("""SELECT u.username FROM secret_area_privileges s, users u WHERE s.area_id = :area_id AND s.user_id = u.id""")
    return Database().fetch_all(sql, {"area_id": area_id})

def delete_message(thread_id, message_id, user_id):
    """
    Deletes a message from the database and also deletes the thread if the message is the only one in the thread.
    """

    delete_thread_sql = text("""
        DELETE FROM threads
        WHERE id = :thread_id AND (
            SELECT COUNT(*) FROM messages WHERE thread = (
                SELECT thread FROM messages WHERE id = :message_id
            )
        ) = 1
    """)
    Database().execute(delete_thread_sql, {"thread_id": thread_id, "message_id": message_id}, False)

    sql = text("""DELETE FROM messages m WHERE m.id = :message_id AND m.sender = :user_id""")
    Database().execute(sql, {"message_id": message_id, "user_id": user_id}, False)

def delete_thread(thread_id):
    """
    Deletes a thread from the database.
    """

    sql = text("""DELETE FROM threads WHERE id = :thread_id""")
    Database().execute(sql, {"thread_id": thread_id}, False)

def delete_area(area_id):
    """
    Deletes an area from the database.
    """

    sql = text("""DELETE FROM areas WHERE id = :area_id""")
    Database().execute(sql, {"area_id": area_id}, False)

def get_turnstile_sitekey():
    return getenv("TURNSTILE_SITEKEY", None)

def full_search(query):
    # SQL queries to search areas, threads, and messages
    area_sql = text("SELECT * FROM areas WHERE topic ILIKE :query")
    thread_sql = text("""
        SELECT t.*, a.topic as area_topic 
        FROM threads t 
        JOIN areas a ON t.area = a.id 
        WHERE t.title ILIKE :query
    """)
    message_sql = text("""
        SELECT m.*, t.title as thread_title, a.topic as area_topic 
        FROM messages m 
        JOIN threads t ON m.thread = t.id 
        JOIN areas a ON t.area = a.id 
        WHERE m.text ILIKE :query
    """)

    areas = Database().fetch_all(area_sql, {"query": f"%{query}%"})
    threads = Database().fetch_all(thread_sql, {"query": f"%{query}%"})
    messages = Database().fetch_all(message_sql, {"query": f"%{query}%"})

    return areas, threads, messages

def is_admin():
    return session["user"] == "admin"