import config
config.setup_gpio()

import threading
from settings import SENSORS
from file_manager import log_sensors
from modules.phase_monitor import LedMonitor
from modules.lcd_display.lcd_module import LCD
import time
from logging_config import logger
from modules.pump_control import pump_manager
from command_processor import processor_thread, processor
from modules.sim800l.sim import sms_thread

# sim800l = SIM800L()
time.sleep(2)
LCD()           # Lcd thread started
time.sleep(2)
sms_thread                       # sms thread started
time.sleep(5)
LedMonitor(poll_interval=1)       # led monitoring started at new thread
time.sleep(5)
log_sensors(sensors=SENSORS)
time.sleep(5)

t2 = threading.Thread(target=processor_thread, daemon= True)
t2.start()

while True:
    time.sleep(2)


