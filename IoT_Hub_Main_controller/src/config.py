import RPi.GPIO as GPIO
from logging_config import logger
from app import db
from database.models.gpio_config import GpioConfig, GpioType
GPIO.setwarnings(False)
GPIO.cleanup()      #FOR PREVIOUS CLEANUP

GPIO_PINS = {
    "sda" : {"gpio_pin": 2, "device_type": "i2c"}, # I2C SDA (BCM 2, Pin 3)
    "scl" : {"gpio_pin": 3, "gpio_type": "i2c"},  #I2C SCL (BCM 3, Pin 5)
    "relay_pi_onoff" : {"gpio_pin":24, "gpio_type": "output", "device_type" : "pump"},  #(Pi On-Off Relay) (BCM 24, Pin 18)
    "relay_dry_run" : {"gpio_pin": 23, "gpio_type": "output"},   #(Dry-Run Control Relay) (BCM 23, Pin 16)
    "phase_monitor_green" : {"gpio_pin": 17, "gpio_type": "input"}, # Phase Monitor - OK (Green LED) (BCM 17, Pin 11)
    "phase_monitor_yellow" : {"gpio_pin": 27, "gpio_type": "input"},    # Phase Monitor - Initial Wait (Yellow LED) (BCM 27, Pin 13)
    "phase_monitor_red" : {"gpio_pin": 22, "gpio_type": "input"},       # Phase Monitor - Fault (Red LED) (BCM 22, Pin 15)
    "bypass_switch" :{"gpio_pin": 11, "gpio_type": "input"},            # DPST Switch 2A (BCM 11, Pin 23)
}

def seed_gpio_config():
    """Seed static GPIO_PINS into DB (one-time)"""
    seeded_count = 0
    for key, data in GPIO_PINS.items():
        existing = GpioConfig.query.filter_by(gpio_key=key).first()
        if not existing:
            config = GpioConfig(
                gpio_key=key,
                gpio_pin=data["device_pin"],
                name=key.replace("_", " ").title(),
                device_type=data["device_type"],
                gpio_type=GpioType.OUTPUT if data["gpio_type"] == "output" else GpioType.INPUT,
                enabled=True,
                description=f"Static: {key}"
            )
            db.session.add(config)
            seeded_count += 1
    
    if seeded_count > 0:
        db.session.commit()
        logger.info(f"✅ Seeded {seeded_count} GPIO configs from config.py!")
    else:
        logger.info("All GPIO pins already seeded")

def setup_gpio(db_session):
    """Setup GPIO pins FROM DB ONLY (static + web-added)"""
    GPIO.setmode(GPIO.BCM)
    
    # DB-driven GPIO setup (single source!)
    configs = db_session.query(GpioConfig).filter(GpioConfig.enabled == True).all()
    
    for config in configs:
        if config.gpio_type == GpioType.OUTPUT:
            GPIO.setup(config.gpio_pin, GPIO.OUT)
        elif config.gpio_type == GpioType.INPUT:
            GPIO.setup(config.gpio_pin, GPIO.IN)
    
    logger.info("Configured Gpio pins")

# def setup_gpio():
#     """Setup all GPIO pins based on their type."""
#     GPIO.setmode(GPIO.BCM)

#     for key, data in GPIO_PINS.items():
#         if data["type"] == "output":
#             GPIO.setup(data["pin"], GPIO.OUT)
#         elif data["type"] == "input":
#             GPIO.setup(data["pin"], GPIO.IN)

def set_high(pin):
    GPIO.output(pin, GPIO.HIGH)

def set_low(pin):
    GPIO.output(pin, GPIO.LOW)

def cleanup_gpio():
    """Cleanup GPIO on exit."""
    GPIO.cleanup()