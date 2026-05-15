# hardware/sim_modem.py
import gammu
from logging_config import logger

class SIMModem:
    def __init__(self):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        self.connected = False
        self.init()

    def init(self):
        try:
            self.sm.Init()
            self.connected = True
            logger.info("SIM modem connected")
        except Exception as e:
            self.connected = False
            logger.error(f"SIM init failed: {e}")

    def check_connection(self) -> bool:
        try:
            self.sm.GetSIMIMSI()
            self.connected = True
        except Exception:
            self.connected = False
        return self.connected

    def get_signal_strength(self):
        if not self.connected:
            return None
        try:
            return self.sm.GetSignalQuality()["SignalPercent"]
        except Exception:
            self.connected = False
            return None

    def read_sms(self, folder=0):
        try:
            return gammu.LinkSMS(
            self.sm.GetSMS(Folder=folder)
            )
        except Exception:
            return []

    def delete_sms(self, folder, location):
        try:
            self.sm.DeleteSMS(folder, location)
            return True
        except Exception as e:
            logger.error(f"Delete failed {folder}:{location}: {e}")
            return False

    def send_sms(self, phone, text):
        msg = {
        "Text": text,
        "SMSC": {"Location": 1},
        "Number": phone,
        }
        self.sm.SendSMS(msg)