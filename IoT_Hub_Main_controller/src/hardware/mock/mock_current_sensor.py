
class MockCurrentSensor:
    def __init__(self):
        self.readings = self.readings
        self.index = 0

    def read_amp(self) :
        if not self.readings:
            return 0
        value = self.readings[min(self.index, len(self.readings)-1)]
        self.index += 1
        return float(value)