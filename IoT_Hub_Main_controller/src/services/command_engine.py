import time
from datetime import datetime
from enum import Enum, auto

from logging_config import logger
from database.models.command import (
    CommandStatus,
    CommandType,
)
from services.pump_context import PumpContextManager


class CommandEngine:

    UPDATE_INTERVAL = 5

    def __init__(
        self,
        pump_service,
        current_sensor,
        power_service,
        command_repo,
        event_emitter,
    ):
        self.pump_service = pump_service
        self.current_sensor = current_sensor
        self.power = power_service
        self.command_repo = command_repo
        self.event_emitter = event_emitter
        self.manual_stop = False
        self.logger = logger

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

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
            # runtime_sec=duration_minutes * 60 if duration_minutes else None,
            target_duration_sec=duration_minutes * 60 if duration_minutes else None,
        )

    def request_manual_stop(self):
        self.manual_stop = True

    def execute(self, cmd_id: int):

        cmd = self.command_repo.get(cmd_id)

        if not cmd:
            return

        try:

            self._mark_running(cmd)

            with PumpContextManager(
                self.pump_service,
                command_id=cmd_id,
            ):
                result, runtime = self._run_loop(cmd)

            self._handle_result(
                cmd,
                result,
                runtime=runtime,
            )

        except Exception as exc:

            self.logger.exception(
                f"Command {cmd_id} failed: {exc}"
            )

            self._handle_result(
                cmd,
                ExecutionResult.ERROR,
                error=str(exc),
                runtime=cmd.runtime_sec or 0,
            )

        finally:
            self.manual_stop = False

    # --------------------------------------------------
    # Runtime Helpers
    # --------------------------------------------------

    def _get_total_runtime(
        self,
        session_start,
        previous_runtime,
    ):
        return previous_runtime + (
            time.time() - session_start
        )

    # --------------------------------------------------
    # Main Loop
    # --------------------------------------------------

    def _run_loop(self, cmd):

        previous_runtime = cmd.runtime_sec or 0
        session_start = time.time()

        last_persist = 0

        while True:

            total_runtime = self._get_total_runtime(
                session_start,
                previous_runtime,
            )

            state = self._get_execution_state(
                cmd,
                total_runtime,
            )

            if state == ExecutionState.STOP_MANUAL:
                return (
                    ExecutionResult.STOP_MANUAL,
                    total_runtime,
                )

            if state == ExecutionState.POWER_LOSS:
                return (
                    ExecutionResult.POWER_LOSS,
                    total_runtime,
                )

            if state == ExecutionState.COMPLETED:

                if cmd.target_duration_sec:
                    total_runtime = min(
                        total_runtime,
                        cmd.target_duration_sec,
                    )

                return (
                    ExecutionResult.COMPLETED,
                    total_runtime,
                )

            now = time.time()

            if now - last_persist >= self.UPDATE_INTERVAL:

                self.command_repo.update(
                    cmd.id,
                    runtime_sec=round(
                        total_runtime,
                        2,
                    ),
                )

                last_persist = now

            time.sleep(1)

    # --------------------------------------------------
    # State Evaluation
    # --------------------------------------------------

    def _get_execution_state(
        self,
        cmd,
        total_runtime,
    ):

        if self.manual_stop:
            return ExecutionState.STOP_MANUAL

        if not self.power.is_power_available():
            return ExecutionState.POWER_LOSS

        if (
            cmd.ctype != CommandType.AUTO_ON
            and cmd.target_duration_sec is not None
            and total_runtime >= cmd.target_duration_sec
        ):
            return ExecutionState.COMPLETED

        return ExecutionState.RUNNING

    # --------------------------------------------------
    # Result Handling
    # --------------------------------------------------

    def _handle_result(
        self,
        cmd,
        result,
        runtime=0,
        error=None,
    ):

        now = datetime.utcnow()

        if result == ExecutionResult.COMPLETED:

            self.command_repo.update(
                cmd.id,
                status=CommandStatus.COMPLETED,
                completed_at=now,
                runtime_sec=round(runtime, 2),
            )

            self.event_emitter.emit(
                "PUMP_COMPLETED",
                {
                    "command_id": cmd.id,
                    "sender": cmd.sender_phone,
                    "total_runtime_min": round(
                        runtime / 60
                    ),
                },
            )

        elif result == ExecutionResult.STOP_MANUAL:

            self.command_repo.update(
                cmd.id,
                status=CommandStatus.TERMINATED,
                runtime_sec=round(runtime, 2),
            )

            event_type = (
                "PUMP_AUTO_STOPPED"
                if cmd.ctype == CommandType.AUTO_ON
                else "PUMP_ABORTED_MANUAL_STOP"
            )

            self.event_emitter.emit(
                event_type,
                {
                    "command_id": cmd.id,
                    "sender": cmd.sender_phone,
                    "ctype": cmd.ctype.value,
                },
            )

        elif result == ExecutionResult.POWER_LOSS:

            self.command_repo.update(
                cmd.id,
                status=CommandStatus.ABORTED,
                runtime_sec=round(runtime, 2),
            )

            remaining = 0

            if cmd.target_duration_sec:

                remaining = max(
                    0,
                    cmd.target_duration_sec - runtime,
                )

            self.event_emitter.emit(
                "PUMP_ABORTED_POWER_LOSS",
                {
                    "command_id": cmd.id,
                    "remaining_min": round(
                        remaining / 60
                    ),
                    "sender": cmd.sender_phone,
                },
            )

        elif result == ExecutionResult.ERROR:

            self.command_repo.update(
                cmd.id,
                status=CommandStatus.ABORTED,
                completed_at=now,
            )

            self.event_emitter.emit(
                "PUMP_ERROR",
                {
                    "command_id": cmd.id,
                    "error": (
                        error[:100]
                        if error
                        else "Unknown error"
                    ),
                    "sender": cmd.sender_phone,
                },
            )

    # --------------------------------------------------
    # Transition To Running
    # --------------------------------------------------

    def _mark_running(self, cmd):

        self.command_repo.update(
            cmd.id,
            status=CommandStatus.RUNNING,
            start_time=datetime.utcnow(),
        )

        mode = (
            "auto"
            if cmd.ctype == CommandType.AUTO_ON
            else "manual"
        )

        self.event_emitter.emit(
            "PUMP_STARTED",
            {
                "command_id": cmd.id,
                "sender": cmd.sender_phone,
                "mode": mode,
                "duration_min": (
                    cmd.target_duration_sec // 60
                    if cmd.target_duration_sec
                    else None
                ),
            },
        )


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