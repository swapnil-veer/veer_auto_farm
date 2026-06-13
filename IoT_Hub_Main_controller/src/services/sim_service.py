# services/sim_service.py
import threading
import time
from datetime import datetime
from logging_config import logger
from database.models.sms_log import SmsLog, SmsStatus

class SIMService:
    def __init__(self, modem, user_repo, sms_repo, poll_interval=5):
        self.modem = modem
        self.user_repo = user_repo
        self.sms_repo = sms_repo
        self.poll_interval = poll_interval
        self.signal = 0

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("SIMService started")

    def get_sim_status(self):
        return self.modem.check_connection

    def get_signal_strength(self):
        return self.signal

    def _loop(self):
        while True:
            self.sync_incoming_sms()
            time.sleep(self.poll_interval)

# --------------------------------------------------------------------------
# FETCH INCOMING SMS(RESTORED LOGIC)
# --------------------------------------------------------------------------

    def sync_incoming_sms(self):
        """
        Read SMS > store > mark status > save authorized messages to db 
        """
        raw_messages = self.modem.read_all_sms()

        if not self.modem.check_connection():
            return

        self.signal = self.modem.get_signal_strength() or 0

        for sms_list in raw_messages:
            sms = sms_list[0]
            phone = sms["Number"]
            message = sms["Text"].strip()

            sms_log = self.sms_repo.log_incoming(phone, message)
            user_id = self.sms_repo.get_user(phone)

            if user_id:
                logger.info(f"SMS received From {phone} AUTHORIZED")
                self.mark_authorized(sms_id=sms_log["id"], user_id=user_id)
            else:
                self.mark_unauthorized(sms_id=sms_log["id"])

            self.modem.delete_sms(sms["Folder"], sms["Location"])

    def send_sms(self, phone, message, rel_sms_id=None):
        try:
            print("in send sms try 1")
            self.modem.send_sms(phone, message)
            print("in send sms try 2")
        except Exception as e:
            self.sms_repo.log_outgoing(
                phone=phone,
                message=message,
                status=SmsStatus.FAILED,
                error=str(e),
                rel_sms_id=rel_sms_id
            )
        else:
            print("in send sms else")
            try:
                user_id = self.sms_repo.get_user(phone)
                self.sms_repo.log_outgoing(
                    phone=phone, 
                    message=message, 
                    status=SmsStatus.SENT, 
                    error=None, 
                    rel_sms_id=rel_sms_id, 
                    user_id=user_id
                )
            except Exception as e:
                print(f"In side send sms {e}")


    def get_authorized_unprocessed(self, limit=5):
        " Will return list of sms dict of authorized unprocessed sms"
        return self.sms_repo.get_sms_logs(
            status=SmsStatus.AUTHORIZED, 
            is_processed=False, 
            order_by="created_at",
            limit=limit,
            )

    def mark_authorized(self, sms_id, user_id=None):
        "This will mark sms is authorized in db"
        fields = {
            "status": SmsStatus.AUTHORIZED,
            "is_authorized": True,
            "processed_at" : datetime.utcnow(),
        }

        if user_id is not None:
            fields["user_id"] = user_id

        return self.sms_repo.update_sms(
            sms_id=sms_id,
            **fields
        )

    def mark_unauthorized(self, sms_id):
        "This will mark sms is un-authorized in db"
        fields = {
            "status": SmsStatus.UNAUTHORIZED,
            "is_authorized": False,
            "processed_at" : datetime.utcnow(),
        }
        return self.sms_repo.update_sms(
            sms_id=sms_id,
            **fields
        )

    def mark_processed(self, sms_id):
        fields = {
            "status": SmsStatus.PROCESSED,
            "is_processed": True,
            "processed_at" : datetime.utcnow(),
        }

        return self.sms_repo.update_sms(
            sms_id=sms_id,
            **fields
        )

    def mark_failed(self, sms_id):
        fields = {
            "status": SmsStatus.FAILED,
            "processed_at" : datetime.utcnow(),
        }
        
        return self.sms_repo.update_sms(
            sms_id=sms_id,
            **fields
        )


    
