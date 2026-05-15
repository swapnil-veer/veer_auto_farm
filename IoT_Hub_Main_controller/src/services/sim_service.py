# services/sim_service.py
import threading
import time
from logging_config import logger
from database.models.sms_log import SmsStatus

class SIMService:
    def __init__(self, modem, repository, poll_interval=5):
        self.modem = modem
        self.repo = repository
        self.poll_interval = poll_interval
        self.signal = 0

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("SIMService started")

    def get_sim_status(self):
        return self.modem.connected

    def get_signal_strength(self):
        return self.signal

    def _loop(self):
        while True:
            self._poll_inbox()
            time.sleep(self.poll_interval)

    def _poll_inbox(self):
        if not self.modem.check_connection():
            return

        self.signal = self.modem.get_signal_strength() or 0

        for batch in self.modem.read_sms():
            sms = batch[0]
            phone = sms["Number"]
            text = sms["Text"].strip()

            log = self.repo.log_incoming(phone, text)
            user = self.repo.get_user(phone)

            if user:
                log.status = SmsStatus.AUTHORIZED
                log.user_id = user.id
                log.is_authorized = True
            else:
                log.status = SmsStatus.UNAUTHORIZED

            self.modem.delete_sms(sms["Folder"], sms["Location"])
