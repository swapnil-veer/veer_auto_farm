# hardware/phase_gpio.py
import RPi.GPIO as GPIO
import config

class PhaseGPIO:
    def __init__(self):
        self.green_pin = config.GPIO_PINS["phase_monitor_green"]["gpio_pin"]
        self.yellow_pin = config.GPIO_PINS["phase_monitor_yellow"]["gpio_pin"]
        self.red_pin = config.GPIO_PINS["phase_monitor_red"]["gpio_pin"]

    def read(self) -> dict:
        # NOTE: preserving your inversion logic
        return {
        "green": not bool(GPIO.input(self.green_pin)),
        "yellow": bool(GPIO.input(self.yellow_pin)),
        "red": bool(GPIO.input(self.red_pin)),
 }