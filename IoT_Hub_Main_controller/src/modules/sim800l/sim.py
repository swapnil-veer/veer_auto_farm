import os
from database import db
from database.models.sms_log import SmsLog, SmsDirection, SmsStatus
from database.models.user import User
from datetime import datetime
from logging_config import logger
from dotenv import load_dotenv
load_dotenv()

ph_no_1 = "+917038835527"
ph_no_2 = os.getenv("ph_no_2")


import gammu
import time
from logging_config import self.logger
# from command_processor import processor
import threading


sms_queue = []


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
        self._lock = threading.Lock()

        self._init_sm()  # Initial
        self._thread = threading.Thread(target=self._sms_loop, daemon=True)
        self._thread.start()
        self.logger = logger
        self.logger.info("SMS background thread started")

    def _init_sm(self):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        try:
            self.sm.Init()
            self._update_status(True)
            self.logger.info(f"Sim Connected")

        except Exception as e:
            self.logger.error(f"Init failed: {e}")
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
            self.logger.info("SIM connected")
        else:
            self.logger.error("SIM not connected")

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
            self.logger.error(f"Signal error: {e}")
            self._update_status(False)
            return None  

    def get_signal_strength(self):
        return self.signal

    def send_sms(self, number, text):
        """Send SMS with error handling"""    
        # TODO 1: Create OUTGOING SmsLog FIRST
        # outgoing = SmsLog(
        #     direction=SmsDirection.OUTGOING,
        #     phone=number,
        #     message=text,
        #     status=SmsStatus.SENDING,
        #     related_sms_id=related_sms_id,
        #     user_id=user_id
        # )
        # db.session.add(outgoing)
        # db.session.commit()
        # outgoing_id = outgoing.id
        def _worker():
            message = {
                "Text": text,
                "SMSC": {"Location": 1},
                "Number": number,
            }
            try:
                self.sm.SendSMS(message)
                # TODO 2: Update SENT status
                # outgoing.status = SmsStatus.SENT
                # outgoing.sent_at = datetime.utcnow()
                # db.session.commit()
                # self.logger.info(f"SMS sent to {number}, log_id={outgoing_id}")
                self.logger.info(f"msg sent to {number} text : {text}")
            except gammu.ERR_TIMEOUT:
                self.connected = False
            except Exception as e:
                # TODO 3: Update FAILED status
                # outgoing.status = SmsStatus.FAILED
                # outgoing.error = str(e)
                # db.session.commit()
                # self.logger.error(f"SMS failed to {number}: {e}")
                self.logger.error(f"SMS error: {e}")
        # Launch worker thread
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()

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
                state = m["State"]
                if state != "UnRead":
                    continue
                self.logger.info(f"sender: {sender}, msg: {text}")
            # TODO 1: SmsLog INSERT (status='received')
            # sms_log = SmsLog(direction=SmsDirection.INCOMING, phone=sender, message=text, status=SmsStatus.RECEIVED)
            # db.session.add(sms_log)
            # db.session.commit()
            # sms_log_id = sms_log.id
            
            # TODO 2: User table authorization (NEW!)
            # user = User.query.filter_by(phone=sender, is_active=True).first()
            # if user:
            #     sms_log.user_id = user.id
            #     sms_log.status = SmsStatus.AUTHORIZED
            #     sms_log.is_authorized = True
            #     db.session.commit()

            # else:
            #     sms_log.status = SmsStatus.UNAUTHORIZED
            #     db.session.commit()
            #     self.logger.info(f"Unauthorized: {sender}")
            # self.sm.DeleteSMS(m["Folder"], m["Location"])
                if sender in self.ALLOWED_NOS.values():
                    with self._lock:
                        sms_queue.append(m)
                    # self._msg_parser(sender, text)
                else:
                    self.logger.info(f"Unauthorized: {sender}")
                # self.sm.DeleteSMS(Folder=0, Location=m["Location"])
                self.sm.DeleteSMS(m["Folder"], m["Location"])
        except gammu.ERR_TIMEOUT:
            self.connected = False
        except gammu.ERR_EMPTYSMSLOCATION:
            pass
        except Exception as e:
            self.logger.error(f"SMS loop error: {e}")
        time.sleep(2)  # Poll interval
        
    def _sms_loop(self):
        while True:
            self.check_inbox()

sms_thread = FarmSMSHandler()
    
# sms_thread = FarmSMSHandler
