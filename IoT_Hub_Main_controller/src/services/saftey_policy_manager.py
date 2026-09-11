from datetime import datetime, timedelta

from database.models.command import (
    CommandStatus,
)
from database.models.saftey_lock import SafetyLockType

from logging_config import logger



class SafetyPolicyManager:

    DEFAULT_RETRY_HOURS = 0.1
    MAX_RETRIES = 2

    def __init__(
        self,
        safety_lock_repo,
        event_emitter,
    ):
        self.safety_lock_repo = safety_lock_repo
        self.event_emitter = event_emitter

        self.logger = logger
        self.logger.info("SafetyPolicyManager initialized")


    def handle_dry_run(self):
        print('in handle dry run')
        retry_at = (datetime.utcnow() + timedelta(hours=self.DEFAULT_RETRY_HOURS))

        lock = self.safety_lock_repo.create_dry_run_lock(
                    valid_until=retry_at,
                    reason="Dry run detected",
                )
        
        self.event_emitter.emit("DRY_RUN_DETECTED")

        self.logger.debug(f"Dry run lock created: {lock}")

        if lock.retry_count <= SafetyPolicyManager.MAX_RETRIES:
            return

        end_of_day = datetime.utcnow().replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=0
        )

        lock.valid_until = end_of_day
        self.safety_lock_repo.save(lock)
        self.logger.info(f"Dry run lock extended until end of day: {end_of_day}")

    def handle_lock_expired(
        self,
        lock,
    ):

        self.safety_lock_repo.release(
            lock.id
        )
        self.logger.debug(f"Lock released: {lock.id}")

        self.event_emitter.emit(
            "DRY_RUN_RETRY_STARTED",
            {
                "retry_count": lock.retry_count,
            },
        )

    def handle_power_lost(self):

        lock = self.safety_lock_repo.get_active_lock()

        if (lock and lock.lock_type == SafetyLockType.POWER.value):
            return

        lock =  self.safety_lock_repo.create(
                lock_type=SafetyLockType.POWER.value,
                valid_until=None,
                retry_count=0,
                reason="Power unavailable",
            )
        self.logger.info(f"Power lock created: {lock}")

    def handle_power_restored(self):

        lock = self.safety_lock_repo.get_active_lock()

        if (not lock or lock.lock_type != SafetyLockType.POWER.value):
            return

        self.safety_lock_repo.release(lock.id)
        self.logger.info(f"Lock released: {lock.id}")

    def can_execute(self):

        self.expire_due_locks()

        return not self.safety_lock_repo.is_locked()

    def expire_due_locks(self):

        lock = self.safety_lock_repo.get_active_lock()

        if not lock:
            return

        if not lock.valid_until:
            return

        if lock.valid_until <= datetime.utcnow():

            self.safety_lock_repo.release(lock.id)
            self.logger.info(f"Expired Dry Run lock released: {lock.id}")

    def is_power_locked(self):
        lock = self.safety_lock_repo.get_active_lock()

        if (lock and lock.lock_type == SafetyLockType.POWER.value):
            return True

    def is_dry_run_locked(self):
        lock = self.safety_lock_repo.get_active_lock()

        if (lock and lock.lock_type == SafetyLockType.DRY_RUN.value):
            return True