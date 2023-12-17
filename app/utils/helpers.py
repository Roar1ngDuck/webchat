from datetime import datetime
import os
from os import getenv
from sqlalchemy import text
import bcrypt
from zxcvbn import zxcvbn
import requests
from flask import session
from ..utils.db import Database
from ..models.area import Area


def get_areas(user_id):
    """
    Fetches a list of areas accessible to a specific user.

    Args:
        user_id (int): The user ID for whom the accessible areas are to be fetched.

    Returns:
        list[Area]: A list of Area objects accessible to the user.
    """

    areas: list[Area] = []

    sql = text("""
        SELECT a.id, a.topic, a.is_secret
        FROM areas a
        LEFT JOIN secret_area_privileges sap ON a.id = sap.area_id AND sap.user_id = :user_id
        INNER JOIN users u ON u.id = :user_id
        WHERE u.is_admin = true OR a.is_secret = false OR sap.user_id IS NOT NULL
    """)

    for result in Database().fetch_all(sql, {"user_id": user_id}):
        area = Area(result["topic"], result["is_secret"], result["id"])
        areas.append(area)

    return areas


def username_exists(username):
    """
    Checks if a username already exists in the database.

    Args:
        username (str): The username to check.

    Returns:
        bool: True if the username exists, False otherwise.
    """

    sql = text("""SELECT COUNT(*) FROM users u WHERE u.username = :username""")
    return Database().fetch_one(sql, {"username": username})["count"] != 0


def verify_login(request):
    """
    Verifies user login credentials.

    Args:
        request (Request): The Flask request object containing form data.

    Returns:
        tuple: A tuple containing user ID and role if credentials are valid, otherwise (None, None).
    """

    username = request.form["username"]
    sql = text("""SELECT u.id, u.password, is_admin FROM users u WHERE u.username = :username""")
    result = Database().fetch_one(sql, {"username": username})

    if not result:
        return (None, None)

    # Check password validity with bcrypt and return user details if authentication succeeds.
    if bcrypt.checkpw(request.form["password"].encode('utf-8'), result["password"].tobytes()):
        return (result["id"], "admin" if result["is_admin"] else "user")

    return (None, None)


def hash_password(password):
    """
    Hashes a password using bcrypt.

    Args:
        password (str): The password to hash.

    Returns:
        str: The hashed password.
    """

    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())


def is_password_secure(password):
    """
    Checks if a password is secure based on certain criteria.

    Args:
        password (str): The password to check.

    Returns:
        bool: True if the password is considered secure, False otherwise.
    """

    return zxcvbn(password)["score"] >= 4


def verify_turnstile(request):
    """
    Verifies a Turnstile CAPTCHA response.

    Args:
        request (Request): The Flask request object containing form data.

    Returns:
        bool: True if the CAPTCHA verification is successful, False otherwise.
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
    Calculates how much time has passed since a given date.

    Args:
        date (datetime): The date to compare with the current time.

    Returns:
        str: A human-readable string representing the time elapsed.
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
    Validates the topic of an area.

    Args:
        topic (str): The area topic to validate.

    Returns:
        bool: True if the topic is valid, False otherwise.
    """

    return len(topic) > 0 and len(topic) < 64


def is_valid_thread_title(title):
    """
    Validates the title of a thread.

    Args:
        title (str): The thread title to validate.

    Returns:
        bool: True if the title is valid, False otherwise.
    """

    return len(title) > 0 and len(title) < 64


def is_valid_message(message):
    """
    Validates a message's content.

    Args:
        message (str): The message to validate.

    Returns:
        bool: True if the message is valid, False otherwise.
    """

    return len(message) > 0 and len(message) < 1024


def is_valid_username(username):
    """
    Validates a username.

    Args:
        username (str): The username to validate.

    Returns:
        bool: True if the username is valid, False otherwise.
    """

    if len(username) <= 0 or len(username) > 32:
        return False

    if not username.isalnum():
        return False

    return True


def add_user_to_secret_area(username, area_id):
    """
    Adds a user to a secret area.

    Args:
        username (str): The username of the user to be added.
        area_id (int): The ID of the secret area.
    """

    sql = text("""INSERT INTO secret_area_privileges (area_id, user_id) VALUES (:area_id, (SELECT id FROM users WHERE username = :username))""")
    Database().execute(sql, {"username": username, "area_id": area_id}, False)


def remove_user_from_secret_area(username, area_id):
    """
    Removes a user from a secret area.

    Args:
        username (str): The username of the user to be removed.
        area_id (int): The ID of the secret area.
    """

    sql = text("""DELETE FROM secret_area_privileges WHERE area_id = :area_id AND user_id = (SELECT id FROM users WHERE username = :username)""")
    Database().execute(sql, {"area_id": area_id, "username": username}, False)


def get_access_list(area_id):
    """
    Retrieves a list of users who have access to a specific area.

    Args:
        area_id (int): The ID of the area.

    Returns:
        list: A list of usernames who have access to the area.
    """

    sql = text("""SELECT u.username FROM secret_area_privileges s, users u WHERE s.area_id = :area_id AND s.user_id = u.id""")
    return Database().fetch_all(sql, {"area_id": area_id})


def get_message_image(message_id):
    """
    Retrieves the image URL associated with a specific message.

    Args:
        message_id (int): The ID of the message.

    Returns:
        str: The URL of the image associated with the message.
    """

    sql = text("""SELECT image_url FROM messages WHERE id = :message_id""")
    return Database().fetch_one(sql, {"message_id": message_id})["image_url"]


def delete_message(thread_id, message_id, user_id):
    """
    Deletes a message from a thread.

    Args:
        thread_id (int): The ID of the thread containing the message.
        message_id (int): The ID of the message to be deleted.
        user_id (int): The ID of the user who sent the message.
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
    Deletes a thread and its associated messages.

    Args:
        thread_id (int): The ID of the thread to be deleted.
    """

    sql = text("""SELECT image_url FROM messages WHERE thread = :thread_id""")
    image_urls = Database().fetch_all(sql, {"thread_id": thread_id})
    for image_url in image_urls:
        if image_url["image_url"]:
            os.remove("./app" + image_url["image_url"])

    sql = text("""DELETE FROM threads WHERE id = :thread_id""")
    Database().execute(sql, {"thread_id": thread_id}, False)


def delete_area(area_id):
    """
    Deletes an area and its associated threads and messages.

    Args:
        area_id (int): The ID of the area to be deleted.
    """

    sql = text("""SELECT image_url FROM messages WHERE thread in (SELECT id FROM threads WHERE area = :area_id)""")
    image_urls = Database().fetch_all(sql, {"area_id": area_id})
    for image_url in image_urls:
        if not image_url["image_url"]:
            os.remove("./app" + image_url["image_url"])

    sql = text("""DELETE FROM areas WHERE id = :area_id""")
    Database().execute(sql, {"area_id": area_id}, False)


def get_turnstile_sitekey():
    """
    Retrieves the Turnstile site key from environment variables.

    The function checks for a site key for the Turnstile CAPTCHA service,
    which is used in the frontend for CAPTCHA verification.

    Returns:
        str or None: The Turnstile site key or None if not set.
    """
    return getenv("TURNSTILE_SITEKEY", None)


def full_search(query):
    """
    Performs a full text search across areas, threads, and messages in the database.

    The function executes SQL queries to search for the provided query string in
    topics of areas, titles of threads, and text of messages.

    Args:
        query (str): The search query string.

    Returns:
        tuple: A tuple containing three lists for areas, threads, and messages
               where each list contains dictionaries of the respective query results.
    """

    area_sql = text("SELECT id, topic FROM areas WHERE topic ILIKE :query")
    thread_sql = text("""
        SELECT t.title, t.id, a.topic as area_topic
        FROM threads t
        JOIN areas a ON t.area = a.id
        WHERE t.title ILIKE :query
    """)
    message_sql = text("""
        SELECT m.text, m.thread, t.title as thread_title, a.topic as area_topic, u.username as sender_name
        FROM messages m
        JOIN threads t ON m.thread = t.id
        JOIN areas a ON t.area = a.id
        JOIN users u ON m.sender = u.id
        WHERE m.text ILIKE :query
    """)

    areas = Database().fetch_all(area_sql, {"query": f"%{query}%"})
    threads = Database().fetch_all(thread_sql, {"query": f"%{query}%"})
    messages = Database().fetch_all(message_sql, {"query": f"%{query}%"})

    return areas, threads, messages


def is_admin():
    """
    Checks if the current session is associated with an admin user.

    This function checks the user's session to determine if the current user
    is marked as an 'admin' in the session data.

    Returns:
        bool: True if the current session is for an admin user, False otherwise.
    """

    return session["user"] == "admin"


def get_notifications(user_id):
    """
    Retrieves notifications for a given user.

    Args:
        user_id (int): The ID of the user to retrieve notifications for.

    Returns:
        list: A list of notifications for the user.
    """

    sql = text("""
        SELECT n.id, n.thread_id, n.message, n.sent_time, n.sender_id,
               t.area, t.title as thread_title,
               a.topic as area_topic,
               u.username as sender_name
        FROM notifications n
        JOIN threads t ON n.thread_id = t.id
        JOIN areas a ON t.area = a.id
        JOIN users u ON n.sender_id = u.id
        WHERE n.user_id = :user_id
        ORDER BY n.sent_time DESC
    """)
    raw_notifications = Database().fetch_all(sql, {"user_id": user_id})

    notifications = []
    for raw_notification in raw_notifications:
        notification = dict(raw_notification)
        notification['sent_time_ago'] = time_ago(notification['sent_time'])
        notifications.append(notification)

    return notifications
