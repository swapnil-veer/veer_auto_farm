import os
import re

from dotenv import load_dotenv
load_dotenv()

ph_no_1 = "+917038835527"
ph_no_2 = os.getenv("ph_no_2")


import gammu
import time
from logging_config import logger
from settings import DEFAULT_DURATION
from command_processor import processor
import threading

sample_msg = """
    Please send msg in correct format.
    Accepts messages like:
      - 'PUMP ON 120', 'ON 120', 'START 120'
      - 'PUMP ON' (uses default)
      - 'OFF', 'STOP'
      - 'STATUS'
      """


class FarmSMSHandler:
    ALLOWED_NOS = {
        "admin": ph_no_1,
        "secondary": ph_no_2
    }

    def __init__(self):

        # Init GSM with retries
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        connected = False
        print("in sms ")

        for attempt in range(5):  # retry up to 5 times
            try:
                self.sm.Init()
                connected = True
                break
            except Exception as e:
                print(f"GSM init failed: {e}")
                time.sleep(10)  # wait before retry
            
        if not connected:
            raise RuntimeError("Unable to initialize GSM modem")
            # Start background thread
        self._thread = threading.Thread(target=self._sms_loop, daemon=True)
        self._thread.start()
        logger.info("SMS started background monitoring thread.")
        print("in sms thread")



    def update_signal_display(self):
        """signal strength """
        signal = self.sm.GetSignalQuality()
        strength = signal["SignalStrength"]  # 0–100
        return strength

    def send_sms(self, number, text):
        """Send SMS with error handling"""
        try:
            message = {
                "Text": text,
                "SMSC": {"Location": 1},
                "Number": number,
            }
            self.sm.SendSMS(message)
            logger.info(f"msg sent to {number} text : {text}")
        except Exception as e:
            logger.error(e)

    def _msg_parser(self, sender, text):
        """
        Accepts messages like:
        - 'PUMP ON 120', 'ON 120', 'START 120'
        - 'PUMP ON' (uses default)
        - 'OFF', 'STOP'
        - 'STATUS'
        Returns a tuple: ('ON', seconds) | ('OFF', None) | ('STATUS', None) | (None, None)
        """
        # {index: "", sender : "", message = "'"}

        msg_body = text

        # OFF
        if re.search(r'\b(OFF|STOP|SHUT\s*DOWN)\b', msg_body):
            # command_queue['off'].append({"sender" : dct['sender']})
            pass

        # STATUS
        elif re.search(r'\bSTATUS\b', msg_body):
            # command_queue['status'].append({"sender" : dct['sender']})
            pass
        
        # ON with optional duration
        elif re.search(r'\b(ON|START)\b', msg_body, flags=re.IGNORECASE):
            m = re.search(r'(\d+)', msg_body)
            if m:
                min = int(m.group(1))
            else:
                min = DEFAULT_DURATION
                # command_queue['on'].append({"sender" : dct['sender'], "duration" : min})
            processor.add_command(min)
        else:
            self.send_sms(number = sender, text = sample_msg)
            logger.error(f"Incorrect msg from sender {sender} : {msg_body}")
            return None

    def check_inbox(self):
        """Check inbox and process commands"""
        try:
            folders = self.sm.GetSMSFolders()
            for folder in folders:
                # print(type(folder))
                # print(folder)
                try:
                    sms_list = self.sm.GetNextSMS(Folder=folder["Inbox"], Location=0)
                    # print(sms_list)
                    # print(1)
                    while True:
                        for sms in sms_list:
                            # print(sms)
                            # print(2)
                            sender = sms["Number"]
                            text = sms["Text"].strip()
                            # print(text)
                            logger.info(f"sender : {sender}, msg : {text}")

                            if sender in self.ALLOWED_NOS.values():
                                self._msg_parser(sender, text)
                                self.sm.DeleteSMS(Folder=0, Location=sms["Location"])
                            else:
                                self.sm.DeleteSMS(Folder=0, Location=sms["Location"])
                                logger.info(f"Unauthorized sender {sender}")

                        sms_list = self.sm.GetNextSMS(Folder=folder["Inbox"],
                                                     Location=sms_list[-1]["Location"])
                except gammu.ERR_EMPTY:
                    pass
        except Exception as e:
            logger.error(f"check in box error {e}")

        
    def _sms_loop(self):
        while True:
            self.check_inbox()
            time.sleep(10)
    
# sms_thread = FarmSMSHandler
