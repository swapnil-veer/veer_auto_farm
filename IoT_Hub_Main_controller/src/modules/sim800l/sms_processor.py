from logging_config import logger
import threading
import time
from .sim import sms_thread, sms_queue
main_controller = None
_sms_lock = threading.Lock()  # shared lock

def set_controller(controller):
    global main_controller
    main_controller = controller


def msg_parser(queue=sms_queue):
    while True:
        with _sms_lock:
            if not queue:
                break
            sms = queue.pop(0)

        sender = sms["Number"]
        text = sms["Text"].strip()

        if main_controller is None:
            logger.error("MainController not set in sms_processor")
            continue

        try:
            reply = main_controller.handle_incoming_sms(sender, text)
        except Exception as e:
            logger.exception("Error in handle_incoming_sms")
            reply = "Internal error. Please try again later."

        if reply:
            sms_thread.send_sms(number=sender, text=reply)
            
def sms_processor():
    while True:
        msg_parser(sms_queue)
        time.sleep(1)



