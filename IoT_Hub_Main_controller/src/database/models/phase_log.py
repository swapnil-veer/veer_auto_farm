from database.database import db


class PhaseLog(db.Model):
    __tablename__ = 'phase_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # LED states only (status derived)
    green_led = db.Column(db.Boolean, nullable=False)
    yellow_led = db.Column(db.Boolean, nullable=False)
    red_led = db.Column(db.Boolean, nullable=False)
    
    # Single timestamp
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    
    # Computed property (no DB column)
    @property
    def status(self):
        if self.green_led:
            return 'power_ok'
        elif self.yellow_led:
            return 'power_wait'
        elif self.red_led:
            return 'power_fault'
        else:
            return 'power_fault'
