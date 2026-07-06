# app/models/command.py
from app import db
from datetime import datetime
from enum import Enum

class CommandType(Enum):
    MANUAL_ON = 'MANUAL_ON'
    AUTO_ON = 'AUTO_ON'
    DELETE_ONE = 'DELETE_ONE'
    DELETE_ALL = 'DELETE_ALL'

class CommandMode(Enum):
    MANUAL = 'manual'
    AUTO = 'auto'

class CommandStatus(Enum):
    CREATED = 'created'
    QUEUED = 'queued'
    RUNNING = 'running'
    COMPLETED = 'completed'
    ABORTED = 'aborted'
    TERMINATED = 'terminated'
    FAILED = 'failed'

class Command(db.Model):
    __tablename__ = 'command'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Enums
    ctype = db.Column(db.Enum(CommandType), nullable=False)
    mode = db.Column(db.Enum(CommandMode), nullable=True)
    status = db.Column(db.Enum(CommandStatus), default=CommandStatus.CREATED, nullable=False)
    
    # Numeric fields
    priority = db.Column(db.Integer, nullable=False)
    runtime_sec = db.Column(db.Float, nullable=True)
    target_duration_sec = db.Column(db.Float, nullable=True)
    
    # Boolean + Timestamps
    in_progress = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Foreign Keys (nullable)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    sms_id = db.Column(db.Integer, db.ForeignKey('sms_log.id'), nullable=True)
    sender_phone = db.Column(db.String(20), nullable=False, index=True)
    terminated_by = db.Column(db.Integer, db.ForeignKey('command.id'), nullable=True)  
    
    __table_args__ = (
        db.Index('idx_status_priority', 'status', 'priority'),
        db.Index('idx_sender_status', 'sender_phone', 'status'),
    )

    def _to_dict(self):
        return {
            "id" : self.id,
            "ctype" : self.ctype,
            "user_id" : self.user_id,
            "sender" : self.sender_phone,
            "status" : self.status,
            "runtime_sec" : self.runtime_sec,
            "target_duration_sec" : self.target_duration_sec,
            "start_time" : self.start_time,
            "created_at" : self.created_at.isoformat() if self.created_at else None,
            "completed_at" : self.completed_at.isoformat() if self.completed_at else None,
        }