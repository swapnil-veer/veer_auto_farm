# services/command_scheduler.py

import time
import threading
from logging_config import logger
from datetime import datetime

class CommandScheduler:
    """
    Event-driven scheduler:
    - Waits for events instead of constant polling
    - Wakes immediately when work is available
    - Falls back to timeout for safety
    """

    def __init__(self, engine, command_repo, saftey_lock_repo, saftey_policy_manager, poll_interval=30):
        self.engine = engine
        self.repo = command_repo
        self.saftey_lock_repo = saftey_lock_repo
        self.saftey_policy_manager = saftey_policy_manager
        self.poll_interval = poll_interval
        self.logger = logger

        self._running = False
        self._thread = None

        # ✅ Core improvement
        self._wakeup_event = threading.Event()

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(name="Command scheduler", target=self._run_loop, daemon=True)
        self._thread.start()

        self.logger.info("CommandScheduler started")

    def stop(self):
        self._running = False
        self.wakeup() # unblock wait
        if self._thread:
            self._thread.join(timeout=2)

        self.logger.info("CommandScheduler stopped")

    # --------------------------------------------------
    # External trigger
    # --------------------------------------------------

    def wakeup(self):
        """
        Called by other components when something changes:
        - new command added
        - power restored
        - manual stop triggered
        """
        self.logger.info('Scheduler wakes up')
        self._wakeup_event.set()

    # --------------------------------------------------
    # Core loop
    # --------------------------------------------------

    def _run_loop(self):
        while self._running:
            if self.saftey_lock_repo.is_locked():
                self.logger.info("Execution blocked by saftey Lock")
                self._wakeup_event.wait(timeout=self.poll_interval)
                self._wakeup_event.clear()
                continue
            try:
                cmd = (
                self.repo.get_active_command()
                or
                self.repo.get_waiting_for_water()
                or
                self.repo.get_waiting_for_power()
                or 
                self.repo.get_next_queued()
                )

                if cmd:
                    self.logger.info(f"Executing command #{cmd["id"]}")
                    self.engine.execute(cmd["id"])
                    continue # Immediately check for next command

                # ✅ No work → wait for event OR timeout
                self.logger.info("Scheduler idle — waiting for work")

                self._wakeup_event.wait(timeout=self.poll_interval)

                # Reset event for next cycle
                self._wakeup_event.clear()

            except Exception as exc:
                self.logger.exception(f"Scheduler loop error: {exc}")
                time.sleep(self.poll_interval) # Prevent tight error loop

    def _process_expired_locks(self):
        lock = self.saftey_lock_repo.get_active_lock()

        if not lock:
            return

        if lock.valid_until <= datetime.utcnow:
            self.logger.info(f"Saftey lock expired: {lock.lock_type}")
            self.saftey_policy_manager.handle_lock_expired(lock)
            self.wakeup()