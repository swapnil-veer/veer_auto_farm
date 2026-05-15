#hardware/gpio_mock.py
class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    IN = "IN"
    LOW = 0
    HIGH = 1

    def __init__(self):
        self.pins = {}

    def setmode(self, mode):
        print(f"[MOCK GPIO] setmode({mode})")

    def setup(self, pin, direction, initial=None):
        self.pins[pin] = initial or self.LOW
        print(f"[MOCK GPIO] setup pin {pin} as {direction}")

    def output(self, pin, value):
        self.pins[pin] = value
        print(f"[MOCK GPIO] pin {pin}={'HIGH' if value else 'LOW'}")

    def input(self, pin):
            return self.pins.get(pin, self.LOW)

    def cleanup(self):
        print("[MOCK GPIO] cleanup")
