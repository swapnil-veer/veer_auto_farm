# database/models/user.py
from app import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)

    #Authentication (for web)
    password_hash = db.Column(db.String(255), nullable=True)
    
    # Role flags (Django-style)
    is_active = db.Column(db.Boolean, default=True)
    is_staff = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    is_superuser = db.Column(db.Boolean, default=False)
    
    # Timestamps
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
  
    @classmethod
    def create_user(cls, phone, name, is_staff=False, is_owner=False):
        """Admin ONLY creates users"""
        if cls.query.filter_by(phone=phone).first():
            raise ValueError("User exists")
        user = cls(phone=phone, name=name, is_staff=is_staff, is_owner=is_owner)
        db.session.add(user)
        db.session.commit()
        return user
    
    @classmethod
    def get_only(cls, phone):
        """Safe lookup - NO create"""
        return cls.query.filter_by(phone=phone, is_active=True).first()

    def __repr__(self):
        # return f"<User {self.user.name}"
        return f"<User {self.name}"

