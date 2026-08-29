class MockPhaseGPIO:
    def __init__(self):
        self.power = False

    def read(self):
    # always power available
        return {
            "green": self.power,
            "yellow": False,
            "red": False,
            }

    def set_power(self, value:bool):
        self.power = value

    