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
            # TODO 1: Fetch AUTHORIZED + unprocessed SMS (oldest first)
            # authorized_sms = SmsLog.query.filter_by(
            #     status=SmsStatus.AUTHORIZED,
            #     is_processed=False
            # ).order_by(SmsLog.created_at.asc()).limit(5).all()
            
            # for sms_log in authorized_sms:
            #     sender = sms_log.phone
            #     text = sms_log.message
            #     
            #     logger.info(f"Processing SMS {sms_log.id}: {text}")
            #     
            #     # TODO 2: MainController process
            #     if main_controller:
            #         reply = main_controller.handle_incoming_sms(sender, text)
            #         
            #         # TODO 3: Mark PROCESSED
            #         sms_log.status = SmsStatus.PROCESSED
            #         sms_log.processed_at = datetime.utcnow()
            #         db.session.commit()
            #         
            #         if reply:
            #             sms_thread.send_sms(sender, reply)
            #             
            #             # TODO 4: Log OUTGOING SMS
            #             # outgoing = SmsLog(
            #             #     direction=SmsDirection.OUTGOING,
            #             #     phone=sender,
            #             #     message=reply,
            #             #     status=SmsStatus.SENT,
            #             #     related_sms_id=sms_log.id,
            #             #     user_id=sms_log.user_id
            #             # )
            #             # db.session.add(outgoing)
            #             # db.session.commit()
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



