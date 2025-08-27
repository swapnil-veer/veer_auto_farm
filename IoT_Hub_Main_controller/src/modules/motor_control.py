import config
from phase_monitor import phase_status, PhaseMonitor
from IoT_Hub_Main_controller.src.modules.lcd_display.lcd_module import LCD
import time
from logging_config import logger
import RPi.GPIO as GPIO
import threading

DEFAULT_DURATION = 30


class MotorControl:
    def __init__(self):
        """Initialize Motor Control and LCD."""
        self.lcd = LCD()
        self.phase_monitor = PhaseMonitor()
        self.pump_pin = config.GPIO_PINS["relay_pi_onoff"]["pin"]
        self.state = "off" # off, waiting, running
        self.duration = 30
        self._stop_event = threading.Event()
        self._pump_thread = None

    def get_motor_state(self):
        return self.state

    def pump_off(self):
        """Turn off pump and log the event."""
        GPIO.output(self.pump_pin, GPIO.LOW)
        self.state = "off"
        logger.info("Pump turned OFF.")
        self.lcd.display_message("Pump OFF")

    def pump_wait(self, duration= self.duration):
        """Wait for green phase to become True, then start pump in a thread."""
        logger.info("Pump waiting for green phase...")
        self.state = "waiting"
        while not self.phase_status["green"]:
            if self._stop_event.is_set():
                self.state = "off"
                return None  # indicates stop
            time.sleep(1)
        self._pump_on(duration=duration)

    def start_pump_thread(self, duration = self.duration):
        """Start _pump_on in a separate thread (public method)."""
        if self._pump_thread and self._pump_thread.is_alive():
            # Stop existing pump thread before starting new
            self.pump_off()
            self._pump_thread.join()

        self._pump_thread = threading.Thread(target=self._pump_on, args=(duration,))
        self._pump_thread.start()

    def _pump_on(self, duration=self.duration):
        """Start pump and monitor phases while running (private)."""
        self._stop_event.clear()
        if not phase_status["green"]:
            self.pump_wait(duration)   # this is invoke wait function

        # Activate pump
        GPIO.output(self.pump_pin, GPIO.HIGH)
        logger.info(f"Pump started. Will run for {duration} seconds unless fault detected.")
        self.state = "on"
        self.lcd.display_message("Pump ON")

        start_time = time.time()
        while time.time() - start_time < duration:
            if self._stop_event.is_set():
                break
            elif phase_status["red"]:  # Fault detected
                logger.error("Phase fault detected! Stopping pump immediately.")
                self.pump_off()
                remaining_time = duration - (time.time() - start_time)
                if remaining_time > 0:
                    logger.info(f"Waiting for green phase to resume for {remaining_time:.1f}s.")
                    self.pump_wait(remaining_time)  # Resume after recovery
                return
            time.sleep(1)
        else:
            logger.info("Pump run duration completed.")
        self.pump_off()
