# farm_controller/database/database.py - FLASK-SQLALCHEMY
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    """Pass Flask app to init DB"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")
