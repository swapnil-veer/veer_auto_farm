from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app():
    basedir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, "../web/templates"),
        static_folder=os.path.join(basedir, "../web/static")
    )

    basedir = os.path.abspath(
        os.path.dirname(__file__)
    )

    app.config.update(
        SQLALCHEMY_DATABASE_URI=
        f"sqlite:///{os.path.join(basedir, '../farm.db')}",

        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        SECRET_KEY=os.getenv(
            "SECRET_KEY",
            "dev-key-change-me"
        ),
    )

    db.init_app(app)
    migrate.init_app(app, db)

    return app