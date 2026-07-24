from datetime import datetime
from app import db

class CurrentReading(db.Model):
    __tablename__ = "current.readings"

    id = db.Column(
        db.Integer,
        primary_key = True)
    
    reading_amp = db.Column(
        db.Float,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    def _to_dict(self):
        return {
            "id" : self.id,
            "reading_amp" : self.reading_amp,
            "created_at" : self.created_at,
        }