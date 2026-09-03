from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException


load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message = "Please log in to continue."


def create_app(config_object=None):
    app = Flask(__name__)

    app.config.from_object(config_object or "app.config.Config")

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User
    from app.routes import main

    app.register_blueprint(main)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        if error.code == 404:
            return error.description, 404
        return error.description, error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unhandled application error")
        return "Something went wrong while processing the request", 500

    return app

