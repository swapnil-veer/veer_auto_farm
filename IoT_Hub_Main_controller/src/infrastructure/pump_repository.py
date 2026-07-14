# infrastructure/pump_repository.py
from app import db
from database.models.pump import Pump, PumpRun
from datetime import datetime
from logging_config import logger

class PumpRepository:
    def __init__(self, app):
        self.app = app
        self.logger = logger

    def get_default_pump_id(self) -> int:
        with self.app.app_context():
            pump = Pump.query.first()
            if not pump:
                raise RuntimeError("No enabled pump configured")
            return pump.id
        
    def get_pump_gpio_pin(self, pump_id) -> int:
        with self.app.app_context():
            pump = Pump.query.get(pump_id)
            if not pump:
                raise RuntimeError(f"Pump {pump_id} not found")
            return pump.gpio_config.gpio_pin

    def start_run(self, pump_id: int, command_id: int) -> int:
        with self.app.app_context():
            run = PumpRun(
            pump_id=pump_id,
            on_command_id=command_id,
            on_time=datetime.utcnow(),
            )
            db.session.add(run)
            db.session.commit()
            return run.id

    def stop_run(self, run_id: int):
        with self.app.app_context():
            run = PumpRun.query.get(run_id)
            if not run:
                self.logger.warning(f"No PumpRun {run_id}")
                return
            run.off_time = datetime.utcnow()
            run.calculate_duration()
            db.session.commit()