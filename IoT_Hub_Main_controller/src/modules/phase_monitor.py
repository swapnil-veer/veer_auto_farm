import config
import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
from logging_config import logger
from app import db
from database.models.phase_log import PhaseLog
from datetime import datetime

phase_data = {
    'timestamp':datetime.now().strftime("%Y-%m-%d %H:%M:%S"),    
    'green_led': 0,
    'yellow_led': 0,
    'red_led': 0
}

# Global dict that can be imported in main.py

class LedMonitor:
    def __init__(self, app = None, poll_interval=1):
        """
        Monitor LED states in the background.
        Updates global phase_data dict.
        :param poll_interval: seconds between checks
        """
        self.green_pin = config.GPIO_PINS["phase_monitor_green"]["gpio_pin"]
        self.yellow_pin = config.GPIO_PINS["phase_monitor_yellow"]["gpio_pin"]
        self.red_pin = config.GPIO_PINS["phase_monitor_red"]["gpio_pin"]
        self.app = app
        self.poll_interval = poll_interval

        self._state = {
            "green_led": False,
            "yellow_led": False,
            "red_led": False,
            "timestamp": datetime.utcnow()
        }

        self._lock = threading.Lock()

        # Start background thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("LedMonitor started background monitoring thread.")

    def is_power_available(self) -> bool:
        """CommandProcessor साठी: Green LED ON?"""
        with self._lock:
            return self._state["green_led"]
    
    def get_status(self) -> str:
        """MainController साठी: power_ok/wait/fault"""
        with self._lock:
            if self._state["green_led"]:
                return "power_ok"
            elif self._state["yellow_led"]:
                return "power_wait"
            elif self._state["red_led"]:
                return "power_fault"
            return "power_fault"
    
    def get_current_state(self) -> dict:
        """Read-only snapshot"""
        with self._lock:
            return self._state.copy()
        
    def _monitor_loop(self):
            """Poll GPIO pins and react on changes"""
            logger.info("LedMonitor polling loop started")

            while True:
                try:
                    green = bool(GPIO.input(self.green_pin))
                    yellow = bool(GPIO.input(self.yellow_pin))
                    red = bool(GPIO.input(self.red_pin))

                    with self._lock:
                        changed = (
                            green != self._state["green_led"] or
                            yellow != self._state["yellow_led"] or
                            red != self._state["red_led"]
                        )

                    if changed:
                        self._handle_state_change(green, yellow, red)

                except Exception as e:
                    logger.exception(f"LedMonitor error: {e}")

                time.sleep(self.poll_interval)

    def _handle_state_change(self, green: bool, yellow: bool, red: bool):
            """Update in-memory state + persist DB"""
            now = datetime.utcnow()

            with self._lock:
                self._state.update({
                    "green_led": green,
                    "yellow_led": yellow,
                    "red_led": red,
                    "timestamp": now
                })

            logger.info(
                f"Phase change detected | Green={green} Yellow={yellow} Red={red}"
            )

            self._persist_phase_log(green, yellow, red, now)

    def _persist_phase_log(
            self,
            green: bool,
            yellow: bool,
            red: bool,
            timestamp: datetime
        ):
            """
            Persist phase log.
            Uses independent app context (thread-safe).
            """
            with self.app.app_context():
                try:
                    phase_log = PhaseLog(
                        green_led=green,
                        yellow_led=yellow,
                        red_led=red,
                        timestamp=timestamp
                    )

                    db.session.add(phase_log)
                    db.session.commit()

                except Exception as e:
                    db.session.rollback()
                    logger.exception(f"Failed to persist PhaseLog: {e}")

