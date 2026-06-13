import pytest
from datetime import datetime, timedelta


# Assuming these exist in your project
# Adjust imports as per your structure
# from services.command_engine import CommandEngine
# from domain.command import Command, CommandStatus


# ---------------------------
# Helper Fake Command (if required)
# ---------------------------
class Command:
    def __init__(self, duration=10, status="WAITING"):
        self.duration = duration
        self.status = status
        self.start_time = None

    def start(self):
        self.status = "RUNNING"
        self.start_time = datetime.now()

    def complete(self):
        self.status = "COMPLETED"


# ---------------------------
# Fake Power Service
# ---------------------------
class FakePowerService:
    def __init__(self, available=True):
        self.available = available

    def is_power_available(self):
        return self.available


# ---------------------------
# Fake DB
# ---------------------------
class FakeDB:
    def __init__(self):
        self.commands = []

    def add_command(self, cmd):
        self.commands.append(cmd)

    def get_next_command(self):
        return self.commands[0] if self.commands else None

    def update_command(self, cmd):
        pass  # no-op for fake


# ---------------------------
# Fake Pump
# ---------------------------
class FakePump:
    def __init__(self):
        self.is_on = False
        self.on_calls = 0
        self.off_calls = 0

    def turn_on(self):
        self.is_on = True
        self.on_calls += 1

    def turn_off(self):
        self.is_on = False
        self.off_calls += 1


# ---------------------------
# Fake Command Engine
# Replace with real import later
# ---------------------------
class CommandEngine:
    def __init__(self, pump, db, power_service):
        self.pump = pump
        self.db = db
        self.power_service = power_service

    def process_next(self):
        cmd = self.db.get_next_command()

        if not cmd:
            return

        # WAITING → RUNNING
        if cmd.status == "WAITING":
            if not self.power_service.is_power_available():
                cmd.status = "WAITING_FOR_POWER"
                return

            self.pump.turn_on()
            cmd.start()

        # RUNNING → COMPLETED
        elif cmd.status == "RUNNING":
            now = datetime.now()
            if now - cmd.start_time >= timedelta(seconds=cmd.duration):
                self.pump.turn_off()
                cmd.complete()


# ===========================
# ✅ TEST CASES
# ===========================


def test_execute_command_success():
    """Command should start when power is available"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService(available=True)

    cmd = Command(duration=5)
    db.add_command(cmd)

    engine = CommandEngine(pump, db, power)

    engine.process_next()

    assert pump.is_on is True
    assert cmd.status == "RUNNING"
    assert cmd.start_time is not None


def test_command_waits_for_power():
    """Command should not start if power is unavailable"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService(available=False)

    cmd = Command()
    db.add_command(cmd)

    engine = CommandEngine(pump, db, power)

    engine.process_next()

    assert pump.is_on is False
    assert cmd.status == "WAITING_FOR_POWER"


def test_running_command_completes():
    """Running command should complete after duration"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService(available=True)

    cmd = Command(duration=1, status="RUNNING")
    cmd.start_time = datetime.now() - timedelta(seconds=2)

    db.add_command(cmd)

    engine = CommandEngine(pump, db, power)

    engine.process_next()

    assert pump.is_on is False
    assert cmd.status == "COMPLETED"
    assert pump.off_calls == 1


def test_no_command_does_nothing():
    """Engine should safely handle empty DB"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService()

    engine = CommandEngine(pump, db, power)

    engine.process_next()

    assert pump.is_on is False


def test_command_not_restarted_if_running():
    """Running command should not re-trigger pump ON"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService()

    cmd = Command(status="RUNNING")
    cmd.start_time = datetime.now()

    db.add_command(cmd)

    engine = CommandEngine(pump, db, power)

    engine.process_next()

    assert pump.on_calls == 0


def test_command_only_starts_once():
    """Pump should not be turned ON multiple times"""

    pump = FakePump()
    db = FakeDB()
    power = FakePowerService()

    cmd = Command()
    db.add_command(cmd)

    engine = CommandEngine(pump, db, power)

    engine.process_next()
    engine.process_next()  # second loop

    assert pump.on_calls == 1
