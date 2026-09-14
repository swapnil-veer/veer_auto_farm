
from datetime import datetime
from enum import Enum

from app import db


class SettingValueType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    BOOLEAN = "BOOLEAN"


class ModuleSetting(db.Model):

    __tablename__ = "module_settings"

    id = db.Column(db.Integer,primary_key=True)

    module_id = db.Column(
        db.Integer,
        db.ForeignKey("modules.id",ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    setting_key = db.Column(
        db.String(100),
        nullable=False,
    )

    config_value = db.Column(
        db.String(255),
        nullable=False,
    )

    default_value = db.Column(
        db.String(255),
        nullable=False,
    )

    value_type = db.Column(
        db.String(20),
        nullable=False,
        default=SettingValueType.STRING.value,
    )

    display_name = db.Column(db.String(100),nullable=True)

    description = db.Column(db.String(255),nullable=True)

    created_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

    updated_at = db.Column(db.DateTime,nullable=False,default=datetime.utcnow,onupdate=datetime.utcnow)

    module = db.relationship("Module",back_populates="settings")

    __table_args__ = (
        db.UniqueConstraint(
            "module_id",
            "setting_key",
            name="uq_module_setting_key",
        ),
    )

    def get_typed_value(self):
        if self.value_type == SettingValueType.INTEGER.value:
            return int(self.config_value)

        if self.value_type == SettingValueType.FLOAT.value:
            return float(self.config_value)

        if self.value_type == SettingValueType.BOOLEAN.value:
            return self.config_value.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
            }

        return self.config_value

    def restore_default(self):
        self.config_value = self.default_value

    def _to_dict(self):

        return {
            "id": self.id,
            "module_id": self.module_id,
            "setting_key": self.setting_key,
            "config_value": self.get_typed_value(),
            "default_value": self._get_typed_default(),
            "value_type": self.value_type,
            "display_name": self.display_name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def _get_typed_default(self):
        original_value = self.config_value

        try:
            self.config_value = self.default_value
            return self.get_typed_value()
        finally:
            self.config_value = original_value