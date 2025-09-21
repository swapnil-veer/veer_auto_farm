import config
import threading
from settings import SENSORS
from file_manager import log_sensors
from modules.phase_monitor import LedMonitor
from modules.lcd_display.lcd_module import LCD
# from modules.motor_control import MotorControl
import time
from logging_config import logger
from modules.sim800l.sms_processor import sms_listener
from modules.pump_control import pump_manager
from command_processor import processor_thread, processor


# sim800l = SIM800L()
config.setup_gpio()
time.sleep(5)
LedMonitor(poll_interval=1)       # led monitoring started at new thread
time.sleep(5)
log_sensors(sensors=SENSORS)
time.sleep(5)

# processor
# pump_manager

# motor_controller = MotorControl()

# def command_processor():
#     """Processes commands from the queue and applies logic."""
#     global command_queue
#     while True:
#         motor_state = motor_controller.get_motor_state()
#         if command_queue["status"]:
#             motor_state = motor_controller.get_motor_state()
#             sender_list = [ dct['sender'] for dct in command_queue["status"] ]
#             for sender in sender_list:
#                 sim800l.send_sms(phone_number=sender, message= f"Pump is {motor_state}")
#             command_queue['status'].clear()            

#         elif command_queue["off"]:
#             motor_controller.pump_off()
#             sender_list = [ dct['sender'] for dct in command_queue["off"] ]
#             for sender in sender_list:
#                 sim800l.send_sms(phone_number=sender, message= "Pump is turned off")
#             command_queue["off"].clear()
#             command_queue["on"].clear()

#         elif command_queue["on"]:
#             if motor_state == "off":
#                 duration = command_queue["on"][0]["duration"]
#                 motor_controller.start_pump_thread(duration)
#                 sender = command_queue["on"][0]["sender"]
#                 sim800l.send_sms(phone_number=sender, message= "Pump is turned On")


if __name__ == "__main__":
    print("Starting system...")

    # Start threads
    t1 = threading.Thread(target=sms_listener, daemon=True)
    t2 = threading.Thread(target=processor_thread, daemon= True)

    t1.start()
    t2.start()

    # time.sleep(1)

    # time.sleep(1)
    # processor.add_command(30)

    # # Simulate power
    # pump_manager.set_power(True)
    # time.sleep(10)  # Run for 10 sec
    # pump_manager.set_power(False)  # Power loss, should pause and rewrite
    # time.sleep(10)
    # pump_manager.set_power(True)  # Power back, continue
    # processor.add_command(10)
    # processor.add_command(15)
    # time.sleep(10) 
    # Keep main thread alive
    while True:
        time.sleep(1)
