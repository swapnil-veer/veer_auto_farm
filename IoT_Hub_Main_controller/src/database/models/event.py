# database/models/event.py
from database.database import db
from enum import Enum

class EventType(Enum):
    PUMP_STARTED = "PUMP_STARTED"
    PUMP_COMPLETED = "PUMP_COMPLETED"
    PUMP_ABORTED_POWER_LOSS = "PUMP_ABORTED_POWER_LOSS"
    PUMP_AUTO_STOPPED = "PUMP_AUTO_STOPPED"
    PUMP_ABORTED_MANUAL_STOP = "PUMP_ABORTED_MANUAL_STOP"
    COMMAND_DELETED_CURRENT = "COMMAND_DELETED_CURRENT"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.Enum(EventType), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    mode = db.Column(db.String(10))
    duration_min = db.Column(db.Float)
    raw_data = db.Column(db.Text)
