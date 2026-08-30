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
            "sim_status" : None,
            "signal_strength": None,
            "safety_lock": None,
            "last_event": None,

            "active_command_id":None,
            "active_command_mode":None,
            "runtime_sec": None,
            "target_duration_sec": None,

            "next_command_id" : None,
            "next_command_mode" : None,
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

            elif etype == "SIM_STATUS":
                self._state["sim_status"] = data["sim_status"]
                
            elif etype == "SIGNAL_STRENGTH":
                self._state["signal_strength"] = data["signal_strength"]

    def set_active_command(
        self,
        command_id,
        command_mode,
        runtime_sec,
        target_duration_sec,
        ):
        self._state["active_command_id"] = command_id
        self._state["active_command_mode"] = command_mode
        self._state["runtime_sec"] = runtime_sec
        self._state["target_duration_sec"] = target_duration_sec


    def clear_current_command(self):
        self._state["active_command_id"] = None
        self._state["active_command_mode"] = None
        self._state["runtime_sec"] = None
        self._state["target_duration_sec"] = None

    def set_next_command(
        self,
        command_id,
        command_mode,
        ):
        self._state["next_command_id"] = command_id
        self._state["next_command_mode"] = command_mode


    def clear_next_command(self):
        self._state["next_command_id"] = None
        self._state["next_command_mode"] = None

