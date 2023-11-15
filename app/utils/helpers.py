from sqlalchemy import text
from datetime import datetime
from sqlalchemy import text
from ..models.area import Area
import bcrypt
from zxcvbn import zxcvbn
from ..utils import db

def get_areas():
    sql = text("""SELECT id, topic FROM areas""")
    areas:list[Area] = []

    for result in db.connection.execute(sql).mappings():
        area = Area()
        area.id = result["id"]
        area.topic = result["topic"]
        areas.append(area)

    return areas

def username_exists(username):
    sql = text("""SELECT COUNT(*) FROM users u WHERE u.username = :username""")
    result = db.connection.execute(sql, {"username" : username})
    fetched = result.fetchone()[0]
    if fetched == 0:
        return False

    return True

def verify_login(request):
    username = request.form["username"]
    sql = text("""SELECT u.id, u.password FROM users u WHERE u.username = :username""")
    result = db.connection.execute(sql, {"username" : username})
    fetched = result.fetchone()

    if fetched == None:
        return None

    id = fetched[0]
    password_hash = fetched[1].tobytes()

    if check_password(password_hash, request.form["password"]):
        return id

    return None

def hash_password(password):
    password_bytes = password.encode('utf-8')

    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    return hashed_password

def check_password(hashed_password, user_password):
    password_bytes = user_password.encode('utf-8')

    if bcrypt.checkpw(password_bytes, hashed_password):
        return True
    else:
        return False

# TODO: Limit execution time to prevent DoS    
def is_password_secure(password):
    strength = zxcvbn(password)

    if strength["score"] >= 4:
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