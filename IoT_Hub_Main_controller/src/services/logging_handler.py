from logging_config import logger

class EventLoggingHandler:
    def handle(self, event: dict):
        logger.info(
            "system_event",
            extra={
            "event": event["type"],
            "command_id": event["command_id"],
            "timestamp": event["timestamp"],
            **event["data"]
            }
            )

