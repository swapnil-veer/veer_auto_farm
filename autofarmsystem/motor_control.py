import config
from phase_monitor import PhaseMonitor
from lcd_display import LCD
import time

class MotorControl:
    def __init__(self):
        """Initialize Motor Control and LCD using config.py"""
        config.setup_gpio()
        self.lcd = LCD()
        self.phase_monitor = PhaseMonitor()

    def control_pump(self):
        """Decide whether to turn the pump ON or OFF based on phase status."""
        status = self.phase_monitor.get_phase_status()
        pump_pin = config.GPIO_PINS["relay_pi_onoff"]["pin"]

        if status == "Phase OK":
            config.GPIO.output(pump_pin, config.GPIO.HIGH)  # Turn ON Pump
            self.lcd.display("PUMP ON", "Watering Farm")
        else:
            config.GPIO.output(pump_pin, config.GPIO.LOW)  # Turn OFF Pump
            self.lcd.display("PUMP OFF", "Phase Issue!")

        return status

    def monitor_and_control(self):
        """Continuously check phase status and control pump accordingly."""
        last_status = None
        while True:
            status = self.control_pump()
            if status != last_status:
                print(f"Updated Status: {status}")
                last_status = status
            time.sleep(2)

    def cleanup(self):
        """Cleanup GPIO"""
        config.cleanup_gpio()
