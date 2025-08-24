
import time
from RPLCD.i2c import CharLCD

class LCD:
    def __init__(self, i2c_address=0x27):
        """
        Initialize the LCD with I2C address (default: 0x27)
        """
        self.lcd = CharLCD(i2c_expander="PCF8574", address=i2c_address,
                           port=1, cols=20, rows=4, charmap="A02",
                           auto_linebreaks=True)
        self.clear()

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
