from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


import config

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = 'super secret key'

    # 블루프린트
    from .views import main_views
    app.register_blueprint(main_views.bp)

    # ORM
    db.init_app(app)
    migrate.init_app(app, db)
    from . import models

    return app