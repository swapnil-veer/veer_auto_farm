import config
config.cleanup_gpio()
config.setup_gpio()

from main_controller import MainController

import threading
from settings import SENSORS
from file_manager import log_sensors
from modules.phase_monitor import LedMonitor, phase_data
from modules.lcd_display.lcd_module import LCD
import time
from logging_config import logger
from modules.pump_control import pump_manager
from command_processor import processor_thread, processor
from modules.sim800l.sim import sms_thread
from modules.sim800l.sms_processor import sms_processor, set_controller

# Create MainController (central brain)
main_controller = MainController(
    command_processor=processor,
    phase_data=phase_data,
    sms=sms_thread,
)

# Wire CommandProcessor -> MainController for events (आधी event_handler field add केलेला असेल तर)
processor.event_handler = main_controller.handle_event

# Wire SMS side -> MainController for incoming commands
set_controller(main_controller)


# sim800l = SIM800L()
time.sleep(2)
LCD()           # Lcd thread started
time.sleep(2)

thread = threading.Thread(target=sms_processor, daemon=True)
thread.start()  

time.sleep(5)
LedMonitor(poll_interval=1)       # led monitoring started at new thread
time.sleep(5)
log_sensors(sensors=SENSORS)
time.sleep(5)

t2 = threading.Thread(target=processor_thread, daemon= True)
t2.start()

while True:
    time.sleep(2)


