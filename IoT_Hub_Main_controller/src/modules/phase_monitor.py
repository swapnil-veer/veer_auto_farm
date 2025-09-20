import config
import RPi.GPIO as GPIO
import time
import threading
from logging_config import logger
from global_var import sensor_data

# Global dict that can be imported in main.py

class LedMonitor:
    def __init__(self, poll_interval=1):
        """
        Monitor LED states in the background.
        Updates global sensor_data dict.
        :param poll_interval: seconds between checks
        """
        self.green_pin = config.GPIO_PINS["phase_monitor_green"]["pin"]
        self.yellow_pin = config.GPIO_PINS["phase_monitor_yellow"]["pin"]
        self.red_pin = config.GPIO_PINS["phase_monitor_red"]["pin"]

        self._poll_interval = poll_interval

        # Start background thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("LedMonitor started background monitoring thread.")

    def _monitor_loop(self):
        """Background loop to update LED states."""
        global sensor_data
        while True:
            updated = False

            green_state = GPIO.input(self.green_pin)
            yellow_state = GPIO.input(self.yellow_pin)
            red_state = GPIO.input(self.red_pin)

            if sensor_data['green_led'] != green_state:
                sensor_data['green_led'] = green_state
                logger.info(f"Green LED changed: {green_state}")
                updated = True

            if sensor_data['yellow_led'] != yellow_state:
                sensor_data['yellow_led'] = yellow_state
                logger.info(f"Yellow LED changed: {yellow_state}")
                updated = True

            if sensor_data['red_led'] != red_state:
                sensor_data['red_led'] = red_state
                logger.info(f"Red LED changed: {red_state}")
                updated = True

            if not updated:
                # No change, skip logging
                pass

            time.sleep(self._poll_interval)


# Example usage
if __name__ == "__main__":
    monitor = LedMonitor(poll_interval=1)
    try:
        while True:
            print(sensor_data)  # Directly access global dict
            time.sleep(2)
    except KeyboardInterrupt:
        GPIO.cleanup()