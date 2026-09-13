from datetime import datetime

from app import db
from database.models.saftey_lock import SafetyLock, SafetyLockStatus, SafetyLockType



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

    def create_dry_run_lock(
        self,
        valid_until,
        reason,
        ):

        with self.app.app_context():

            start_of_day = datetime.utcnow().replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            last_lock = (
                SafetyLock.query
                .filter(
                    SafetyLock.lock_type
                    == SafetyLockType.DRY_RUN.value,
                    SafetyLock.created_at >= start_of_day,
                )
                .order_by(
                    SafetyLock.created_at.desc()
                )
                .first()
            )

            retry_count = (
                last_lock.retry_count + 1
                if last_lock
                else 1
            )

            lock = SafetyLock(
                lock_type=SafetyLockType.DRY_RUN.value,
                valid_until=valid_until,
                retry_count=retry_count,
                reason=reason,
            )

            db.session.add(lock)
            db.session.commit()

            return lock._to_dict()

    def save(self, lock):
        with self.app.app_context():
            db.session.merge(lock)
            db.session.commit()

    def update(self, lock_id: int, **updates):
        with self.app.app_context():
            SafetyLock.query.filter_by(id=lock_id).update(updates)
            db.session.commit()