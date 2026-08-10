from app import db
from database.models.current_reading import CurrentReading


class CurrentReadingRepository:
    def __init__(self, app):
        self.app = app

    def save(self, reading_amp:float):
        with self.app.app_context():
            row = CurrentReading(reading_amp = reading_amp)
            db.session.add(row)
            db.session.commit()

    def latest(self):
        with self.app.app_context():
            row = (CurrentReading.query.order_by(CurrentReading.id.desc())).first()
            return row 

    def get_last_n(self, limit:int):
        with self.app.app_context():
            rows = CurrentReading.query.order_by(CurrentReading.id.desc()).limit(limit).all()
            return list(reversed(rows))