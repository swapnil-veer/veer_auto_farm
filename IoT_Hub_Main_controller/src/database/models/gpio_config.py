from app import db
from datetime import datetime
from enum import Enum
# from models import Pump

class GpioType(Enum):
    INPUT = 'input'
    OUTPUT = 'output'

class GpioConfig(db.Model):
    __tablename__ = 'gpio_config'
    
    id = db.Column(db.Integer, primary_key=True)
    gpio_pin = db.Column(db.Integer, nullable=False, unique=True)  # 24, 23, 17...
    gpio_key = db.Column(db.String(50), nullable=False, unique=True)  # "relay_pi_onoff"
    name = db.Column(db.String(50), nullable=False, unique=True)       # "PUMP1_Main" 
    device_type = db.Column(db.String(20), nullable=True)            # "pump", "valve"
    gpio_type = db.Column(db.Enum(GpioType), nullable=True)             # "input", "output"
    enabled = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # pump = db.relationship('Pump', backref='gpio_config')
    
    __table_args__ = (
        db.Index('idx_device_enabled', 'device_type', 'enabled'),
    )
    
    def __repr__(self):
        return f'<GpioConfig {self.name} ({self.gpio_key})>'
