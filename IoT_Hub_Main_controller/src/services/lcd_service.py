import time
import threading

from settings import get_ip_address, get_cpu_temp


class LCDService:

    def __init__(self,lcd_driver,command_repo,sim_service,power_service,logger,poll_interval=1,):
        self.lcd = lcd_driver
        self.repo = command_repo
        self.sim_service = sim_service
        self.power = power_service
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

        # Boot screen
        self.lcd.clear()
        self.lcd.write_line(0, "VEER AUTO-FARM".center(20))
        time.sleep(10)
        self.lcd.clear()

        # Start background thread
        self._thread = threading.Thread(target=self._display_loop, daemon=True)
        self._thread.start()

        self.logger.info("LCD service started")

    # --------------------------------------------------
    # EVENT HANDLER (event-driven UI)
    # --------------------------------------------------

    def handle_event(self, event):

        event_type = event["event"]

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

    def _set_event(self, msg, duration=3):
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

    def _signal_text(self):
        if not self.sim_service.get_sim_status():
            return "NO SIM ".ljust(7)

        strength = self.sim_service.get_signal_strength()
        self._update_signal_chars(strength)

        return (chr(0) + chr(1) + chr(2)).ljust(7)

    # --------------------------------------------------
    # DATA BUILDERS
    # --------------------------------------------------

    def _get_active_command(self):
        return self.repo.get_active_command()

    def _get_next_command(self):
        return self.repo.get_next_queued()

    def _build_line1(self):
        power_ok = self.power.is_power_available()
        return f"{self._signal_text()}PWR:{'ON' if power_ok else 'OFF'}".ljust(20)

    def _build_line2(self):
        cmd = self._get_active_command()

        if not cmd:
            return "PUMP: OFF".ljust(20)

        if cmd["ctype"] == "AUTO_ON":
            return "PUMP: AUTO RUN".ljust(20)
        # elapsed = time.time() - cmd["start_time"].timestamp()

        # remaining = max(0, (cmd["remaining_sec"] or 0) - elapsed)


        remaining = (cmd["target_duration_sec"] - cmd["runtime_sec"]) or 0

        rounded = round(remaining / 5) * 5

        mins = rounded // 60
        secs = rounded % 60

        return f"ON {mins:02}:{secs:02}".ljust(20)

    def _build_line3(self):
        cmd = self._get_next_command()

        if not cmd:
            return ""
            # return "Queue: Empty".ljust(20)

        minutes = (cmd["target_duration_sec"] or 0) // 60
        return f"Next: {minutes} min".ljust(20)

    def _build_line4(self):
        # show event first
        with self.event_lock:
            if self.event_message and time.time() < self.event_expiry:
                return self.event_message.ljust(20)

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
        lines = [
            self._build_line1(),
            self._build_line2(),
            self._build_line3(),
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


