import config
import RPi.GPIO as GPIO
from logging_config import logger

phase_status = {"green": False, "yellow": False, "red": False}


class PhaseMonitor:
    def __init__(self):
        """Initialize GPIO pins and event detection."""
        self.green_pin = config.GPIO_PINS["phase_monitor_green"]["pin"]
        self.yellow_pin = config.GPIO_PINS["phase_monitor_yellow"]["pin"]
        self.red_pin = config.GPIO_PINS["phase_monitor_red"]["pin"]

        # Setup event detection for each phase pin
        GPIO.add_event_detect(self.green_pin, GPIO.BOTH, callback=self._phase_change, bouncetime=200)
        GPIO.add_event_detect(self.yellow_pin, GPIO.BOTH, callback=self._phase_change, bouncetime=200)
        GPIO.add_event_detect(self.red_pin, GPIO.BOTH, callback=self._phase_change, bouncetime=200)

        # Initial state read
        self._update_phase_status()

    def _update_phase_status(self):
        """Read all pins and update phase_status dictionary."""
        phase_status["green"] = GPIO.input(self.green_pin)
        phase_status["yellow"] = GPIO.input(self.yellow_pin)
        phase_status["red"] = GPIO.input(self.red_pin)
        logger.info(f"Phase Status Updated: {phase_status}")

    def _phase_change(self, channel):
        """Callback when any phase pin changes state."""
        self._update_phase_status()
