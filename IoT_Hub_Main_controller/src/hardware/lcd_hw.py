# hardware/lcd_hw.py
import threading
from RPLCD.i2c import CharLCD

class LCDDriver:
    def __init__(self, i2c_address=0x27):
        self.lcd_lock = threading.Lock()

        self.lcd = CharLCD(
        i2c_expander="PCF8574",
        address=i2c_address,
        port=1,
        cols=20,
        rows=4,
        charmap="A02",
        auto_linebreaks=False,
        )

        self._load_base_custom_chars()

    # ---------- Low-level LCD ops ----------

    def clear(self):
        with self.lcd_lock:
            self.lcd.clear()

    def write_line(self, row, text):
        with self.lcd_lock:
            self.lcd.cursor_pos = (row, 0)
            self.lcd.write_string(text[:20].ljust(20))

    def create_char(self, slot, pattern):
        with self.lcd_lock:
            self.lcd.create_char(slot, pattern)

        # ---------- Custom chars ----------

    def _load_base_custom_chars(self):
        network_top = [
        0b00000,
        0b00000,
        0b00000,
        0b11111,
        0b01110,
        0b00100,
        0b00100,
        0b00100,
        ]
        self.create_char(0, network_top)