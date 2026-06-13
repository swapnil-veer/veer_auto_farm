# hardware/pump_gpio.py
# from config import set_high, set_low
from logging_config import logger

class PumpGPIO:
    def __init__(self, gpio, pin):
        self.gpio = gpio
        self.pin = pin
        self.gpio.setup(pin, gpio.OUT, initial=gpio.LOW)
        self.state = False

    def on(self):
        self.gpio.output(self.pin, self.gpio.HIGH)
        self.state=True

    def off(self):
        self.gpio.output(self.pin, self.gpio.LOW)
        self.state=False

    def is_on(self) -> bool:
        return self.state
    
