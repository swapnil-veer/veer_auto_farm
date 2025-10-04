import time
from contextlib import contextmanager
from config import GPIO_PINS, set_high, set_low



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

class PumpManager:
    """
    Core relay manager for relay control and power state.
    """
    def __init__(self):
        self.power = False
        self.state = False         #Default off
        self.pump_pin = GPIO_PINS["relay_pi_onoff"]["pin"]

    def relay_on(self):
        """Turn relay on."""
        print("Relay turned ON")
        self.state = True
        set_high(self.pump_pin)

    def relay_off(self):
        """Turn relay off."""
        print("Relay turned OFF")
        self.state = False
        set_low(self.pump_pin)

    def set_power(self, state: bool):
        """Set power state."""
        self.power = state

    def get_pump_state(self):
        return self.state

pump_manager = PumpManager()
pump_context_manager = PumpContextManager(pump_manager)