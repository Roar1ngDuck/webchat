from functools import wraps
from flask import request, session, redirect, url_for, flash
from ..utils import helpers

def login_required(f):
    """
    Decorator to enforce user login for protected routes.

    This decorator checks if the user is logged in (by checking if 'user_id' is in the session).
    If the user is not logged in, they are redirected to the login page.

    Args:
        f (function): The view function to be wrapped by the decorator.

    Returns:
        function: The decorated view function which includes login check logic.
    """
    @wraps(f)
    def _login_required(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("chat.login"))
        return f(*args, **kwargs)
    return _login_required

def captcha_required(f):
    """
    Decorator to enforce CAPTCHA validation on form submissions.

    This decorator checks the CAPTCHA response on POST requests using a helper function
    `verify_turnstile`. If CAPTCHA validation fails, it shows an error message and
    redirects the user back to the same page.

    Args:
        f (function): The view function to be wrapped by the decorator.

    Returns:
        function: The decorated view function which includes CAPTCHA validation logic.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            if request.method == "POST" and not helpers.verify_turnstile(request):
                flash("CAPTCHA verification failed", "error")
                return redirect(request.url)
        return f(*args, **kwargs)
    return decorated_function
