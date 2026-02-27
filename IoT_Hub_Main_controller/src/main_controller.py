import re
from settings import DEFAULT_DURATION
from logging_config import logger
from database.models.command import Command, CommandStatus, CommandType



class MainController:
    """
    Central brain:
    - Receives user intents (SMS, HTTP, etc.)
    - Delegates to CommandProcessor for pump control
    - Builds response messages for users
    - Reads system status (phase_monitor, CommandProcessor state)
    """

    def __init__(self, command_processor, led_monitor, sms_handler):
        self.command_processor = command_processor    # CommandProcessor instance
        self.sms_handler = sms_handler
        self.logger = logger
        self._event_handler = EventHandler(sms_handler=self.sms_handler, logger=self.logger)
        self.power_service = PowerStatusService(led_monitor)

    # === PUBLIC ENTRY POINT (for SMS layer) ===
    def handle_incoming_sms(self, sender: str, text: str, sms_log_id = None, user_id = None) -> str:
        """
        Entry point called by sms_processor.
        Parses the SMS text at a high level, decides action,
        and returns a reply string to send back to this sender.
        """
        # delete_all_commands   
        if re.search(r'\b(ALL OFF)', text, flags=re.IGNORECASE):
            # cmd = self._create_command('DELETE_ALL', sender)
            self.command_processor.handle(ctype = CommandType.DELETE_ALL, sender = sender, sms_log_id = sms_log_id, user_id=user_id)
            return None

        # delete_one_command
        elif re.search(r'\b(OFF|STOP|SHUT\s*DOWN)\b', text, flags=re.IGNORECASE):
            # cmd = self._create_command('DELETE_ONE', sender)
            self.command_processor.handle(ctype = CommandType.DELETE_ONE, sender = sender, sms_log_id = sms_log_id, user_id=user_id)
            return None

        # STATUS
        elif re.search(r'\bSTATUS\b', text, flags=re.IGNORECASE):
            return self._handle_status(sender=sender)
        
        # For auto mode
        elif re.search(r'\b(Auto|Auto on)\b', text, flags=re.IGNORECASE):
            # TODO: replace direct add_command call with brain.handle_incoming_sms
            # cmd = self._create_command('AUTO_ON', sender)
            self.command_processor.handle(ctype = CommandType.AUTO_ON, sender = sender, sms_log_id = sms_log_id, user_id=user_id)
            return None
        
        # ON with optional duration
        elif re.search(r'\b(ON|START)\b', text, flags=re.IGNORECASE):
            m = re.search(r'(\d+)', text)
            if m:
                min = int(m.group(1))
            else:
                min = DEFAULT_DURATION
            # cmd = self._create_command('MANUAL_ON', sender, min)
            try :
                self.command_processor.handle(ctype = CommandType.MANUAL_ON, duration_minutes = min, sender = sender, sms_log_id = sms_log_id, user_id=user_id)
            except ValueError as err_msg:
                return err_msg
            return None

        else:
            return self._handle_invalid(sender=sender)

        
    def get_system_status(self) -> dict:
        """
        Central status provider.
        Uses phase_data, command_processor, sms_thread, etc.
        Returns a single, stable structure for all UIs.
        """
        cmd_dict = self.command_processor.get_command(self.command_processor.cmd_id)  # or current cmd_id
        
        mode = cmd_dict.get('mode') or 'idle'
        manual_remaining_min = None
        if mode == 'manual':
            rem_sec = cmd_dict.get('remaining_sec', 0) or 0
            dur_sec = cmd_dict.get('duration_sec', 0) or 0  # Fix typo + safe
            manual_remaining_min = round((rem_sec - dur_sec) / 60) 
            # manual_remaining_min = round(cmd_dict.get('remaining_sec', 0) / 60)
            # manual_remaining_min = round((cmd_dict.get('remaining_sec') - cmd_dict.get('durstion_sec')) / 60)
        # print(f"")
        status = {
            'power': self.power_service.is_power_available(),
            'mode': mode,
            'pump_on': self.command_processor.pump_context_manager.relay_manager.get_pump_state(),  # pump_manager
            'manual_remaining_min': manual_remaining_min,
            'sim_ok': self.sms_handler.get_sim_status(),
            'signal_strength': self.sms_handler.get_signal_strength() or 0,
        }
        return status
        
    # === COMMAND HANDLERS (internal to MainController) ===

    def _handle_off(self, sender: str) -> str:
        """
        Handle OFF / STOP request:
        - tell CommandProcessor to delete current command
        - build acknowledgement message
        """
        self.command_processor.delete_one()
        return "Pump OFF request received. Stopping current command (if any)."

    def _handle_all_off(self, sender: str) -> str:
        """
        Handle ALL OFF request:
        - delete current + queued commands
        """
        self.command_processor.delete_all()
        return "All commands cleared. Pump will be OFF."

    def _handle_manual_on(self, sender: str, minutes: int) -> str:
        """
        Handle 'ON <minutes>' or default ON.
        """
        self.command_processor.add_command(duration_minutes=minutes, sender=sender)
        return f"Request accepted: Pump ON for {minutes} min."

    def _handle_auto_on(self, sender: str) -> str:
        """
        Handle AUTO mode start.
        """
        self.command_processor.add_command(sender=sender, mode="auto")
        return "Request accepted: Pump ON in AUTO mode (runs until OFF)."

    def _handle_status(self, sender: str) -> str:
        """
        Build status message using phase_data + CommandProcessor state + LCD helper.
        """
        status = self.get_system_status()
        power = status["power"]
        pump_text = "ON" if status["pump_on"] else "OFF"
        rem = status["manual_remaining_min"]
        rem_part = f"REM:{rem} min" if rem is not None else ""
        
        if status["mode"] == "auto":
            if status["pump_on"]:
                return f"PWR:{power}, PUMP:{pump_text} AUTO"
            else:
                return f"PWR:{power}, PUMP:{pump_text} AUTO WAIT PWR"
        return f"PWR:{power}, PUMP:{pump_text}{rem_part}"

    def _handle_invalid(self, sender: str) -> str:
        """
        For unrecognized commands, return help text.
        """
        sample_msg ="""Send msg in correct format as below:
 - 'PUMP ON 120', 'ON 120', 
 - 'AUTO ON' - Motor starts in Auto mode
 - 'OFF', 'STOP' - Off Auto mode / Delete Current Commands
 - 'ALL OFF' - Delete all commands.
 - 'STATUS'"""
        return sample_msg
    
    # Events
    def handle_event(self, event: dict) -> None:
        """Entry point for CommandProcessor events."""
        self._event_handler.handle(event)


class EventHandler:
    """Only event-specific logic; no orchestration."""
    def __init__(self, sms_handler, logger):
        self.sms_handler = sms_handler
        self.logger = logger

    def handle(self, event: dict) -> None:
        etype = event.get("type")
        data = event.get("data", {})

        dispatch = {
            "PUMP_STARTED": self._pump_started,
            "PUMP_COMPLETED": self._pump_completed,
            "PUMP_ABORTED_POWER_LOSS": self._on_power_loss,
            "PUMP_AUTO_STOPPED": self._on_pump_auto_stopped,
            "PUMP_ABORTED_MANUAL_STOP": self._on_pump_man_stopped,
            "COMMAND_DELETED_CURRENT": self._on_command_deleted,
            "PUMP_CLEARED_ALL": self._pump_cleared_all,
            "COMMAND_QUEUED" : self._command_queued,
        }
        handler = dispatch.get(etype)
        if handler:
            handler(data)
        else:
            self.logger.warning(f"Unknown event: {etype} {data}")

    def _pump_started(self, data: dict) -> None:
        sender = data.get("sender")
        mode = data.get("mode")
        duration_min = data.get("duration_min")
        cmd_id = data.get("command_id")
        if sender:
            if mode == "manual" and duration_min:
                text = f"#{cmd_id} Pump started for {duration_min} min."
            else:
                text = f"#{cmd_id} Pump started in AUTO mode."
            self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_STARTED: {data}")
    
    def _pump_completed(self, data: dict) -> None:
        sender = data.get("sender")
        mode = data.get("mode")
        duration_min = data.get("total_runtime_min")
        cmd_id = data.get("command_id")
        if sender:
            text = f"#{cmd_id}Pump completed, {duration_min} min total"
            self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_COMPLETED: {data}")
    
    def _on_power_loss(self, data : dict) -> None:
        sender = data.get("sender")
        mode = data.get("mode")
        duration_min = data.get("duration_min")
        if sender:
            if mode == "manual" and duration_min:
                text = f"Power loss. Waiting, {duration_min} min left"
            else:
                text = "Power loss in AUTO mode. Waiting for power to resume."
            self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_ABORTED_POWER_LOSS: {data}")

    def _on_pump_auto_stopped(self, data : dict) -> None:
        sender = data.get("sender")
        if sender:
                text = f"AUTO mode stopped by user {sender}"
                self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_AUTO_STOPPED: {data}")

    def _on_pump_man_stopped(self, data : dict) -> None:
        sender = data.get("sender")
        if sender:
                text = f"Pump manually stopped by user {sender}"
                self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_ABORTED_MANUAL_STOP: {data}")

    def _on_command_deleted(self, data: dict) -> None:
        sender = data.get("sender")
        if sender:
                text = f"This Command deleted without run by user {sender}"
                self.sms_handler.send_sms(sender, text)
        self.logger.info(f"COMMAND_DELETED_CURRENT: {data}")

    def _pump_cleared_all(self, data: dict) -> None:
        """DEL ALL - Comprehensive cleanup report"""
        sender = data.get("sender")
        deleted_count = data.get("deleted_count", 0)
        running_stopped = data.get("running_stopped", False)
        
        deleted_text = f"{deleted_count} queued/aborted" if deleted_count > 0 else "No queued"
        running_text = "🛑 STOPPED" if running_stopped else "None running"
        
        text = f"🧹 Queue cleared!\n{deleted_text} TERMINATED. Current pump: {running_text}"
        
        if sender:
            self.sms_handler.send_sms(sender, text)
        self.logger.info(f"PUMP_CLEARED_ALL: {text}")

    def _command_queued(self, data: dict) -> None:
        """Command added to queue"""
        sender = data.get("sender")
        ctype = data.get("ctype", "unknown")
        duration = data.get("duration_min")
        position = data.get("position", "?")
        if duration:
            text = f"Request accepted: #{data['command_id']} queued ({ctype}, {duration}min)"
        else:
            text = f"Request accepted: #{data['command_id']} queued ({ctype})"
        if sender:
            self.sms_handler.send_sms(sender, text)
        self.logger.info(f"COMMAND_QUEUED: {data}")


class PowerStatusService:
    def __init__(self, led_monitor):
        self.led_monitor = led_monitor
    
    def is_power_available(self) -> bool:
        return self.led_monitor.is_power_available()
    
    def get_status(self) -> str:
        return self.led_monitor.get_status()






