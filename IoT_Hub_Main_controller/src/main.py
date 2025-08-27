import config
import threading
from modules.phase_monitor import phase_status, PhaseMonitor
from IoT_Hub_Main_controller.src.modules.lcd_display.lcd_module import LCD
from modules.sim800l.sim800l_gsm_module import SIM800L
from modules.motor_control import MotorControl, DEFAULT_DURATION 
import time
import  re
from logging_config import logger

config.setup_gpio()


sim800l = SIM800L()
motor_controller = MotorControl()

# Queue for incoming SMS commands
command_queue = {
                "off": [],
                "on": [],
                "status": []
}

sample_msg = """
    Please send msg in correct format.
    Accepts messages like:
      - 'PUMP ON 120', 'ON 120', 'START 120'
      - 'PUMP ON' (uses default)
      - 'OFF', 'STOP'
      - 'STATUS'
      """

def msg_parser(dct):
    """
    Accepts messages like:
      - 'PUMP ON 120', 'ON 120', 'START 120'
      - 'PUMP ON' (uses default)
      - 'OFF', 'STOP'
      - 'STATUS'
    Returns a tuple: ('ON', seconds) | ('OFF', None) | ('STATUS', None) | (None, None)
    """
    # {index: "", sender : "", message = "'"}

    msg_body = dct['msg'].strip().upper()

    # OFF
    if re.search(r'\b(OFF|STOP|SHUT\s*DOWN)\b', msg_body):
        command_queue['off'].append({"sender" : dct['sender']})

    # STATUS
    elif re.search(r'\bSTATUS\b', msg_body):
        command_queue['status'].append({"sender" : dct['sender']})

    # ON with optional duration
    elif re.search(r'\b(ON|START)\b', msg_body):
        m = re.search(r'(\d+)', msg_body)
        if m:
            min = int(m.group(1))
        else:
            min = DEFAULT_DURATION
            command_queue['on'].append({"sender" : dct['sender'], "duration" : min})
    else:
        sim800l.send_msg(phone_no = dct['sender'], message = sample_msg)
        logger.error(f"Incorrect msg from sender {dct['sender']} : {dct['msg']}")
        return None
    
def sms_listener():
    """Continuously checks for new SMS and puts commands into the queue."""
    while True:
        for msg in sim800l.check_new_sms():  # it will return list of msgs from authorized sources
            msg_parser(msg)    #if msg in well format then que generate unless send sms to sender to resend msg

        time.sleep(5)  # Poll every 5 sec



# Flags
# override_mode = False
# override_command = None  # Can be "ON" or "OFF"
# auto_mode = True  # Default mode is AUTO

# def command_processor():
#     """Processes commands from the queue and applies logic."""
#     global override_mode, override_command, auto_mode

#     command_queue = {
#                 "off": [],
#                 "on": [],
#                 "status": []
# }
#     while True:
#         if command_queue["off"]:
#             motor_controller.pump_off()
#             sender_list = [ dct['sender'] for dct in command_queue["off"] ]
#             for sender in sender_list:
#                 sim800l.send_sms(phone_number=sender, message= "Pump is turned off")
#         if not command_queue.empty():
#             cmd = command_queue.get()
#             cmd = cmd.upper()

#             if cmd == "AUTO":
#                 override_mode = False
#                 auto_mode = True
#                 print("[Command Processor] Switched to AUTO mode")
#             elif cmd in ["ON", "OFF"]:
#                 override_mode = True
#                 override_command = cmd
#                 print(f"[Command Processor] Override mode activated: {cmd}")
#         time.sleep(1)

# def motor_controller():
#     """Controls the motor based on mode (AUTO or OVERRIDE)."""
#     while True:
#         if override_mode:
#             # Apply override command
#             if override_command == "ON" and not is_motor_running():
#                 print("[Motor Controller] Override: Turning ON motor")
#                 start_motor()
#             elif override_command == "OFF" and is_motor_running():
#                 print("[Motor Controller] Override: Turning OFF motor")
#                 stop_motor()
#         else:
#             if auto_mode:
#                 # Here add your logic for sensor-based control in AUTO mode
#                 print("[Motor Controller] AUTO mode active (waiting for sensor logic)")
#         time.sleep(2)

if __name__ == "__main__":
    print("Starting system...")

    # Start threads
    t1 = threading.Thread(target=sms_listener, daemon=True)
    t2 = threading.Thread(target=command_processor, daemon=True)
    # t3 = threading.Thread(target=motor_controller, daemon=True)

    t1.start()
    t2.start()
    # t3.start()

    # Keep main thread alive
    while True:
        time.sleep(1)

# {
#   "OFF":[{"sender": "+91XXXX"}],
#   "ON": [{"duration": 120, "sender": "+91XXXX"}],
#   "STATUS" : [{"sender": "+91XXXX"}]
# }
