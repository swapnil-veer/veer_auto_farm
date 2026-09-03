class MockSIMModem:
    def __init__(self):
        self.connected = True
        self._signal = 75
        self._inbox = []

    def check_connection(self):
        return True

    def get_signal_strength(self):
        return self._signal

    def read_all_sms(self):
        """
        Return fake SMS batches.
        Format matches gammu.LinkSMS output shape.
        """
        msgs = list(self._inbox)
        self._inbox.clear()
        return[[msg]for i, msg in enumerate(msgs)]
        return [[{
            "Number": "+911234567890",
            "Text": msg,
            "Folder": 0,
            "Location": i
            }] for i, msg in enumerate(msgs)]

    def delete_sms(self, folder, location):
        return True

    def send_sms(self, phone, text):
        print(f"[MOCK SMS → {phone}]: {text}")

    # helper for tests
    def inject_sms(self, phone, message):
        dct = {
            "Number": phone,
            "Text": message,
            "Folder": 0,
            "Location": 1
            }
        self._inbox.append(dct)