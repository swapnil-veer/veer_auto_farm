import os
from app import db
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
import threading


sms_queue = []


class FarmSMSHandler:
    ALLOWED_NOS = {
        "admin": ph_no_1,
        "secondary": ph_no_2
    }

    def __init__(self,poll_interval = 5, app = None):
        # Init GSM with retries
        # self.sm = gammu.StateMachine()
        # self.sm.ReadConfig()
        self.connected = False
        self.signal = 0
        self._lock = threading.Lock()
        self.poll_interval = poll_interval
        self.logger = logger
        self.logger.info("SMS background thread started")
        self._init_sm()  # Initial
        self._thread = threading.Thread(target=self._sms_loop, daemon=True)
        self._thread.start()
        self.app = app


    def _init_sm(self):
        self.sm = gammu.StateMachine()
        self.sm.ReadConfig()
        try:
            self.sm.Init()
            self._update_status(True)
            self.logger.info(f"Sim Connected")

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
            self.logger.info("SIM connected")
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
            self.logger.error(f"Signal error: {e}")
            self._update_status(False)
            return None  

    def get_signal_strength(self):
        return self.signal
        
    def _sms_loop(self):
        while True:
            self.check_inbox()
            time.sleep(self.poll_interval)  # Poll interval

    def check_inbox(self):
        if not self._ensure_sim_connected():
            return None
        self.signal = self._signal_strength()
        sms_list = self._read_sms_folder(0)
        for sms_batch in sms_list:
            try:
                sms = sms_batch[0]
                phone, text, folder, location = self._process_single_sms(sms)
                sms_log_id = self._log_incoming_sms(phone, text)
                self._authorize_sms_log(sms_log_id)
                self._delete_sms(folder, location)
                
            except Exception as e:
                self.logger.error(f"SMS processing failed: {e}") 

# Core Helpers
    def _ensure_sim_connected(self) -> bool:
        """Check connection + re-init if needed."""
        self._check_connection()
        if not self.connected:
            self._init_sm()
        return self.connected
    
    def _is_authorized_user(self, phone: str) -> bool:
        with self.app.app_context():
            user = User.query.filter_by(phone=phone, is_active=True).first()
        if user:
            user_id = user.id
            self.logger.info(f"User {user_id} authorized.")
            return True

    def _get_user(self, phone: str) -> int | None:
        """Get active user by phone."""
        with self.app.app_context():
            user = User.query.filter_by(phone=phone, is_active=True).first()
            return user.id
        
    def _read_sms_folder(self, folder: int = 0) -> list[dict]:
        """Read entire SMS folder + LinkSMS multi-part."""
        if not self.connected:
            return []
        
        sms = []
        try:
            status = self.sm.GetSMSStatus()
            remain = status["SIMUsed"] + status["PhoneUsed"] + status["TemplatesUsed"]
            start = True
            
            while remain > 0:
                if start:
                    cursms = self.sm.GetNextSMS(Start=True, Folder=folder)
                    start = False
                else:
                    cursms = self.sm.GetNextSMS(Location=cursms[0]["Location"], Folder=folder)
                remain -= len(cursms)
                sms.append(cursms)
            
            return gammu.LinkSMS(sms)
        except Exception:
            return []

    def _process_single_sms(self, sms: dict) -> tuple[str, str, int, int]:
        """Extract phone/text/folder/location from single SMS."""
        m = sms 
        return (
            m["Number"], 
            m["Text"].strip(), 
            m["Folder"], 
            m["Location"]
        )

    def _log_incoming_sms(self, phone: str, text: str) -> int:
        """Create RECEIVED SmsLog entry."""
        self.logger.info(f"sender: {phone}, msg: {text}")
        with self.app.app_context():
            sms_log = SmsLog(
                direction=SmsDirection.INCOMING,
                phone=phone,
                message=text,
                status=SmsStatus.RECEIVED
            )
            db.session.add(sms_log)
            db.session.commit()
            return sms_log.id

    def _authorize_sms_log(self, sms_log_id: int) -> None:
        """Set AUTHORIZED/UNAUTHORIZED status on SmsLog."""
        with self.app.app_context():
            sms_log = SmsLog.query.get(sms_log_id)
            if self._is_authorized_user(sms_log.phone):
                user_id = self._get_user(sms_log.phone)
                sms_log.user_id = user_id
                sms_log.status = SmsStatus.AUTHORIZED
                sms_log.is_authorized = True
            else:
                sms_log.status = SmsStatus.UNAUTHORIZED
            db.session.commit()

    def _delete_sms(self, folder: int, location: int) -> bool:
        """Safely delete single SMS."""
        try:
            self.sm.DeleteSMS(folder, location)
            return True
        except Exception as e:
            self.logger.error(f"Delete failed {folder}:{location}: {e}")
            return False

# ---------------------------------------------------------------
#   for sending
    def _log_sms_sent(self, phone: str, text: str, related_sms_id: int = None, user_id: int = None) -> SmsLog:
        """Create SENT SmsLog entry."""
        with self.app.app_context():
            if self._is_authorized_user(phone):
                user_id = self._get_user(phone)
            sms_log = SmsLog(
                direction=SmsDirection.OUTGOING,
                phone=phone,
                message=text,
                status=SmsStatus.SENT,
                related_sms_id=related_sms_id,
                user_id=user_id
            )
            db.session.add(sms_log)
            db.session.commit()
            return sms_log

    def _send_sms_worker(self, phone: str, text: str, related_sms_id: int = None, user_id: int = None) -> None:
        """Thread-safe SendSMS + logging."""
        message = {
            "Text": text,
            "SMSC": {"Location": 1, "Number": "+919822078000"},
            "Number": phone,
        }
        
        try:
            self.sm.SendSMS(message)
            self._log_sms_sent(phone, text, related_sms_id, user_id)
            self.logger.info(f"SMS sent to {phone}: {text}")
        except gammu.ERR_TIMEOUT:
            self.connected = False
            self._log_sms_failed(phone, text, "Timeout - SIM disconnected", related_sms_id, user_id)
        except Exception as e:
            self.logger.error(f"SMS failed to {phone}: {e}")
            self._log_sms_failed(phone, text, str(e), related_sms_id, user_id)

    def _log_sms_failed(self, phone: str, text: str, error: str, related_sms_id: int = None, user_id: int = None) -> SmsLog:
        """Create FAILED SmsLog entry."""
        with self.app.app_context():
            sms_log = SmsLog(
                direction=SmsDirection.OUTGOING,
                phone=phone,
                message=text,
                status=SmsStatus.FAILED,
                error=error,
                related_sms_id=related_sms_id,
                user_id=user_id
            )
            db.session.add(sms_log)
            db.session.commit()
            return sms_log


    def send_sms(self, phone: str, text: str, related_sms_id: int = None, user_id: int = None):
        """Send SMS asynchronously."""
        thread = threading.Thread(
            target=self._send_sms_worker, 
            args=(phone, text, related_sms_id, user_id),
            daemon=True
        )
        thread.start()
