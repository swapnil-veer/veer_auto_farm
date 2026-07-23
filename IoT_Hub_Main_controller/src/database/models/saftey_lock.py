from enum import Enum
from datetime import datetime

from app import db


class SafetyLockType(str, Enum):
    DRY_RUN = "DRY_RUN"
    DAILY_LOCK = "DAILY_LOCK"


class SafetyLockStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"


class SafetyLock(db.Model):

    __tablename__ = "safety_locks"

    id = db.Column(db.Integer,primary_key=True)
    lock_type = db.Column(db.String(50),nullable=False)
    status = db.Column(db.String(20),nullable=False,default=SafetyLockStatus.ACTIVE.value)
    retry_count = db.Column(db.Integer,nullable=False,default=0)
    valid_until = db.Column(db.DateTime,nullable=False)
    reason = db.Column(db.String(255))
    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    released_at = db.Column(db.DateTime)

    def _to_dict(self):
        return {
            "id": self.id,
            "lock_type": self.lock_type,
            "status": self.status,
            "retry_count": self.retry_count,
            "valid_until": self.valid_until,
            "reason": self.reason,
        }