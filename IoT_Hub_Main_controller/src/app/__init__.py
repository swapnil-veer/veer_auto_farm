# app/__init__.py
from flask import Flask
import os
from database import init_db

def create_app():
    app = Flask(__name__)
    
    # SQLite config
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "../farm.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Init database
    init_db(app)
    
    @app.route('/ping')
    def ping():
        return {'status': 'OK', 'db': 'ready'}
    
    return app
