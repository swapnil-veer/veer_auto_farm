import threading
import time
from statistics import mean


class CurrentMonitoringService:

    SAMPLE_INTERVAL_SEC = 10

    RAW_SAMPLE_COUNT = 3

    DRY_RUN_THRESHOLD_AMP = 5.0

    DRY_RUN_WINDOWS = 2

    MOTOR_STOP_THRESHOLD_AMP = 1.0

    MOTOR_STOP_DELAY_SEC = 2

    def __init__(
        self,
        sensor,
        current_repo,
        event_emitter,
    ):
        self.sensor = sensor
        self.current_repo = current_repo
        self.event_emitter = event_emitter

        self._running = False
        self._thread = None
        self._command_id = None

    # ----------------------------------
    # Lifecycle
    # ----------------------------------

    def start(
        self,
        command_id:int,
    ):

        if self._running:
            return

        self._command_id = command_id
        self._running = True

        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="Current Monitor",
        )

        self._thread.start()

    def stop(self):

        self._running = False

        if self._thread:
            self._thread.join(timeout=2)

    # ----------------------------------
    # Sampling
    # ----------------------------------

    def _take_snapshot(self):

        samples = []

        for _ in range(
            self.RAW_SAMPLE_COUNT):

            samples.append(self.sensor.read_amp())

            time.sleep(0.2)

        avg_current = mean(samples)

        self.current_repo.save(reading_amp=round(avg_current,2,))

        return avg_current

    # ----------------------------------
    # Monitor Loop
    # ----------------------------------

    def _run_loop(self):

        while self._running:

            self._take_snapshot()

            self._check_dry_run()

            time.sleep(self.SAMPLE_INTERVAL_SEC)

    # ----------------------------------
    # Dry Run Detection
    # ----------------------------------

    def _check_dry_run(self):

        snapshots = (self.current_repo.get_last_n(self.DRY_RUN_WINDOWS))

        if (len(snapshots)< self.DRY_RUN_WINDOWS):
            return

        below_threshold = all(
            snapshot.reading_amp
            <= self.DRY_RUN_THRESHOLD_AMP
            for snapshot in snapshots
        )

        if below_threshold:

            avg_current = mean([s.reading_amp for s in snapshots])

            self.event_emitter.emit(
                "DRY_RUN_DETECTED",
                {
                    "command_id": self._command_id,
                    "current_amp": round(avg_current,2,),
                },
            )

    # ----------------------------------
    # Motor Stop Verification
    # ----------------------------------

    def verify_motor_stopped(self,command_id:int):

        time.sleep(self.MOTOR_STOP_DELAY_SEC)

        samples = []

        for _ in range(self.RAW_SAMPLE_COUNT):
            samples.append(self.sensor.read_amp())
            time.sleep(0.2)

        avg_current = mean(samples)

        if (avg_current<= self.MOTOR_STOP_THRESHOLD_AMP):
            self.event_emitter.emit("MOTOR_STOP_VERIFIED",
                {
                    "command_id": command_id,
                    "current_amp": round(avg_current,2,),
                },
            )

            return True

        self.event_emitter.emit(
            "MOTOR_STOP_FAILURE",
            {
                "command_id": command_id,
                "current_amp": round(avg_current,2,),
            },
        )
        return False