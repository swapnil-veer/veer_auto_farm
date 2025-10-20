
import time
from RPLCD.i2c import CharLCD
from ..sim800l.sim import sms_thread
from modules.phase_monitor import phase_data
from modules.pump_control import pump_manager
from command_processor import processor
import threading
from logging_config import logger

# signal_strength = sms_thread.get_signal_strength()



def get_system_status(phase_data):
    status =  {
        "power": "ON" if phase_data.get("green_led") == 1 else "OFF",
        "signal": sms_thread.get_signal_strength() or 0,
        "sim_status":  sms_thread.get_sim_status(),  
        # "network": sms_handler.get_network_name(),
        "pump_on": pump_manager.get_pump_state(),
        "pump_rem": round(processor.current_command['remaining_sec']/60) if processor.current_command else False,
        # "pump_total": pump_handler.total_today,
        # "battery": battery_handler.get_battery_percent()
    }
    return status
class LCD:
    def __init__(self, i2c_address=0x27, poll_interval=1):
        """
        Initialize the LCD with I2C address (default: 0x27)
        """
        print("in lcd")
        self.lcd = CharLCD(i2c_expander="PCF8574", address=i2c_address,
                           port=1, cols=20, rows=4, charmap="A02",
                           auto_linebreaks=True)
        self.lcd.write_string("VEER AUTO-FARM".center(7))
        time.sleep(2)
        self.clear()
        self.poll_interval = poll_interval
                # Start background thread
        self._thread = threading.Thread(target=self.display_thread, daemon=True)
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

    def get_signal_symbol(self, value):
        """Convert signal bars (0–5) to mobile-style bars."""
        network_sym = [
            0b00000,
            0b00000,
            0b00000,
            0b11111,
            0b01110,
            0b00100,
            0b00100,
            0b00100,]
        self.lcd.create_char(0, network_sym )

        bars = round(value/20)
            # Define 1 custom character per bar level (simple version)

        patterns = [
          ([0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000],  # empty
            [0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000]),
            
        ([0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b11100,
        0b11100],
        [0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000]),

        ([0b00000,
         0b00000,
         0b00000,
         0b00000,
         0b00111,
         0b00111,
         0b11111,
         0b11111],
         [0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000,
        0b00000]),

       ([0b00000,
         0b00000,
         0b00000,
         0b00000,
         0b00111,
         0b00111,
         0b11111,
         0b11111,],
        [0b00000,
         0b00000,
         0b11100,
         0b11100,
         0b11100,
         0b11100,
         0b11100,
         0b11100]),

        (
        [0b00000,
         0b00000,
         0b00000,
         0b00000,
         0b00111,
         0b00111,
         0b11111,
         0b11111],
        [0b00111,
         0b00111,
         0b11111,
         0b11111,
         0b11111,
         0b11111,
         0b11111,
         0b11111])
]

        bars = max(0, min(len(patterns) - 1, bars))
        self.lcd.create_char(1, patterns[bars][0])   # load into slot 0
        self.lcd.create_char(2, patterns[bars][1])   # load into slot 0

        return chr(0) + chr(1) + chr(2)  # printable symbol

    def static_lines(self):
        status = get_system_status(phase_data)
        if status["sim_status"] != True:
            signal_bar = "NO SIM"
        else:
            # signal = status["signal_bars"].ljust(7)[:7]
            signal_bar = self.get_signal_symbol(status["signal"])
        signal_text = signal_bar.ljust(7)[:7]
        power_text = f"PWR:{status['power']}".center(6)[:7]
        line1 = signal_text + power_text
        self.lcd.write_string(line1[:20])

        #line 2
        if status['pump_on']:
            line2 = f"PUMP:ON Rem:{status['pump_rem']}min"
        elif status["power"] == "OFF" and status['pump_rem'] != False:
            line2 = f"PUMP:OFF WAIT PWR"
        else:
            line2 = f"PUMP:OFF"
        return line1, line2

    def display_thread(self):
        while True:
            self.lcd.clear()
            self.lcd.cursor_pos = (0,0)
            for i, line in enumerate(self.static_lines()):
                self.lcd.cursor_pos = (i, 0)
                self.lcd.write_string(line[:20])
            # self.lcd.cursor_pos = (2,0)
            time.sleep(self.poll_interval)

