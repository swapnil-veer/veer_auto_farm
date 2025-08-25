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


    def pump_off(self):
        """Turn off pump and log the event."""
        GPIO.output(self.pump_pin, GPIO.LOW)
        logger.info("Pump turned OFF.")
        self.lcd.display_message("Pump OFF")

    def pump_wait(self, duration=DEFAULT_DURATION):
        """Wait for green phase to become True, then start pump in a thread."""
        logger.info("Pump waiting for green phase...")
        GPIO.remove_event_detect(self.phase_monitor.green_pin)  # Avoid duplicate events
        GPIO.add_event_detect(
            self.phase_monitor.green_pin,
            GPIO.RISING,
            callback=lambda channel: self.start_pump_thread(duration),
            bouncetime=200
        )

    def start_pump_thread(self, duration):
        """Start _pump_on in a separate thread (public method)."""
        threading.Thread(target=self._pump_on, args=(duration,), daemon=True).start()

    def _pump_on(self, duration=DEFAULT_DURATION):
        """Start pump and monitor phases while running (private)."""
        if not phase_status["green"]:
            logger.warning("Cannot start pump. Green phase not available.")
            return

        # Activate pump
        GPIO.output(self.pump_pin, GPIO.HIGH)
        logger.info(f"Pump started. Will run for {duration} seconds unless fault detected.")
        self.lcd.display_message("Pump ON")

        start_time = time.time()
        while time.time() - start_time < duration:
            if phase_status["red"]:  # Fault detected
                logger.error("Phase fault detected! Stopping pump immediately.")
                self.pump_off()
                remaining_time = duration - (time.time() - start_time)
                if remaining_time > 0:
                    logger.info(f"Waiting for green phase to resume for {remaining_time:.1f}s.")
                    self.pump_wait(remaining_time)  # Resume after recovery
                return
            time.sleep(1)

        logger.info("Pump run duration completed.")
        self.pump_off()
