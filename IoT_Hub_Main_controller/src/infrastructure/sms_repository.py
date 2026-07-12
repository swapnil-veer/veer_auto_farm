# infrastructure/sms_repository.py
from app import db
from database.models.sms_log import SmsLog, SmsDirection, SmsStatus
from database.models.user import User

class SMSRepository:
    def __init__(self, app):
        self.app = app

    def get_user(self, phone):
        with self.app.app_context():
            user = User.query.filter_by(phone=phone, is_active=True).first()
            if user:
                return user.id

    def log_incoming(self, phone, message):
        with self.app.app_context():
            sms = SmsLog(
            direction=SmsDirection.INCOMING,
            phone=phone,
            message=message,
            status=SmsStatus.RECEIVED,
            )
            db.session.add(sms)
            db.session.commit()
            return sms._to_dict()

    def update_sms(self, sms_id: int, **fields):
        """
        Generic update method for SMS log.

        Allows updating any columns dynamically, e.g.:
            update_sms(id, status=..., processed=True)

        Args:
            sms_id: ID of SMS log
            **fields: key-value pairs to update
        """
        with self.app.app_context():
            sms = db.session.get(SmsLog, sms_id)

            if not sms:
                return None

            for key, value in fields.items():
                if hasattr(sms, key):
                    setattr(sms, key, value)

            db.session.commit()
            return sms._to_dict()
           
    def log_outgoing(self, phone, message, status, error=None, rel_sms_id=None, user_id=None):
        with self.app.app_context():
            sms = SmsLog(
            direction=SmsDirection.OUTGOING,
            phone=phone,
            message=message,
            status=status,
            error_info=error,
            related_sms_id=rel_sms_id,
            user_id=user_id,
            )
            db.session.add(sms)
            db.session.commit()
            return sms._to_dict()

    def get_sms_logs(self, limit=None, order_by=None, **filters):
        """
        Generic query method for SMS logs.

        Supports dynamic filtering, ordering, and limits.

        Args:
            limit: max rows to return
            order_by: column for sorting
            **filters: column=value filters

        Example:
            get_sms_logs(status=SMSStatus.AUTHORIZED, is_processed=False
        """
        with self.app.app_context():
            query = SmsLog.query

            for key, value in filters.items():
                column = getattr(SmsLog, key, None)
                if column is not None:
                    query = query.filter(column == value)

            if order_by:
                column = getattr(SmsLog, order_by, None)
                if column is not None:
                    query = query.order_by(column)

            if limit:
                query = query.limit(limit)
            return [sms._to_dict() for sms in query.all()]
        
