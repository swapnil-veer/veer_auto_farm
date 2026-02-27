from app import create_app, db
app = create_app()
import config

with app.app_context():
    db.create_all()
config.seed_gpio_config(app)
config.seed_pumps_from_gpio(app)
config.setup_gpio(app)

# config.cleanup_gpio()


from main_controller import MainController

import threading
from settings import SENSORS
from file_manager import log_sensors
from modules.phase_monitor import LedMonitor
from modules.lcd_display.lcd_module import LCD
import time
from logging_config import logger
from modules.pump_control import PumpManager, PumpContextManager
from command_processor import CommandProcessor
from modules.sim800l.sim import FarmSMSHandler
from modules.sim800l.sms_service import SMSService

#create pump manager instance
pump_manager = PumpManager(app = app)

pump_context_manager = PumpContextManager(relay_manager = pump_manager)
led_monitor = LedMonitor(app = app, poll_interval=1)

# command_processor instance
processor = CommandProcessor(pump_context_manager=pump_context_manager, app = app)
# 3. **NEW: Create SMS Handler (instead of global sms_thread)**
sms_handler = FarmSMSHandler(app = app)  

# Create MainController (central brain)
main_controller = MainController(
    command_processor=processor,
    led_monitor = led_monitor,
    sms_handler=sms_handler,
)

# Wire CommandProcessor -> MainController for events (आधी event_handler field add केलेला असेल तर)
processor.event_handler = main_controller.handle_event
processor.power_service = main_controller.power_service

sms_service = SMSService(main_controller, sms_handler, app = app)
sms_service.start()


# sim800l = SIM800L()
time.sleep(2)

lcd = LCD(main_controller=main_controller)          # Lcd thread started
time.sleep(2)

time.sleep(5)
log_sensors(sensors=SENSORS)
time.sleep(5)

t2 = threading.Thread(target=processor.run, daemon=True)
t2.start()

# from database.models import User
# user = User (phone = "+917038835527", name = "Swapnil", email = "veerswapnil00@gmail.com", is_owner = True, is_superuser = True)
# with app.app_context():
#     db.session.add(user)
#     db.session.commit()
try:
    while True:
        time.sleep(2)
except KeyboardInterrupt:
    config.cleanup_gpio()
    logger.info("Main loop interrupted - cleanup already registered")

# TODO: Delete all not working
# TODO: Create superuser
# TODO: led moniter db integration
# TODO: make lcd_display as plugin
# TODO: this system should work without RPi module, so we can test code without Pi
# TODO: add testcases 
# TODO: create multi pump logic


# print(user)
