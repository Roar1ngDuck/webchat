from sqlalchemy import text
from datetime import datetime
from ..models.area import Area
import bcrypt
from zxcvbn import zxcvbn
from ..utils.db import Database
import requests
from os import getenv

def get_areas():
    areas:list[Area] = []

    sql = text("""SELECT id, topic, is_secret FROM areas""")
    for result in Database().fetch_all(sql):
        area = Area(result["topic"], result["is_secret"], result["id"])
        areas.append(area)

    return areas

def username_exists(username):
    sql = text("""SELECT COUNT(*) FROM users u WHERE u.username = :username""")
    if Database().fetch_one(sql, {"username" : username})["count"] == 0:
        return False

    return True

def verify_login(request):
    username = request.form["username"]

    sql = text("""SELECT u.id, u.password FROM users u WHERE u.username = :username""")
    result = Database().fetch_one(sql, {"username" : username})

    if not result:
        return None

    if bcrypt.checkpw(request.form["password"].encode('utf-8'), result["password"].tobytes()):
        return result["id"]

    return None

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def is_password_secure(password):
    return zxcvbn(password)["score"] >= 4

def verify_turnstile(request):
    if getenv("USE_TURNSTILE") != "True":
        return True

    turnstile_response = request.form.get("cf-turnstile-response", "")
    remote_ip = request.form.get("CF-Connecting-IP", "")

    data = {
    'secret': getenv("TURNSTILE_SECRET"),
    'response': turnstile_response,
    'remoteip': remote_ip
    }

    response = requests.post('https://challenges.cloudflare.com/turnstile/v0/siteverify', data=data)

    if not response.ok:
        return False

    outcome = response.json()

    if outcome.get('success'):
        return True
    
    return False
        

def time_ago(date):
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
    return len(topic) > 0 and len(topic) < 64

def is_valid_thread_title(title):
    return len(title) > 0 and len(title) < 64

def is_valid_message(message):
    return len(message) > 0 and len(message) < 1024

def is_valid_username(username):
    if len(username) <= 0 or len(username) > 32:
        return False
    
    if not username.isalnum():
        return False

    return True