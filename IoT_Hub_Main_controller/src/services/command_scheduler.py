# services/command_scheduler.py

import time
import threading
from logging_config import logger

class CommandScheduler:
    """
    Event-driven scheduler:
    - Waits for events instead of constant polling
    - Wakes immediately when work is available
    - Falls back to timeout for safety
    """

    def __init__(self, engine, command_repo, poll_interval=5):
        self.engine = engine
        self.repo = command_repo
        self.poll_interval = poll_interval

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
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

        logger.info("CommandScheduler started")

    def stop(self):
        self._running = False
        self.wakeup() # unblock wait
        if self._thread:
            self._thread.join(timeout=2)

        logger.info("CommandScheduler stopped")

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
        self._wakeup_event.set()

    # --------------------------------------------------
    # Core loop
    # --------------------------------------------------

    def _run_loop(self):
        while self._running:
            try:
                cmd = (
                self.repo.get_active_command()
                or
                self.repo.get_waiting_for_power()
                or 
                self.repo.get_next_queued()
                )

                if cmd:
                    logger.info(f"Executing command #{cmd["id"]}")
                    self.engine.execute(cmd["id"])
                    continue # Immediately check for next command

                # ✅ No work → wait for event OR timeout
                logger.debug("Scheduler idle — waiting for work")

                self._wakeup_event.wait(timeout=self.poll_interval)

                # Reset event for next cycle
                self._wakeup_event.clear()

            except Exception as exc:
                logger.exception(f"Scheduler loop error: {exc}")
                time.sleep(1) # Prevent tight error loop