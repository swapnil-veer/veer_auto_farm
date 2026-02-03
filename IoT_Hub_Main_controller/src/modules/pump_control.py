import time
from contextlib import contextmanager
from config import GPIO_PINS, set_high, set_low
from database.models.pump import Pump, PumpRun
from datetime import datetime
from logging_config import logger


class PumpContextManager:
    """
    Context manager for safely turning the relay on and off.
    Ensures relay is turned off on exit, even if exceptions occur.
    """
    def __init__(self, relay_manager):
        self.relay_manager = relay_manager
        self.is_on = False

    def __enter__(self):
        self.relay_manager.relay_on()
        self.is_on = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_on:
            self.relay_manager.relay_off()
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
    def __init__(self, db_session, pump: Pump = None):
        self.db = db_session
        self.logger = logger

        # Resolve default pump if none provided
        if pump is None:
            pump = (self.db.query(Pump)         #default pump
                .order_by(Pump.id)
                .first()
            )
            
            if not pump:
                raise RuntimeError("No pump configured in system")

            self.logger.info(f"Default pump selected: {pump.name}")

        self.pump = pump
        self.current_run = None
        self.state = False

    def relay_on(self, command_id: int):
        if self.state:
            self.logger.warning(f"Pump already ON: {self.pump.name}")
            return

        pin = self.pump.gpio_config.pin_number

        self.logger.info(f"Pump ON: {self.pump.name} (GPIO {pin})")
        set_high(pin)
        self.state = True

        self.current_run = PumpRun(
            pump_id=self.pump.id,
            on_command_id=command_id,
            on_time=datetime.utcnow()
        )
        self.db.add(self.current_run)
        self.db.commit()

    def relay_off(self, command_id: int = None):
        if not self.state:
            return

        pin = self.pump.gpio_config.pin_number

        self.logger.info(f"Pump OFF: {self.pump.name} (GPIO {pin})")
        set_low(pin)
        self.state = False

        if self.current_run:
            self.current_run.off_time = datetime.utcnow()
            self.current_run.off_command_id = command_id
            self.current_run.calculate_duration()
            self.db.commit()
            self.current_run = None

    def set_power(self, state: bool):
        """Set power state."""
        self.power = state

    def get_pump_state(self):
        return self.state
