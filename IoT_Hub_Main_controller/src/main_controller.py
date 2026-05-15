#main_controller.py
import re
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

    def __init__(self, command_repo, command_engine, power_service,sms_handler, notifier,):
        self.command_repo = command_repo
        self.command_engine = command_engine
        self.power_service = power_service
        self.sms_handler = sms_handler
        self.notifier = notifier
        self.logger = logger

    # ------------------------------------------------------------------
    # Incoming SMS / API entry point
    # ------------------------------------------------------------------

    def handle_incoming_sms(
        self,
        sender: str,
        text: str,
        sms_log_id: int | None = None,
        user_id: int | None = None,
        ) -> str | None:
        """
        Parse incoming SMS text and trigger system intent.
        Returns optional reply text.
        """

        text = text.strip()

        # ALL OFF
        if re.search(r"\bALL\s*OFF\b", text, re.IGNORECASE):
            self._create_system_command(
            CommandType.DELETE_ALL,
            sender,
            sms_log_id,
            user_id,
            )
            return None

        # OFF / STOP
        if re.search(r"\b(OFF|STOP|SHUT\s*DOWN)\b", text, re.IGNORECASE):
            self.command_engine.request_manual_stop()
            self._create_system_command(
            CommandType.DELETE_ONE,
            sender,
            sms_log_id,
            user_id,
            )
            return None

        # STATUS
        if re.search(r"\bSTATUS\b", text, re.IGNORECASE):
            return self._build_status_response()

        # AUTO
        if re.search(r"\bAUTO\b", text, re.IGNORECASE):
            self._create_system_command(
            CommandType.AUTO_ON,
            sender,
            sms_log_id,
            user_id,
            )
            return None

        # MANUAL ON
        if re.search(r"\b(ON|START)\b", text, re.IGNORECASE):
            minutes = self._extract_minutes(text) or DEFAULT_DURATION
            self._create_system_command(
            CommandType.MANUAL_ON,
            sender,
            sms_log_id,
            user_id,
            duration_minutes=minutes,
            )
            return None

        return self._invalid_command_message()

    # ------------------------------------------------------------------
    # Command creation helpers (NO execution here)
    # ------------------------------------------------------------------

    def _create_system_command(
        self,
        ctype: CommandType,
        sender: str,
        sms_log_id: int | None,
        user_id: int | None,
        duration_minutes: int | None = None,
        ):
        self.command_repo.create(
            ctype=ctype,
            sender_phone=sender,
            sms_id=sms_log_id,
            user_id=user_id,
            status=CommandStatus.QUEUED
            if ctype in (CommandType.MANUAL_ON, CommandType.AUTO_ON)
            else CommandStatus.COMPLETED,
            duration_sec=duration_minutes * 60 if duration_minutes else None,
            remaining_sec=duration_minutes * 60 if duration_minutes else None,
        )

    # ------------------------------------------------------------------
    # Status / Messaging
    # ------------------------------------------------------------------

    def _build_status_response(self) -> str:
        """
        Build SMS-friendly system status text.
        """
        power_on = self.power_service.is_power_available()
        signal = self.sms_handler.get_signal_strength()
        sim_ok = self.sms_handler.get_sim_status()

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
