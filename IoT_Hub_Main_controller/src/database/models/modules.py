
from datetime import datetime
from enum import Enum

from app import db


class ModuleType(str, Enum):
    LCD = "LCD"
    CURRENT_MONITOR = "CURRENT_MONITOR"

    # Add optional modules here later.
    # SIM = "SIM"
    # PHASE_MONITOR = "PHASE_MONITOR"


class Module(db.Model):

    __tablename__ = "modules"

    id = db.Column(db.Integer,primary_key=True,)

    module_type = db.Column(db.String(50),nullable=False,unique=True,index=True)

    is_installed = db.Column(db.Boolean,nullable=False,default=False)

    is_enabled = db.Column(db.Boolean,nullable=False,default=False)

    configured_at = db.Column(db.DateTime,nullable=True)

    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    settings = db.relationship(
        "ModuleSetting",
        back_populates="module",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def _to_dict(self, include_settings=False):

        data = {
            "id": self.id,
            "module_type": self.module_type,
            "is_installed": self.is_installed,
            "is_enabled": self.is_enabled,
            "configured_at": self.configured_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

        if include_settings:
            data["settings"] = [
                setting._to_dict()
                for setting in self.settings
            ]

        return data