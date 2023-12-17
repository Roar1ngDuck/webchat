from flask import request, session, redirect, url_for, flash
from functools import wraps
from ..utils import helpers

def login_required(f):
    @wraps(f)
    def _login_required(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("chat.login"))
        return f(*args, **kwargs)
    return _login_required

def captcha_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            if request.method == "POST" and not helpers.verify_turnstile(request):
                flash("CAPTCHA verification failed", "error")
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function