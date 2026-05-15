# services/pump_context.py
class PumpContextManager:
    def __init__(self, pump_service, command_id=None):
        self.pump_service = pump_service
        self.command_id = command_id
        self.run_id = None

    def set_cmd_id(self, command_id):
        self.command_id = command_id

    def __enter__(self):
        self.run_id = self.pump_service.start(self.command_id)
        return self.run_id

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pump_service.stop(self.run_id)
        return False # re-raise exceptions