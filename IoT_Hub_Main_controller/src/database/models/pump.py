# app/models/pump.py
from app import db
from database.models.gpio_config import GpioConfig
from database.models.command import Command
from datetime import datetime

class Pump(db.Model):
    __tablename__ = 'pumps'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    desc = db.Column(db.String(100), nullable=True)
    
    # Relationships
    gpio_config = db.relationship('GpioConfig', backref='pumps')
    pump_runs = db.relationship('PumpRun', backref='pump', lazy=True)
    
    def __repr__(self):
        return f'<Pump {self.name}>'

class PumpRun(db.Model):
    __tablename__ = 'pump_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    pump_id = db.Column(db.Integer, db.ForeignKey('pumps.id'), nullable=False)
    on_command_id = db.Column(db.Integer, db.ForeignKey('command.id'), nullable=False)
    on_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    off_command_id = db.Column(db.Integer, db.ForeignKey('command.id'), nullable=True)
    off_time = db.Column(db.DateTime, nullable=True)
    duration_sec = db.Column(db.Integer, nullable=True)  # Store calculated
    
    # Relationships
    pump = db.relationship('Pump', backref='pump_runs')
    on_command = db.relationship('Command', 
                               foreign_keys=[on_command_id], 
                               backref='pump_runs_on')
    off_command = db.relationship('Command', 
                                foreign_keys=[off_command_id], 
                                backref='pump_runs_off')
    
    def calculate_duration(self):
        """Auto-calculate duration_sec"""
        if self.off_time and self.on_time:
            self.duration_sec = int((self.off_time - self.on_time).total_seconds())
            return self.duration_sec
        return 0
    
    def __repr__(self):
        return f'<PumpRun {self.pump.name} ({self.duration_sec or 0}s)>'