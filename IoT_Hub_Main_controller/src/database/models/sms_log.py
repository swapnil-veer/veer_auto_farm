# app/models/sms_log.py
from app import db
from datetime import datetime
from enum import Enum 

class SmsDirection(Enum):
    INCOMING = 'incoming'
    OUTGOING = 'outgoing'

class SmsStatus(Enum):
    RECEIVED = 'received'
    AUTHORIZED = 'authorized'
    UNAUTHORIZED = 'unauthorized'
    PROCESSED = 'processed'
    HANDLED = 'handled'
    SENT = 'sent'
    FAILED = 'failed'

class SmsLog(db.Model):
    __tablename__ = 'sms_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Core fields
    direction = db.Column(db.Enum(SmsDirection), nullable=False, default=SmsDirection.INCOMING)
    phone = db.Column(db.String(20), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    channel = db.Column(db.String(20), default='sim800l')
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    related_sms_id = db.Column(db.Integer, 
                              db.ForeignKey('sms_log.id'), 
                              nullable=True)
    
    # Status tracking
    status = db.Column(db.Enum(SmsStatus), default=SmsStatus.RECEIVED, nullable=False)
    is_authorized = db.Column(db.Boolean, default=False)
    is_processed = db.Column(db.Boolean, default=False)
 

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    error_info = db.Column(db.Text, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_direction_status', 'direction', 'status'),
        db.Index('idx_phone_created', 'phone', 'created_at'),
        db.Index('idx_related_sms', 'related_sms_id'),
    )
    
    def __repr__(self):
        return f'<SmsLog(id={self.id}, phone={self.phone}, status={self.status.value})>'
    
    def _to_dict(self):
        return {
            "id" : self.id,
            "sender" : self.phone,
            "message" : self.message,
            "status" : self.status,
            "user_id" : self.user_id,
            "created_at" : self.created_at,
        }
