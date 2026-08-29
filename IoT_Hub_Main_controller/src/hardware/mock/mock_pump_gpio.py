class MockPumpGPIO:
    def __init__(self, gpio, pin=None):
        self.gpio = gpio
        self.pin = pin
        self.state = False

    def on(self):
        self.state = True
        print("[MOCK GPIO] Pump ON")

    def off(self):
        self.state = False
        print("[MOCK GPIO] Pump OFF")

    def is_on(self):
        return self.state