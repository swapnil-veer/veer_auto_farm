#main_controller.py
import re
import threading
import time
from logging_config import logger
from settings import DEFAULT_DURATION
from database.models.command import CommandType, CommandStatus

class MainController:
    """
    Application coordinator:
    - Parses incoming user intents (SMS, HTTP, etc.)
    - Creates commands in DB
    - Requests execution control via CommandEngine
    - Builds human-readable responses
    - Handles domain events
    """

    def __init__(self, scheduler, command_engine, power_service, sim_service, notifier, sms_poll_interval=5):
        self.scheduler = scheduler
        self.command_engine = command_engine
        self.power_service = power_service
        self.sim_service = sim_service
        self.notifier = notifier
        self.logger = logger
        self._stop_event = threading.Event()
        self._thread = None
        self.sms_poll_interval = sms_poll_interval

    # ------------------------------------------------------------------
    # Incoming SMS / API entry point
    # ------------------------------------------------------------------

    def handle_incoming_sms(
        self,
        sender: str,
        text: str,
        sms_id: int | None = None,
        user_id: int | None = None,
        ) -> str | None:
        """
        Parse incoming SMS text and trigger system intent.
        Returns optional reply text.
        """

        text = text.strip()

        # ALL OFF
        if re.search(r"\bALL\s*OFF\b", text, re.IGNORECASE):
            self.command_engine._create_command(
            CommandType.DELETE_ALL,
            sender,
            sms_id,
            user_id,
            )
            return None

        # OFF / STOP
        if re.search(r"\b(OFF|STOP|SHUT\s*DOWN)\b", text, re.IGNORECASE):
            self.command_engine.request_manual_stop()
            self.command_engine._create_command(
            CommandType.DELETE_ONE,
            sender,
            sms_id,
            user_id,
            )
            return None

        # STATUS
        if re.search(r"\bSTATUS\b", text, re.IGNORECASE):
            return self._build_status_response()

        # AUTO
        if re.search(r"\bAUTO\b", text, re.IGNORECASE):
            self.command_engine._create_command(
            CommandType.AUTO_ON,
            sender,
            sms_id,
            user_id,
            )
            self.scheduler.wakeup()
            return None

        # MANUAL ON
        if re.search(r"\b(ON|START)\b", text, re.IGNORECASE):
            minutes = self._extract_minutes(text) or DEFAULT_DURATION
            self.command_engine._create_command(
            ctype=CommandType.MANUAL_ON,
            sender=sender,
            sms_id=sms_id,
            user_id=user_id,
            duration_minutes=minutes,
            )
            self.scheduler.wakeup()
            return None

        return self._invalid_command_message()

    # ------------------------------------------------------------------
    # Status / Messaging
    # ------------------------------------------------------------------

    def _build_status_response(self) -> str:
        """
        Build SMS-friendly system status text.
        """
        power_on = self.power_service.is_power_available()
        signal = self.sim_service.get_signal_strength()
        sim_ok = self.sim_service.get_sim_status()

        power_txt = "ON" if power_on else "OFF"
        signal_txt = f"{signal}%" if sim_ok else "NO SIM"

        return f"PWR:{power_txt}, SIG:{signal_txt}"

    def _invalid_command_message(self) -> str:
        return (
        "Invalid command.\n"
        "Examples:\n"
        "- ON 120\n"
        "- AUTO ON\n"
        "- OFF / STOP\n"
        "- ALL OFF\n"
        "- STATUS"
        )

    def _extract_minutes(self, text: str) -> int | None:
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else None

    # ------------------------------------------------------------------
    # Event handling (from CommandEventEmitter)
    # ------------------------------------------------------------------

    def handle_event(self, event: dict):
        """
        Receive and react to command lifecycle events.
        """
        etype = event.get("type")
        data = event.get("data", {})
        sender = data.get("sender")

        if not sender:
            self.logger.info(f"Event received: {etype}")
            return

        dispatch = {
        "PUMP_STARTED": self._on_pump_started,
        "PUMP_COMPLETED": self._on_pump_completed,
        "PUMP_ABORTED_POWER_LOSS": self._on_power_loss,
        "PUMP_ABORTED_MANUAL_STOP": self._on_manual_stop,
        "PUMP_AUTO_STOPPED": self._on_auto_stop,
        "PUMP_CLEARED_ALL": self._on_all_cleared,
        "COMMAND_QUEUED": self._on_command_queued,
        }

        handler = dispatch.get(etype)
        if handler:
            handler(sender, data)
        else:
            self.logger.warning(f"Unhandled event: {etype}")

    # ------------------------------------------------------------------
    # Event handlers (SMS side effects only)
    # ------------------------------------------------------------------

    def _on_pump_started(self, sender, data):
        msg = f"#{data['command_id']} Pump started ({data['mode'].upper()})"
        self.notifier.send(sender, msg)

    def _on_pump_completed(self, sender, data):
        msg = f"#{data['command_id']} Completed in {data['total_runtime_min']} min"
        self.notifier.send(sender, msg)

    def _on_power_loss(self, sender, data):
        self.notifier.send(sender, "Power lost. Waiting to resume.")

    def _on_manual_stop(self, sender, data):
        self.notifier.send(sender, "Pump stopped manually.")

    def _on_auto_stop(self, sender, data):
        self.notifier.send(sender, "AUTO mode stopped.")

    def _on_all_cleared(self, sender, data):
        msg = (
        f"Queue cleared. "
        f"{data.get('deleted_count', 0)} pending removed."
        )
        self.notifier.send(sender, msg)

    def _on_command_queued(self, sender, data):
        msg = f"Command #{data['command_id']} queued."
        self.notifier.send(sender, msg)

    # ------------------------------------------------------------------
    # SMS polling
    # ------------------------------------------------------------------
    def start_sms_polling(self):
        """Start background SMS processing"""
        self._thread = threading.Thread(name="main controller", target=self._process_loop, daemon=True)
        self._thread.start()
        self.logger.info("SMS polling started")
    
    def stop_sms_polling(self):
        """Stop background processing"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
    
    def _process_loop(self):
        """Background loop: Poll → Process → Update"""
        while not self._stop_event.wait(2):  # Poll every 2s
            try:
                self._process_next_sms()
                time.sleep(self.sms_poll_interval)
            except Exception as e:
                self.logger.error(f"SMSService error: {e}")
    
    def _process_next_sms(self):
        """Process AUTHORIZED → PROCESSED (MainController handles SMS)"""

        authorized_sms = self.sim_service.get_authorized_unprocessed()
        for sms_dict in authorized_sms:
            sender=sms_dict['sender'] 
            message=sms_dict['message']
            sms_id=sms_dict['id']
            user_id = sms_dict['user_id']
            self.logger.info(f"Processing SMS {sms_id}: {message[:50]}...")

            try:
                # MainController: Parse + Command + Send SMS + Log outgoing
                reply = self.handle_incoming_sms(
                    sender=sender, 
                    text=message, 
                    sms_id=sms_id,
                    user_id = user_id,
                )

            except Exception as e:
                self.sim_service.mark_failed(sms_id)
            
            else:
                # Mark PROCESSED (MainController handles SMS sending)
                self.sim_service.mark_processed(sms_id)

                if reply:
                    try:
                        self.sim_service.send_sms(phone=sender, message=reply, rel_sms_id=sms_id)
                    except Exception as e:
                        self.logger.exception(e)
                self.logger.info(f"SMS {sms_id} processed successfully")
                

