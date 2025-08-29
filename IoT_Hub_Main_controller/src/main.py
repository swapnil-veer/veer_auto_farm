import config
import threading
from modules.phase_monitor import phase_status, PhaseMonitor
from modules.lcd_display.lcd_module import LCD
from modules.sim800l.sim800l_gsm_module import SIM800L
from modules.motor_control import MotorControl
import time
from logging_config import logger
from modules.sim800l.sim800l_gsm_module import SIM800L
from modules.sim800l.sms_processor import sms_listener, command_queue

lcd = LCD()
sim800l = SIM800L()
config.setup_gpio()

motor_controller = MotorControl()

def command_processor():
    """Processes commands from the queue and applies logic."""
    global command_queue
    while True:
        motor_state = motor_controller.get_motor_state()
        if command_queue["status"]:
            motor_state = motor_controller.get_motor_state()
            sender_list = [ dct['sender'] for dct in command_queue["status"] ]
            for sender in sender_list:
                sim800l.send_sms(phone_number=sender, message= f"Pump is {motor_state}")
            command_queue['status'].clear()            

        elif command_queue["off"]:
            motor_controller.pump_off()
            sender_list = [ dct['sender'] for dct in command_queue["off"] ]
            for sender in sender_list:
                sim800l.send_sms(phone_number=sender, message= "Pump is turned off")
            command_queue["off"].clear()
            command_queue["on"].clear()

        elif command_queue["on"]:
            if motor_state == "off":
                duration = command_queue["on"][0]["duration"]
                motor_controller.start_pump_thread(duration)
                sender = command_queue["on"][0]["sender"]
                sim800l.send_sms(phone_number=sender, message= "Pump is turned On")


if __name__ == "__main__":
    print("Starting system...")

    # Start threads
    t1 = threading.Thread(target=sms_listener, daemon=True)
    t2 = threading.Thread(target=command_processor, daemon=True)

    t1.start()
    t2.start()

    # Keep main thread alive
    while True:
        time.sleep(1)
