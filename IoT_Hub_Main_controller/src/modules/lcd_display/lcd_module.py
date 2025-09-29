
import time
from RPLCD.i2c import CharLCD
from sim800l.sim import sms_thread
from phase_monitor import phase_data
from pump_control import pump_manager
from command_processor import processor
import threading
from logging_config import logger

# signal_strength = sms_thread.get_signal_strength()

def get_signal_symbol() -> str:
    """Convert signal bars (0–5) to mobile-style bars."""
    bars = round(sms_thread.get_signal_strength()/20)
    symbols = [
        "     ",          # 0 bars
        "▂    ",          # 1 bar
        "▂▄   ",          # 2 bars
        "▂▄▆  ",          # 3 bars
        "▂▄▆█ ",          # 4 bars
        "▂▄▆█▉",          # 5 bars
    ]
    return symbols[max(0, min(5, bars))]

def get_system_status(phase_data):
    return {
        "power": "ON" if phase_data.get("green_led") == 1 else "OFF",
        "signal_bars": get_signal_symbol(),
        "sim_status": sms_thread.get_sim_status(),
        # "network": sms_handler.get_network_name(),
        "pump_on": pump_manager.get_pump_state(),
        "pump_rem": processor.current_command['remaining_sec'] if processor.current_command else False,
        # "pump_total": pump_handler.total_today,
        # "battery": battery_handler.get_battery_percent()
    }

class LCD:
    def __init__(self, i2c_address=0x27, poll_interval=1):
        """
        Initialize the LCD with I2C address (default: 0x27)
        """
        self.lcd = CharLCD(i2c_expander="PCF8574", address=i2c_address,
                           port=1, cols=20, rows=4, charmap="A02",
                           auto_linebreaks=True)
        self.clear()
        self.poll_interval = poll_interval
                # Start background thread
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("LCD Display started background monitoring thread.")

    def display(self, line1="", line2="", line3 = "", line4 = ""):
        """
        Display four lines of text on the LCD.
        """
        self.lcd.clear()
        self.lcd.write_string(line1)
        if line2:
            self.lcd.cursor_pos = (1, 0)  # Move to second line
            self.lcd.write_string(line2)
        elif line3:
            self.lcd.cursor_pos = (2, 0)  # Move to third line
            self.lcd.write_string(line3)
        elif line4:
            self.lcd.cursor_pos = (3, 0)  # Move to four line
            self.lcd.write_string(line4)

    def clear(self):
        """Clear the LCD screen."""
        self.lcd.clear()

    def close(self):
        """Close the LCD connection."""
        self.clear()

    def static_lines(self):
        status = get_system_status(phase_data)
        if status["sim_status"] != True:
            signal = "No sim"
        else:
            signal = status["signal_bars"].ljust(7)[:7]
        power_text = status['power'].center(6)[:6]
        line1 = signal + power_text

        #line 2
        if status['pump_on']:
            line2 = f"PUMP : ON Rem:{status['pump_rem']}"
        elif status["power"] == "OFF":
            line2 = f"PUMP:OFF Wait for PWR"
        else:
            line2 = f"PUMP : OFF"
        return line1, line2

    def display_thread(self):
        while True:
            # self.lcd.clear()
            for i, line in enumerate(self.static_lines()):
                self.lcd.write_line(i, line[:20])
            time.sleep(self.poll_interval)

