import os
import re


from dotenv import load_dotenv
load_dotenv()

ph_no_1 = "+917038835527"
ph_no_2 = os.getenv("ph_no_2")

counter = 0
i = 0

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
        # self.sm = gammu.StateMachine()
        # self.sm.ReadConfig()
        self.connected = False
        self.signal = 0

        self._init_sm()  # Initial
        self._thread = threading.Thread(target=self._sms_loop, daemon=True)
        self._thread.start()
        logger.info("SMS background thread started")

    def _init_sm(self):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        try:
            self.sm.Init()
            self._update_status(True)
            logger.info(f"Sim Connected")

        except Exception as e:
            logger.error(f"Init failed: {e}")
            self._update_status(False)


    def _check_connection(self):
        if not self.connected:
            self._init_sm()  # Recreate on disconnect
            return
        try:
            self.sm.GetSIMIMSI()  # Quick check
        except gammu.ERR_TIMEOUT:
            self._update_status(False)
        except Exception:
            self._update_status(False)

    def _update_status(self, boolean:bool):
        self.connected = boolean
        if self.connected:
            logger.info("SIM connected")
        else:
            logger.error("SIM not connected")

    def get_sim_status(self):
        return self.connected  # Fast var check; no blocking call

    def _signal_strength(self):
        """Signal strength in %"""
        if not self.connected :
            return None
        try:
            signal = self.sm.GetSignalQuality()
            return signal["SignalPercent"]
        except gammu.ERR_TIMEOUT:
            self._update_status(False)
            return None
        except Exception as e:
            logger.error(f"Signal error: {e}")
            self._update_status(False)
            return None  

    def get_signal_strength(self):
        return self.signal

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
        except gammu.ERR_TIMEOUT:
            self.connected = False
        except Exception as e:
            logger.error(f"SMS error: {e}")



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
        if re.search(r'\b(OFF|STOP|SHUT\s*DOWN)\b', msg_body, flags=re.IGNORECASE):
            # command_queue['off'].append({"sender" : dct['sender']})
            pass

        # STATUS
        elif re.search(r'\bSTATUS\b', msg_body, flags=re.IGNORECASE):
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
        self._check_connection()  # Periodic check/re-init
        if not self.connected:
            time.sleep(5)
            return None

        try:
            self.signal = self._signal_strength()
            # self.sm.Init()  # Init here if not in __init__
            status = self.sm.GetSMSStatus()
            remain = status["SIMUsed"] + status["PhoneUsed"] + status["TemplatesUsed"]
            sms = []
            start = True
            while remain > 0:
                if start:
                    cursms = self.sm.GetNextSMS(Start=True, Folder=0)
                    start = False
                else:
                    cursms = self.sm.GetNextSMS(Location=cursms[0]["Location"], Folder=0)
                remain -= len(cursms)
                sms.append(cursms)
            data = gammu.LinkSMS(sms)  # Combine multi-part
            for x in data:
                m = x[0]
                sender = m["Number"]
                text = m["Text"].strip()
                logger.info(f"sender: {sender}, msg: {text}")
                if sender in self.ALLOWED_NOS.values():
                    self._msg_parser(sender, text)
                else:
                    logger.info(f"Unauthorized: {sender}")
                self.sm.DeleteSMS(Folder=0, Location=m["Location"])
        except gammu.ERR_TIMEOUT:
            self.connected = False
        except gammu.ERR_EMPTYSMSLOCATION:
            pass
        except Exception as e:
            logger.error(f"SMS loop error: {e}")
        time.sleep(2)  # Poll interval
        
    def _sms_loop(self):
        while True:
            self.check_inbox()

sms_thread = FarmSMSHandler()
    
# sms_thread = FarmSMSHandler
