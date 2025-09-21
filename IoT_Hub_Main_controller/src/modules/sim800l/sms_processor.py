import time
import  re
from logging_config import logger
from .sim800l_gsm_module import SIM800L
from settings import DEFAULT_DURATION
from command_processor import processor


sim800l = SIM800L()

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
            # command_queue['on'].append({"sender" : dct['sender'], "duration" : min})
        processor.add_command(min)
    else:
        sim800l.send_msg(phone_no = dct['sender'], message = sample_msg)
        logger.error(f"Incorrect msg from sender {dct['sender']} : {dct['msg']}")
        return None
    
def sms_listener():
    """Continuously checks for new SMS and puts commands into the queue."""
    while True:
        for msg in sim800l.check_new_sms():  # it will return list of msgs from authorized sources
            msg_parser(msg)    #if msg in well format then que generate unless send sms to sender to resend msg

        time.sleep(2)  # Poll every 5 sec
