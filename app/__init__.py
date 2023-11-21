from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv
from .chat.views import chat_blueprint

def create_app():
    app = Flask(__name__)
    app.secret_key = getenv("SECRET_KEY")
    
    if getenv("ENV") == "PROD":
        app.config.update(
            SESSION_COOKIE_SECURE = True,
            SESSION_COOKIE_HTTPONLY = True,
            SESSION_COOKIE_SAMESITE = "Strict",
        )

    app.register_blueprint(chat_blueprint)

    return app