from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv

def create_app():
    app = Flask(__name__)
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/webchat'
    app.secret_key = getenv("SECRET_KEY")

    #db.init_app(app)

    # Import and register your blueprints
    from .chat.views import chat_blueprint
    app.register_blueprint(chat_blueprint)

    return app