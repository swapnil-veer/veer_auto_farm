# database/__init__.py
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        from .models import command, sms_log, phase_log, event  # noqa
        db.create_all()
    return db
