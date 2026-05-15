#infrastructure/gpio_seed.py

"""
GPIO seeding and runtime setup.

GPIO adapter contract:
- gpio.BCM
- gpio.OUT / gpio.IN
- gpio.LOW / gpio.HIGH
- setmode(), setup(), cleanup()
"""

from logging_config import logger
from app import db
from database.models.gpio_config import GpioConfig, GpioType
from database.models.pump import Pump

GPIO_PINS = {
    "sda": {"gpio_pin": 2, "gpio_type": "i2c"},
    "scl": {"gpio_pin": 3, "gpio_type": "i2c"},
    "relay_pi_onoff": {"gpio_pin": 24, "gpio_type": "output", "device_type": "pump"},
    "relay_dry_run": {"gpio_pin": 23, "gpio_type": "output"},
    "phase_monitor_green": {"gpio_pin": 17, "gpio_type": "input"},
    "phase_monitor_yellow": {"gpio_pin": 27, "gpio_type": "input"},
    "phase_monitor_red": {"gpio_pin": 22, "gpio_type": "input"},
    "bypass_switch": {"gpio_pin": 11, "gpio_type": "input"},
    }

def seed_gpio_config(app):
    with app.app_context():
        for key, data in GPIO_PINS.items():
            if GpioConfig.query.filter_by(gpio_key=key).first():
                continue

            gpio_type = (
                GpioType.OUTPUT if data["gpio_type"] == "output"
                else GpioType.INPUT if data["gpio_type"] == "input"
                else None
                )

            config = GpioConfig(
                gpio_key=key,
                gpio_pin=data["gpio_pin"],
                name=key.replace("_", " ").title(),
                device_type=data.get("device_type"),
                gpio_type=gpio_type,
                enabled=True,
                description=f"Static: {key}",
                )
            db.session.add(config)

            db.session.commit()
            logger.info("GPIO configuration seeding complete")

def seed_pumps_from_gpio(app):
    with app.app_context():
        pump_gpios = GpioConfig.query.filter_by(device_type="pump").all()
        created = 0

        for gpio in pump_gpios:
            if Pump.query.filter_by(gpio_config_id=gpio.id).first():
                continue

            pump = Pump(
                gpio_config_id=gpio.id,
                name=gpio.name,
                desc=f"Auto-created from GPIO {gpio.gpio_key}",
                )
            db.session.add(pump)
            created += 1

        db.session.commit()
        logger.info(f"Auto-created {created} pump(s)")

def setup_gpio_runtime(app, gpio):
    gpio.setmode(gpio.BCM)

    with app.app_context():
        configs = GpioConfig.query.filter_by(enabled=True).all()

    for cfg in configs:
        if cfg.gpio_type == GpioType.OUTPUT:
            gpio.setup(cfg.gpio_pin, gpio.OUT, initial=gpio.LOW)
        elif cfg.gpio_type == GpioType.INPUT:
            gpio.setup(cfg.gpio_pin, gpio.IN)
        else:
            pass # managed by kernel / I2C driver

    logger.info("GPIO runtime configured")

def cleanup_gpio(gpio):
    gpio.cleanup()