# services/command_events.py

import time
from logging_config import logger

class CommandEventEmitter:

    def __init__(self):
        self._handlers = []
        self.logger = logger

    def register(self, handler):
        self._handlers.append(handler)

    def emit(self, event_type: str, data: dict | None = None):

        event = {
        "type": event_type,
        "timestamp": time.time(),
        "data": data or {},
        }

        for handler in self._handlers:
            try:
                handler(event)
            except Exception as exc:
                self.logger.exception(f"Event handler failed: {exc}")