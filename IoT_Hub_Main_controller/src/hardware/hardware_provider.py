import os
APP_MODE = os.getenv("APP_MODE", "pi")

if APP_MODE == "pi":
    from hardware.gpio_rpi import RaspberryPiGPIO
    from hardware.sim_modem import SIMModem
    from hardware.pump_gpio import PumpGPIO
    from hardware.phase_gpio import PhaseGPIO
    from hardware.current_sensor import CurrentSensor
    from hardware.lcd_hw import LCDDriver


#Mock hardware import
from hardware.mock.mock_gpio import MockGPIO
from hardware.mock.mock_sim_modem import MockSIMModem
from hardware.mock.mock_pump_gpio import MockPumpGPIO
from hardware.mock.mock_phase_gpio import MockPhaseGPIO
from hardware.mock.mock_current_sensor import MockCurrentSensor
from hardware.mock.mock_lcd import MockLCD 


class HardwareProvider:

    def __init__(self, mode):
        self.mode = mode.upper()

    def get_gpio(self):
        if self.mode == "SIMULATOR":
            return MockGPIO()
        return RaspberryPiGPIO()

    def get_sim(self):
        if self.mode == "SIMULATOR":
            return MockSIMModem()
        return SIMModem()

    def get_pump_gpio(self, *args):
        if self.mode == "SIMULATOR":
            return MockPumpGPIO(*args)
        return PumpGPIO(*args)

    def get_phase_gpio(self):
        if self.mode == "SIMULATOR":
            return MockPhaseGPIO()
        return PhaseGPIO()

    def get_current_sensor(self, *args):
        if self.mode == "SIMULATOR":
            return MockCurrentSensor(*args)
        return CurrentSensor()

    def get_lcd(self):
        if self.mode == "SIMULATOR":
            return MockLCD()
        return LCDDriver()