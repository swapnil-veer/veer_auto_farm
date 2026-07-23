from datetime import datetime, timedelta

from database.models.command import (
    CommandStatus,
)
from database.models.saftey_lock import SafetyLockType



class SafetyPolicyManager:

    DEFAULT_RETRY_HOURS = 2
    MAX_RETRIES = 1

    def __init__(
        self,
        command_repo,
        safety_lock_repo,
        event_emitter,
    ):
        self.command_repo = command_repo
        self.safety_lock_repo = safety_lock_repo
        self.event_emitter = event_emitter

    def handle_dry_run(
        self,
        command_id:int,
    ):

        retry_at = (
            datetime.utcnow()
            + timedelta(
                hours=self.DEFAULT_RETRY_HOURS
            )
        )

        self.command_repo.update(
            command_id,
            status=(
                CommandStatus.WAITING_FOR_WATER
            )
        )

        self.safety_lock_repo.create(
            lock_type=(
                SafetyLockType.DRY_RUN.value
            ),
            valid_until=retry_at,
            retry_count=0,
            reason="Dry run detected",
        )

        self.event_emitter.emit(
            "DRY_RUN_WAIT_STARTED",
            {
                "command_id": command_id,
                "retry_at": retry_at,
            },
        )

    def handle_lock_expired(
        self,
        lock,
    ):

        self.safety_lock_repo.release(
            lock.id
        )

        self.event_emitter.emit(
            "DRY_RUN_RETRY_STARTED",
            {
                "retry_count": lock.retry_count,
            },
        )