# infrastructure/phase_repository.py
from database.models.phase_log import PhaseLog
from app import db
from logging_config import logger

class PhaseRepository:
    def __init__(self, app):
        self.app = app

    def save(self, green: bool, yellow: bool, red: bool, timestamp):
        with self.app.app_context():
            try:
                log = PhaseLog(
                green_led=green,
                yellow_led=yellow,
                red_led=red,
                timestamp=timestamp,
                )
                db.session.add(log)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.exception(f"PhaseLog persist failed: {e}")
