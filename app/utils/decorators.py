from flask import session, redirect, url_for
from functools import wraps

def login_required(f):
    @wraps(f)
    def _login_required(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("chat.login"))
        return f(*args, **kwargs)
    return _login_required