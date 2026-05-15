#hardware/gpio_rpi.py
class RaspberryPiGPIO:
    def __init__(self):
        import RPi.GPIO as GPIO # ✅ deferred import
        GPIO.setwarnings(False)
        self.GPIO = GPIO

    def setmode(self, mode):
        self.GPIO.setmode(mode)

    def setup(self, pin, direction, initial=None):
        if initial is not None:
            self.GPIO.setup(pin, direction, initial=initial)
        else:
            self.GPIO.setup(pin, direction)

    def output(self, pin, value):
        self.GPIO.output(pin, value)

    def input(self, pin):
        return self.GPIO.input(pin)

    def cleanup(self):
        self.GPIO.cleanup()

    # constants
    BCM = lambda self: self.GPIO.BCM
    OUT = lambda self: self.GPIO.OUT
    IN = lambda self: self.GPIO.IN
    LOW = lambda self: self.GPIO.LOW
    HIGH = lambda self: self.GPIO.HIGH