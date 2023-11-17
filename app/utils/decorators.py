from flask import session, redirect
from functools import wraps

def login_required(f):
    @wraps(f)
    def _login_required(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return _login_required