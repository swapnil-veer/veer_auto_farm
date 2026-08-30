from logging_config import logger

class EventLoggingHandler:
    def handle_event(self, event: dict):
        logger.info(
            event["type"],
            extra={
            "command_id": event.get("command_id"),
            "timestamp": event["timestamp"],
            **event["data"]
            }
            )

