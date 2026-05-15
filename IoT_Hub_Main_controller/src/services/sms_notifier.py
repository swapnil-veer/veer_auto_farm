from services.notifier import Notifier

class SMSNotifier(Notifier):
    def __init__(self, sms_handler):
        self.sms_handler = sms_handler

    def send(self, recipient: str, message: str, meta: dict | None = None):
        self.sms_handler.send_sms(recipient, message)