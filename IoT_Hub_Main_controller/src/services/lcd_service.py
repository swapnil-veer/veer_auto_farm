import time
import threading

from settings import get_ip_address, get_cpu_temp
from database.models.command import CommandType
from logging_config import logger


class LCDService:

    def __init__(self,lcd_driver, system_state, poll_interval=1,):
        self.lcd = lcd_driver
        self.system_state = system_state
        self.logger = logger
        self.poll_interval = poll_interval

        self.last_lines = ["", "", "", ""]
        self.last_signal_bars = None

        self.event_message = None
        self.event_expiry = 0
        self.event_lock = threading.Lock()

        self._stop_event = threading.Event()

        # cache system info
        self._last_sys_fetch = 0
        self._ip = ""
        self._cpu = ""

        self._running = False
        self._thread = None

        # Boot screen
        self.lcd.clear()
        self.lcd.write_line(0, "VEER AUTO-FARM".center(20))
        time.sleep(10)
        self.lcd.clear()
        self.lcd.write_line(0, "Initializing...!".center(20))
        

    def start(self):
        if self._running:
            return
        
        self._thread = threading.Thread(name="LCD service", target=self._display_loop, daemon=True)
        self._thread.start()

        self.logger.info("LCD service started")


    # --------------------------------------------------
    # EVENT HANDLER (event-driven UI)
    # --------------------------------------------------

    def handle_event(self, event):
        event_type = event["type"]

        if event_type == "PUMP_STARTED":
            self._set_event("Pump Started")

        elif event_type == "PUMP_COMPLETED":
            self._set_event("Completed ✅")

        elif event_type == "PUMP_ABORTED_POWER_LOSS":
            self._set_event("Power Lost ⚠")

        elif event_type == "PUMP_ERROR":
            self._set_event("ERROR ⚠")

        elif event_type == "SMS_RECEIVED":
            self._set_event("SMS Received")

    def _set_event(self, msg, duration=10):
        with self.event_lock:
            self.event_message = msg[:20]
            self.event_expiry = time.time() + duration

    # --------------------------------------------------
    # SIGNAL ICON LOGIC (your tower style ✅)
    # --------------------------------------------------

    def _signal_patterns(self):
        return [
            ([0]*8, [0]*8),
            ([0,0,0,0,0,0,0b11100,0b11100], [0]*8),
            ([0,0,0,0,0b00111,0b00111,0b11111,0b11111], [0]*8),
            ([0,0,0,0,0b00111,0b00111,0b11111,0b11111],
             [0,0,0b11100,0b11100,0b11100,0b11100,0b11100,0b11100]),
            ([0,0,0,0,0b00111,0b00111,0b11111,0b11111],
             [0b00111,0b00111,0b11111,0b11111,0b11111,0b11111,0b11111,0b11111]),
        ]

    def _update_signal_chars(self, strength):
        bars = max(0, min(4, round(strength / 20)))
        if bars == self.last_signal_bars:
            return

        pat = self._signal_patterns()[bars]
        self.lcd.create_char(1, pat[0])
        self.lcd.create_char(2, pat[1])
        self.last_signal_bars = bars

    def _signal_text(self, status):
        sim_status = status.get("sim_status")
        signal_strength = status.get("signal_strength")
        if not sim_status:
            return "NO SIM ".ljust(7)

        self._update_signal_chars(strength= signal_strength)

        return (chr(0) + chr(1) + chr(2)).ljust(7)

    # --------------------------------------------------
    # DATA BUILDERS
    # --------------------------------------------------

    def _get_active_command(self):
        return self.repo.get_active_command()

    def _get_next_command(self):
        return self.repo.get_next_queued()

    def _build_line1(self, state):
        power_ok = state["power_available"]
        return f"{self._signal_text(state)}PWR:{'ON' if power_ok else 'OFF'}".ljust(20)


    def _build_line2(self, state):
        cmd = state.get("active_command_id")
        mode = state.get("active_command_mode")
        runtime_sec = max(0, state.get("runtime_sec") or 0)
        target_duration_sec = max(0, state.get("target_duration_sec") or 0)

        if not cmd:
            return "PUMP: OFF".ljust(20)
        if mode == CommandType.AUTO_ON:
            return "PUMP: AUTO RUN".ljust(20)

        remaining = (target_duration_sec - runtime_sec)

        rounded = round(remaining / 5) * 5

        mins = rounded // 60
        secs = rounded % 60

        return f"ON {mins:02}:{secs:02}".ljust(20)

    def _build_line3(self, state):
        next_command_id = state.get("next_command_id")

        return f"Next: {next_command_id}".ljust(20)

    def _build_line4(self):
        # show event first
        with self.event_lock:
            if self.event_message and (time.time() < self.event_expiry):
                return self.event_message.ljust(20)
            
            # Event has expired, clear it
            self.event_message = None
            self.event_expiry = 0


        # fallback system info
        now = time.time()
        if now - self._last_sys_fetch > 10:
            self._ip = get_ip_address()
            self._cpu = get_cpu_temp()
            self._last_sys_fetch = now
        return f"CPU:{self._cpu}".ljust(20)

    # --------------------------------------------------
    # RENDER LOOP
    # --------------------------------------------------

    def _display_loop(self):
        while not self._stop_event.is_set():
            try:
                self._render()
            except Exception:
                self.logger.exception("LCD refresh failed")

            self._stop_event.wait(self.poll_interval)

    def _render(self):
        state = self.system_state.snapshot()
        lines = [
            self._build_line1(state),
            self._build_line2(state),
            self._build_line3(state),
            self._build_line4(),
        ]
        for i in range(4):
            if lines[i] != self.last_lines[i]:
                self.lcd.write_line(i, lines[i])
        self.last_lines = lines

    # --------------------------------------------------
    # CLEANUP
    # --------------------------------------------------

    def stop(self):
        self._stop_event.set()
        self.lcd.clear()


