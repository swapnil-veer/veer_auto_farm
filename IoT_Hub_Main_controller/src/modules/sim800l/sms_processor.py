from logging_config import logger
from settings import DEFAULT_DURATION
import threading
import time
import re
from .sim import sms_thread, sms_queue
from command_processor import processor
from pump_control import pump_manager
from phase_monitor import phase_data
from lcd_display.lcd_module import get_system_status


sample_msg = """
    Please send msg in correct format.
    Accepts messages like:
      - 'PUMP ON 120', 'ON 120', 'START 120'
      - 'PUMP ON' (uses default)
      - 'OFF', 'STOP'
      - 'STATUS'
      """
def status(status):
    line1 =  status['power']
    if status['pump_on']:
        line2 = f"PUMP:ON Rem:{status['pump_rem']}min"
    elif status["power"] == "OFF" and status['pump_rem'] != False:
        line2 = f"PUMP:OFF WAIT PWR"
    else:
        line2 = f"PUMP:OFF"
    return line1, line2

def msg_parser(queue = sms_queue):

    """
    Accepts messages like:
    - 'PUMP ON 120', 'ON 120', 'START 120'
    - 'PUMP ON' (uses default)
    - 'OFF', 'STOP'
    - 'STATUS'
    Returns a tuple: ('ON', seconds) | ('OFF', None) | ('STATUS', None) | (None, None)
    """
    # {index: "", sender : "", message = "'"}
    while len(queue) > 0:
        with threading.Lock():
            sms = queue.pop(0)
        sender = sms["Number"]
        text = sms["Text"].strip()

        # OFF
        if re.search(r'\b(OFF|STOP|SHUT\s*DOWN)\b', text, flags=re.IGNORECASE):
            # command_queue['off'].append({"sender" : dct['sender']})
            processor.delete_one()
            
        elif re.search(r'\b(ALL OFF)', text, flags=re.IGNORECASE):
            processor.delete_all()

        # STATUS
        elif re.search(r'\bSTATUS\b', text, flags=re.IGNORECASE):
            # command_queue['status'].append({"sender" : dct['sender']})
            text = status()
            for i in text:
                text_body = i + "\n"
            sms_thread.send_sms(number = sender, text = text_body)

        # ON with optional duration
        elif re.search(r'\b(ON|START)\b', text, flags=re.IGNORECASE):
            m = re.search(r'(\d+)', text)
            if m:
                min = int(m.group(1))
            else:
                min = DEFAULT_DURATION
                # command_queue['on'].append({"sender" : dct['sender'], "duration" : min})
            processor.add_command(min, sender = sender)
        else:
            sms_thread.send_sms(number = sender, text = sample_msg)
            logger.error(f"Incorrect msg from sender {sender} : {text}")
            
def sms_processor():
    while True:
        msg_parser(sms_queue)
        time.sleep(1)


  # Poll interval


