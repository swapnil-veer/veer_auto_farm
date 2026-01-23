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
from modules.pump_control import PumpManager, PumpContextManager
from command_processor import CommandProcessor
from modules.sim800l.sim import FarmSMSHandler
from modules.sim800l.sms_service import SMSService

#create pump manager instance
pump_manager = PumpManager()
pump_context_manager = PumpContextManager(pump_manager)
led_monitor = LedMonitor(poll_interval=1)

# command_processor instance
processor = CommandProcessor(
    pump_context_manager=pump_context_manager,
    phase_data=phase_data,
    poll_interval=5,
)
# 3. **NEW: Create SMS Handler (instead of global sms_thread)**
sms_handler = FarmSMSHandler()  

# Create MainController (central brain)
main_controller = MainController(
    command_processor=processor,
    phase_data=phase_data,
    sms_handler=sms_handler,
)

# Wire CommandProcessor -> MainController for events (आधी event_handler field add केलेला असेल तर)
processor.event_handler = main_controller.handle_event
processor.power_service = main_controller.power_service

sms_service = SMSService(main_controller, sms_handler)
sms_service.start()


# sim800l = SIM800L()
time.sleep(2)

lcd = LCD(main_controller=main_controller, logger=logger)          # Lcd thread started
time.sleep(2)

LedMonitor(poll_interval=1)       # led monitoring started at new thread
time.sleep(5)
log_sensors(sensors=SENSORS)
time.sleep(5)

t2 = threading.Thread(target=processor.run, daemon=True)
t2.start()

try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    config.cleanup_gpio()
    logger.info("Main loop interrupted - cleanup already registered")



