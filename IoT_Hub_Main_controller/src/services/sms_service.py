from logging_config import logger
import threading
from datetime import datetime
from app import db
from database.models.sms_log import SmsLog, SmsStatus
import time

class SMSService:
    def __init__(self, main_controller, sms_handler, poll_interval = 5, app = None):
        self.main_controller = main_controller
        self.poll_interval = poll_interval
        self.sms_handler = sms_handler
        self.logger = logger  
        self._stop_event = threading.Event()
        self._thread = None
        self.app = app
        
    def start(self):
        """Start background SMS processing"""
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        self.logger.info("SMSService started")
    
    def stop(self):
        """Stop background processing"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
    
    def _process_loop(self):
        """Background loop: Poll → Process → Update"""
        while not self._stop_event.wait(2):  # Poll every 2s
            try:
                self._process_next_sms()
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"SMSService error: {e}")
    
    def _process_next_sms(self):
        """Process AUTHORIZED → PROCESSED (MainController handles SMS)"""
        with self.app.app_context():
            authorized_sms = SmsLog.query.filter_by(
                                status=SmsStatus.AUTHORIZED,
                                is_processed=False
                                ).order_by(SmsLog.created_at.asc()).limit(5).all()
            for sms_log in authorized_sms:
                try:
                    self.logger.info(f"Processing SMS {sms_log.id}: {sms_log.message[:50]}...")
                    
                    # MainController: Parse + Command + Send SMS + Log outgoing
                    reply = self.main_controller.handle_incoming_sms(
                        sender=sms_log.phone, 
                        text=sms_log.message, 
                        sms_log_id=sms_log.id,
                        user_id = sms_log.user_id,
                    )
                    # Mark PROCESSED (MainController handles SMS sending)
                    sms_log.status = SmsStatus.PROCESSED
                    sms_log.is_processed = True
                    sms_log.processed_at = datetime.utcnow()
                    db.session.commit()
                    if reply:
                            self.sms_handler.send_sms(sms_log.phone, reply, related_sms_id=sms_log.id, user_id=sms_log.user_id)
                    self.logger.info(f"SMS {sms_log.id} processed successfully")
                    
                except Exception as e:
                    self.logger.error(f"Failed SMS {sms_log.id}: {e}")
                    sms_log.status = SmsStatus.FAILED
                    sms_log.processed_at = datetime.utcnow()
                    db.session.commit()
