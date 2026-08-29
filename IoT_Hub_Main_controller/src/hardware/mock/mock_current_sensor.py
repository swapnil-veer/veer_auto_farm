
class MockCurrentSensor:
    NORMAL = "normal"
    DRY_RUN = "dry_run"
    MOTOR_STOPPED = "motor_stopped"
    STOP_FAILURE = "stop_failure"

    def __init__(self):
        self.mode = self.NORMAL

    def set_mode(self, mode):
        self.mode = mode

    def get_mode(self):
        return self.mode

    def read_current(self):

        if self.mode == self.NORMAL:
            return 11.5

        if self.mode == self.DRY_RUN:
            return 2.0

        if self.mode == self.MOTOR_STOPPED:
            return 0.0

        if self.mode == self.STOP_FAILURE:
            return 4.5

        return 0.0