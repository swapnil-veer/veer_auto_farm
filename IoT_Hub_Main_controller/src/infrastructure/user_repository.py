from database.models.user import User


class UserRepository:
    def __init__(self, app):
        self.app = app

    def get_by_phone(self, phone):
        with self.app.app_context():
            return User.query.filter_by(phone=phone, is_active=True).first()

    def get_by_id(self, user_id):
        with self.app.app_context():
            return User.query.get(user_id)

    def get_by_email(self, email):
        with self.app.app_context():
            return User.query.filter_by(email=email, is_active=True).first()
