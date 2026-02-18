import RPi.GPIO as GPIO
from logging_config import logger
from app.app import db
from database.models.gpio_config import GpioConfig, GpioType
from database.models.pump import Pump
GPIO.setwarnings(False)
GPIO.cleanup()      #FOR PREVIOUS CLEANUP

GPIO_PINS = {
    "sda" : {"gpio_pin": 2, "gpio_type": "i2c"}, # I2C SDA (BCM 2, Pin 3)
    "scl" : {"gpio_pin": 3, "gpio_type": "i2c"},  #I2C SCL (BCM 3, Pin 5)
    "relay_pi_onoff" : {"gpio_pin":24, "gpio_type": "output", "device_type" : "pump"},  #(Pi On-Off Relay) (BCM 24, Pin 18)
    "relay_dry_run" : {"gpio_pin": 23, "gpio_type": "output"},   #(Dry-Run Control Relay) (BCM 23, Pin 16)
    "phase_monitor_green" : {"gpio_pin": 17, "gpio_type": "input"}, # Phase Monitor - OK (Green LED) (BCM 17, Pin 11)
    "phase_monitor_yellow" : {"gpio_pin": 27, "gpio_type": "input"},    # Phase Monitor - Initial Wait (Yellow LED) (BCM 27, Pin 13)
    "phase_monitor_red" : {"gpio_pin": 22, "gpio_type": "input"},       # Phase Monitor - Fault (Red LED) (BCM 22, Pin 15)
    "bypass_switch" :{"gpio_pin": 11, "gpio_type": "input"},            # DPST Switch 2A (BCM 11, Pin 23)
}

def seed_gpio_config(app):
    """Seed static GPIO_PINS into DB (one-time)"""
    seeded_count = 0
    for key, data in GPIO_PINS.items():
        with app.app_context():
            existing = GpioConfig.query.filter_by(gpio_key=key).first()
        if not existing:
            if data["gpio_type"] == "output":
                type = GpioType.OUTPUT
            elif data["gpio_type"] == "input":
                type = GpioType.INPUT 
            else:
                type = None
            with app.app_context():
                config = GpioConfig(
                    gpio_key=key,
                    gpio_pin=data["gpio_pin"],
                    name=key.replace("_", " ").title(),
                    device_type=data.get("device_type"),
                    gpio_type= type,
                    enabled=True,
                    description=f"Static: {key}"
                )
                db.session.add(config)
                db.session.commit()
            logger.info(f"✅ Seeded {seeded_count} GPIO configs from config.py!")
            seeded_count += 1
    
    if seeded_count == 0:
        logger.info("All GPIO pins already seeded")

def seed_pumps_from_gpio(app):
    """Create Pump entries for GPIO configs of type PUMP"""
    pumps_created = 0

    with app.app_context():
        pump_gpios = GpioConfig.query.filter_by(device_type="pump").all()

        for gpio in pump_gpios:
            existing = Pump.query.filter_by(gpio_config_id=gpio.id).first()
            if existing:
                continue

            pump = Pump(
                gpio_config_id=gpio.id,
                name=gpio.name,          # reuse GPIO name
                desc=f"Auto-created from GPIO {gpio.gpio_key}"
            )

            db.session.add(pump)
            pumps_created += 1

        if pumps_created > 0:
            db.session.commit()
            logger.info(f"✅ Auto-created {pumps_created} Pump entries")
        else:
            logger.info("All Pump entries already exist")

def setup_gpio(app):
    """Setup GPIO pins FROM DB ONLY (static + web-added)"""
    GPIO.setmode(GPIO.BCM)
    
    with app.app_context():
        configs = GpioConfig.query.filter_by(enabled = True).all()
    
    for config in configs:
        if config.gpio_type == GpioType.OUTPUT:
            GPIO.setup(config.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
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