from datetime import datetime

from app import db
from database.models.saftey_lock import SafetyLock, SafetyLockStatus



class SafetyLockRepository:

    def __init__(self, app):
        self.app = app

    def create(self, **fields):

        with self.app.app_context():

            lock = SafetyLock(**fields)

            db.session.add(lock)
            db.session.commit()

            return lock

    def get_active_lock(self):

        with self.app.app_context():

            lock = (
                SafetyLock.query
                .filter_by(
                    status=SafetyLockStatus.ACTIVE.value
                )
                .first()
            )

            return lock

    def is_locked(self):

        return self.get_active_lock() is not None

    def release(self, lock_id:int):

        with self.app.app_context():

            lock = SafetyLock.query.get(lock_id)

            if not lock:
                return

            lock.status = (
                SafetyLockStatus.RELEASED.value
            )

            lock.released_at = datetime.utcnow()

            db.session.commit()

    def increment_retry(self, lock_id:int):

        with self.app.app_context():

            lock = SafetyLock.query.get(lock_id)

            if not lock:
                return

            lock.retry_count += 1

            db.session.commit()