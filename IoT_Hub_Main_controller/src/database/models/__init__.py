# app/models/__init__.py
from app import db

# Import all models (auto-register)
from .user import User
from .command import Command  # noqa
from .sms_log import SmsLog  # noqa
from .phase_log import PhaseLog  # noqa
from .event import Event  # noqa
from .pump import Pump
from .gpio_config import GpioConfig

