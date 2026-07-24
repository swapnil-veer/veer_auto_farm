
class NullCurrentMonitoringService:
    def start(self):
        pass
    
    def stop(self):
        pass

    def verify_motor_stopped(self, command_id = None):
        return None