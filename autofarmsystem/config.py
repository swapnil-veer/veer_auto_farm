import RPi.GPIO as GPIO

GPIO_PINS = {
    "sda" : {"pin": 2, "type": "i2c"}, # I2C SDA (BCM 2, Pin 3)
    "scl" : {"pin": 3, "type": "i2c"},  #I2C SCL (BCM 3, Pin 5)
    "relay_pi_onoff" : {"pin":23, "type": "output"},  #(Pi On-Off Relay) (BCM 23, Pin 16)
    "relay_dry_run" : {"pin": 24, "type": "output"},   #(Dry-Run Control Relay) (BCM 24, Pin 18)
    "phase_monitor_green" : {"pin": 17, "type": "input"}, # Phase Monitor - OK (Green LED) (BCM 17, Pin 11)
    "phase_monitor_yellow" : {"pin": 27, "type": "input"},    # Phase Monitor - Initial Wait (Yellow LED) (BCM 27, Pin 13)
    "phase_monitor_red" : {"pin": 22, "type": "input"},       # Phase Monitor - Fault (Red LED) (BCM 22, Pin 15)
    "bypass_switch" :{"pin": 11, "type": "input"},            # DPST Switch 2A (BCM 11, Pin 23)
}


def setup_gpio():
    """Setup all GPIO pins based on their type."""
    GPIO.setmode(GPIO.BCM)

    for key, data in GPIO_PINS.items():
        if data["type"] == "output":
            GPIO.setup(data["pin"], GPIO.OUT)
        elif data["type"] == "input":
            GPIO.setup(data["pin"], GPIO.IN)

def cleanup_gpio():
    """Cleanup GPIO on exit."""
    GPIO.cleanup()