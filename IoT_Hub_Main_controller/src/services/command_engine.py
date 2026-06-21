# services/command_engine.py

import time
from datetime import datetime
from enum import Enum, auto

from logging_config import logger
from database.models.command import CommandStatus, CommandType
from services.pump_context import PumpContextManager

class CommandEngine:

    UPDATE_INTERVAL = 5 # seconds (DB write throttle)

    def __init__(self, pump_service, power_service, command_repo, event_emitter):
        # self.pump_ctx = pump_context_manager
        self.pump_service = pump_service
        self.power = power_service
        self.command_repo = command_repo
        self.event_emitter = event_emitter
        self.manual_stop = False
        self.logger = logger

    def _create_command(
        self,
        ctype: CommandType,
        sender: str,
        sms_id: int | None,
        user_id: int | None,
        duration_minutes: int | None = None,
        ):
        self.command_repo.create(
            ctype=ctype,
            sender_phone=sender,
            sms_id=sms_id,
            user_id=user_id,
            priority = 1,
            status=CommandStatus.QUEUED
            # status = CommandStatus.CREATED
            if ctype in (CommandType.MANUAL_ON, CommandType.AUTO_ON)
            else CommandStatus.COMPLETED,
            duration_sec=duration_minutes * 60 if duration_minutes else None,
            remaining_sec=duration_minutes * 60 if duration_minutes else None,
        )

    # --------------------------------------------------
    # Public control
    # --------------------------------------------------

    def request_manual_stop(self):
        self.manual_stop = True

        # --------------------------------------------------
        # Main entry point
        # --------------------------------------------------

    def execute(self, cmd_id: int):

        cmd = self.command_repo.get(cmd_id)
        if not cmd:
            return

        try:
            self._mark_running(cmd)

            with PumpContextManager(self.pump_service, command_id = cmd_id):
            # with self.pump_ctx(command_id = cmd_id):
                result = self._run_loop(cmd)

            self._handle_result(cmd, result)

        except Exception as exc:
            self.logger.exception(f"Command {cmd_id} failed: {exc}")
            self._handle_result(cmd, ExecutionResult.ERROR, error=str(exc))

        finally:
            self.manual_stop = False

    # --------------------------------------------------
    # Core loop (PURE execution logic)
    # --------------------------------------------------

    def _run_loop(self, cmd):

        # remaining = cmd.remaining_sec or 0
        # last_trick = time.time()
        base_duration = cmd.duration_sec or 0
        start_time = time.time()
        last_persist = 0

        while True:
            state = self._get_execution_state(cmd, start_time, base_duration)

            if state == ExecutionState.STOP_MANUAL:
                return ExecutionResult.STOPPED_MANUAL

            if state == ExecutionState.POWER_LOSS:
                return ExecutionResult.POWER_LOSS

            if state == ExecutionState.COMPLETED:
                return ExecutionResult.COMPLETED

            # Update DB periodically (throttled)
            now = time.time()
            if now - last_persist >= self.UPDATE_INTERVAL:
                elapsed = self._get_elapsed(start_time, base_duration)
                self.command_repo.update(cmd.id, duration_sec=round(elapsed, 2))
                last_persist = now

            time.sleep(1)

    # --------------------------------------------------
    # State evaluation
    # --------------------------------------------------

    def _get_execution_state(self, cmd, start_time, base_duration):

        if self.manual_stop:
            return ExecutionState.STOP_MANUAL

        if not self.power.is_power_available():
            return ExecutionState.POWER_LOSS

        # AUTO mode runs forever
        if cmd.ctype != CommandType.AUTO_ON and cmd.remaining_sec:
            elapsed = self._get_elapsed(start_time, base_duration)
            if elapsed >= cmd.remaining_sec:
                return ExecutionState.COMPLETED

        return ExecutionState.RUNNING

    # --------------------------------------------------
    # Time helpers
    # --------------------------------------------------

    def _get_elapsed(self, start_time, base_duration):
        elapsed = base_duration + (
            time.time() - start_time
        )
        return elapsed
        # return time.time() - start_time

    def _get_remaining(self, cmd, start_time):
        if not cmd.remaining_sec:
            return None

        elapsed = self._get_elapsed(start_time)
        return max(0, cmd.remaining_sec - elapsed)

    # --------------------------------------------------
    # State transitions (SINGLE SOURCE)
    # --------------------------------------------------

    def _handle_result(self, cmd, result, error=None):

        now = datetime.utcnow()

        if result == ExecutionResult.COMPLETED:
            elapsed = self._get_elapsed(time.time() - (cmd.duration_sec or 0))

            self.command_repo.update(
            cmd.id,
            status=CommandStatus.COMPLETED,
            completed_at=now,
            duration_sec=round(elapsed, 2),
            )

            self.event_emitter.emit("PUMP_COMPLETED", {
            "command_id": cmd.id,
            "sender": cmd.sender_phone,
            "total_runtime_min": round(elapsed / 60),
            })

        elif result == ExecutionResult.STOP_MANUAL:
            self.command_repo.update(
            cmd.id,
            status=CommandStatus.TERMINATED,
            )

            event_type = (
            "PUMP_AUTO_STOPPED"
            if cmd.ctype == CommandType.AUTO_ON
            else "PUMP_ABORTED_MANUAL_STOP"
            )

            self.event_emitter.emit(event_type, {
            "command_id": cmd.id,
            "sender": cmd.sender_phone,
            "ctype": cmd.ctype.value,
            })

        elif result == ExecutionResult.POWER_LOSS:
            self.command_repo.update(
            cmd.id,
            status=CommandStatus.ABORTED,
            )

            remaining = self._get_remaining(cmd, time.time())

            self.event_emitter.emit("PUMP_ABORTED_POWER_LOSS", {
            "command_id": cmd.id,
            "remaining_min": round(remaining / 60) if remaining else 0,
            "sender": cmd.sender_phone,
            })

        elif result == ExecutionResult.ERROR:
            self.command_repo.update(
            cmd.id,
            status=CommandStatus.ABORTED,
            completed_at=now,
            )

            self.event_emitter.emit("PUMP_ERROR", {
            "command_id": cmd.id,
            "error": error[:100] if error else "Unknown error",
            "sender": cmd.sender_phone,
            })

    # --------------------------------------------------
    # Transition to RUNNING
    # --------------------------------------------------

    def _mark_running(self, cmd):

        self.command_repo.update(
            cmd.id,
            status=CommandStatus.RUNNING,
            start_time=datetime.utcnow(),
            )

        mode = "auto" if cmd.ctype == CommandType.AUTO_ON else "manual"

        self.event_emitter.emit("PUMP_STARTED", {
            "command_id": cmd.id,
            "sender": cmd.sender_phone,
            "mode": mode,
            "duration_min": cmd.remaining_sec // 60 if cmd.remaining_sec else None,
            })


class ExecutionState(Enum):
    RUNNING = auto()
    COMPLETED = auto()
    STOP_MANUAL = auto()
    POWER_LOSS = auto()

class ExecutionResult(Enum):
    COMPLETED = auto()
    STOP_MANUAL = auto()
    POWER_LOSS = auto()
    ERROR = auto()