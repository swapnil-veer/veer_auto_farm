# services/phase_monitor.py
import time
import threading
from datetime import datetime
from logging_config import logger

class PhaseMonitor:
    def __init__(self, gpio_reader, repository, poll_interval=1):
        self.gpio = gpio_reader
        self.repo = repository
        self.poll_interval = poll_interval

        self._state = {
        "green_led": False,
        "yellow_led": False,
        "red_led": False,
        "timestamp": datetime.utcnow(),
        }

        self._lock = threading.Lock()

        self._thread = threading.Thread(
        target=self._loop, daemon=True
        )
        self._thread.start()

        logger.info("PhaseMonitor started")

    # ---------- Public API (for MainController / PowerStatusService) ----------

    def is_power_available(self) -> bool:
        with self._lock:
            return True
            return self._state["green_led"]

    def get_status(self) -> str:
        with self._lock:
            if self._state["green_led"]:
                return "power_ok"
            if self._state["yellow_led"]:
                return "power_wait"
            return "power_fault"

    def get_current_state(self) -> dict:
        with self._lock:
            return self._state.copy()

    # ---------- Internal loop ----------

    def _loop(self):
        while True:
            try:
                raw = self.gpio.read()
                self._handle_sample(raw)
            except Exception as e:
                logger.exception(f"PhaseMonitor error: {e}")
                time.sleep(self.poll_interval)

    def _handle_sample(self, raw: dict):
        green, yellow, red = raw["green"], raw["yellow"], raw["red"]

        with self._lock:
            changed = (
            green != self._state["green_led"] or
            yellow != self._state["yellow_led"] or
            red != self._state["red_led"]
            )

        if not changed:
            return

        now = datetime.utcnow()
        with self._lock:
            self._state.update({
            "green_led": green,
            "yellow_led": yellow,
            "red_led": red,
            "timestamp": now,
            })

        logger.info(
            f"Phase change | G={green} Y={yellow} R={red}"
            )

        # Persist (side effect)
        self.repo.save(green, yellow, red, now)