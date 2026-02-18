import time
from contextlib import contextmanager
from config import GPIO_PINS, set_high, set_low
from database.models.pump import Pump, PumpRun
from datetime import datetime
from logging_config import logger
from app import db


class PumpContextManager:
    """
    Context manager for safely turning the relay on and off.
    Ensures relay is turned off on exit, even if exceptions occur.
    """
    def __init__(self, relay_manager, cmd_id = None):
        self.relay_manager = relay_manager
        self.cmd_id = cmd_id
        self.is_on = False
        self.pump_run_id = None

    def set_cmd_id(self, cmd_id):  # ✅ Setter method
        self.cmd_id = cmd_id

    def __enter__(self):
        self.pump_run_id = self.relay_manager.relay_on(self.cmd_id)
        self.is_on = True
        return self.pump_run_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_on:
            self.relay_manager.relay_off(self.pump_run_id)
        # Re-raise exception if any
        return False

# class PumpManager:
#     """
#     Core relay manager for relay control and power state.
#     """
#     def __init__(self):
#         self.power = False
#         self.state = False         #Default off
#         self.pump_pin = GPIO_PINS["relay_pi_onoff"]["pin"]

#     def relay_on(self):
#         """Turn relay on."""
#         print("Relay turned ON")
#         self.state = True
#         set_high(self.pump_pin)

#     def relay_off(self):
#         """Turn relay off."""
#         print("Relay turned OFF")
#         self.state = False
#         set_low(self.pump_pin)

#     def set_power(self, state: bool):
#         """Set power state."""
#         self.power = state

#     def get_pump_state(self):
#         return self.state

class PumpManager:
    def __init__(self, app = None, pump_id : int = None):
        self.app = app
        self.logger = logger
        self._resolve_pump(pump_id)
        self.current_run = None
        self.state = False

        self._pump_id = None
        self._pump_name = None
        self._pin = None
        self.state = False
        self.current_run_id = None
        
        self._resolve_pump(pump_id)
        logger.info(f"PumpManager initialized: ID={self._pump_id}")
    def _resolve_pump(self, pump_id : int = None):
        """Resolve pump safely with app context."""
        with self.app.app_context():
            if pump_id:
                self._pump = Pump.query.get(pump_id)
            else:
                self._pump = Pump.query.first()
            
            if not self._pump:
                raise RuntimeError("No enabled pump configured!")
            
            self._pump_id = self._pump.id
            self._pump_name = self._pump.name
            self._pin = self._pump.gpio_config.gpio_pin
            logger.info(f"Pump resolved: {self._pump_name} → GPIO {self._pin}")

    def relay_on(self, command_id: int):
        """Turn pump ON and log PumpRun."""
        if self.state:
            logger.warning(f"Pump {self._pump_id} already ON")
            return self.current_run.id if self.current_run else None

        try:
            set_high(self._pin)
            self.state = True
            logger.info(f"Pump ON: {self._pump.name} (GPIO {self._pin})")

            with self.app.app_context():
                pump_run = PumpRun(
                    pump_id=self._pump_id,
                    on_command_id=command_id,
                    on_time=datetime.utcnow()
                )
                db.session.add(pump_run)
                db.session.commit()
                self.current_run_id = pump_run.id
                return self.current_run_id
                
        except Exception as e:
            logger.error(f"Pump ON failed: {e}")
            set_low(self._pin)  # Safety off
            self.state = False
            raise

    def relay_off(self, pump_run_id : int):
        """Turn pump OFF and update run record."""
        if not self.state:
            return

        run_id = pump_run_id or (self.current_run_id if self.current_run_id else None)
        if not run_id:
            logger.warning("No pump_run_id provided")
            return

        try:
            set_low(self._pin)
            self.state = False
            logger.info(f"Pump OFF: {self._pump.name}")

            with self.app.app_context():
                pump_run = PumpRun.query.get(run_id)
                if pump_run:
                    pump_run.off_time = datetime.utcnow()
                    pump_run.calculate_duration()
                    db.session.commit()
                self.current_run_id = None
                
        except Exception as e:
            logger.error(f"Pump OFF failed: {e}")
            raise

    def get_status(self) -> dict:
        """Get current pump status."""
        return {
            'pump_id': self._pump_id,
            'pump_name': self._pump_name,
            'pin': self._pin,
            'state': self.state,
            'current_run_id': self.current_run_id 
        }
    
    def set_power(self, state: bool):
        """Set power state."""
        self.power = state

    def get_pump_state(self):
        return self.state
