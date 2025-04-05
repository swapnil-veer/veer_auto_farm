import config

class PhaseMonitor:
    def __init__(self):
        """Initialize Phase Monitor using config.py"""
        config.setup_gpio()

    def get_phase_status(self):
        """Check phase status and return a message."""
        if config.GPIO.input(config.GPIO_PINS["phase_monitor_green"]["pin"]):
            return "Phase OK"
        elif config.GPIO.input(config.GPIO_PINS["phase_monitor_yellow"]["pin"]):
            return "Phase Wait"
        elif config.GPIO.input(config.GPIO_PINS["phase_monitor_red"]["pin"]):
            return "Phase Fault"
        else:
            return "Unknown"

    def cleanup(self):
        """Cleanup GPIO"""
        config.cleanup_gpio()
