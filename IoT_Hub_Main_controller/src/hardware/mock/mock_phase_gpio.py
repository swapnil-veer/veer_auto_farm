class MockPhaseGPIO:
    def read(self):
    # always power available
        return {
            "green": True,
            "yellow": False,
            "red": False,
            }