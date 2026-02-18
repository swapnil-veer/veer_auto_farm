# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from dotenv import load_dotenv
# from database.database import init_db, db

load_dotenv()

db = SQLAlchemy()

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Config
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "../farm.db")}'
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veer_farm.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-me')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize database using YOUR database.py method
    # init_db(app)
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'db': 'veer_farm.db ready'}
    return app
