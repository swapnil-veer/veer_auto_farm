from threading import Lock
from copy import deepcopy
from logging_config import logger


class SystemState:
    """
    Centralized runtime snapshot of the system.

    Updated through events.
    Read by LCD, STATUS command, future UI, etc.
    """

    def __init__(self):
        self._lock = Lock()

        self._state = {
            "power_available": None,
            "pump_running": False,
            "pump_mode": None,
            "active_command_id": None,
            "signal_strength": None,
            "safety_lock": None,
            "last_event": None,
        }

    def snapshot(self):
        with self._lock:
            return deepcopy(self._state)

    def update(self, **kwargs):
        with self._lock:
            self._state.update(kwargs)

    def handle_event(self, event: dict):
        logger.debug(f"system state received : {event}")

        etype = event.get("type")
        data = event.get("data", {})

        with self._lock:

            self._state["last_event"] = etype

            if etype == "PUMP_STARTED":
                self._state["pump_running"] = True
                self._state["pump_mode"] = data.get("mode")
                self._state["active_command_id"] = data.get("command_id")

            elif etype in (
                "PUMP_COMPLETED",
                "PUMP_ABORTED_MANUAL_STOP",
                "PUMP_ABORTED_POWER_LOSS",
                "PUMP_AUTO_STOPPED",
            ):
                self._state["pump_running"] = False
                self._state["pump_mode"] = None
                self._state["active_command_id"] = None

            elif etype == "POWER_RESTORED":
                self._state["power_available"] = True

            elif etype == "POWER_LOST":
                self._state["power_available"] = False

            elif etype == "DRY_RUN_WAIT_STARTED":
                self._state["safety_lock"] = "DRY_RUN"

            elif etype == "DRY_RUN_RECOVERED":
                self._state["safety_lock"] = None
