from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv

def create_app():
    app = Flask(__name__)
    app.secret_key = getenv("SECRET_KEY")

    from .chat.views import chat_blueprint
    app.register_blueprint(chat_blueprint)

    return app