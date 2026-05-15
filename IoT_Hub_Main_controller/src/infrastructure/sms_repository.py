# infrastructure/sms_repository.py
from app import db
from database.models.sms_log import SmsLog, SmsDirection, SmsStatus
from database.models.user import User
from datetime import datetime

class SMSRepository:
    def __init__(self, app):
        self.app = app

    def get_user(self, phone):
        with self.app.app_context():
            return User.query.filter_by(phone=phone, is_active=True).first()

    def log_incoming(self, phone, text):
        with self.app.app_context():
            log = SmsLog(
            direction=SmsDirection.INCOMING,
            phone=phone,
            message=text,
            status=SmsStatus.RECEIVED,
            )
            db.session.add(log)
            db.session.commit()
            return log

    def log_outgoing(self, phone, text, status, error=None, related_id=None, user_id=None):
        with self.app.app_context():
            log = SmsLog(
            direction=SmsDirection.OUTGOING,
            phone=phone,
            message=text,
            status=status,
            error=error,
            related_sms_id=related_id,
            user_id=user_id,
            )
            db.session.add(log)
            db.session.commit()
            return log

    def get_authorized_unprocessed(self, limit=5):
        with self.app.app_context():
            return SmsLog.query.filter_by(
                status=SmsStatus.AUTHORIZED,
                is_processed=False
                ).order_by(SmsLog.created_at.asc()).limit(limit).all()