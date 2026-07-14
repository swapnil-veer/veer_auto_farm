# services/pump_service.py
from logging_config import logger

class PumpService:
    def __init__(self, gpio, repository, pump_id):
        self.gpio = gpio
        self.repo = repository
        self.current_run_id = None
        self.pump_id = pump_id
        self.logger = logger

    def start(self, command_id: int) -> int:
        if self.gpio.is_on():
            self.logger.warning("Pump already running")
            return self.current_run_id

        try:
            self.gpio.on()
            run_id = self.repo.start_run(pump_id=self.pump_id, command_id=command_id)
            self.current_run_id = run_id
            return run_id
        except Exception:
            self.gpio.off() # safety
            self.current_run_id = None
            raise

    def stop(self, run_id: int | None = None):
        if not self.gpio.is_on():
            return

        rid = run_id or self.current_run_id
        if not rid:
            self.logger.warning("No run ID to stop")
            return

        self.gpio.off()
        self.repo.stop_run(rid)
        self.current_run_id = None

    def is_running(self) -> bool:
        return self.gpio.is_on()