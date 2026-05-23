# services/lcd_service.py
# import time
# import threading
# from settings import get_ip_address, get_cpu_temp

# class LCDService:
#     def __init__(self, lcd_driver, main_controller, logger, poll_interval=1):
#         self.lcd = lcd_driver
#         self.main_controller = main_controller
#         self.logger = logger
#         self.poll_interval = poll_interval

#         self.startup_time = time.time()
#         self.last_lines = ["", "", "", ""]
#         self.last_signal_bars = None

#         self.temp_line3_message = None
#         self.temp_line3_expiry = 0
#         self.temp_lock = threading.Lock()

#         self._stop_event = threading.Event()

#         # Boot screen
#         self.lcd.clear()
#         self.lcd.write_line(0, "VEER AUTO-FARM".center(20))
#         time.sleep(2)
#         self.lcd.clear()

#         self.refresh(force=True)

#         self._thread = threading.Thread(
#         target=self._display_loop, daemon=True
#         )
#         self._thread.start()

#         self.logger.info("LCD service started")

#         # ---------- Signal logic ----------

#     def _signal_patterns(self):
#         return [
#         ([0]*8, [0]*8),
#         ([0,0,0,0,0,0,0b11100,0b11100], [0]*8),
#         ([0,0,0,0,0b00111,0b00111,0b11111,0b11111], [0]*8),
#         ([0,0,0,0,0b00111,0b00111,0b11111,0b11111],
#         [0,0,0b11100,0b11100,0b11100,0b11100,0b11100,0b11100]),
#         ([0,0,0,0,0b00111,0b00111,0b11111,0b11111],
#         [0b00111,0b00111,0b11111,0b11111,0b11111,0b11111,0b11111,0b11111]),
#         ]

#     def _update_signal_chars(self, strength):
#         bars = max(0, min(4, round(strength / 20)))
#         if bars == self.last_signal_bars:
#             return

#         pat = self._signal_patterns()[bars]
#         self.lcd.create_char(1, pat[0])
#         self.lcd.create_char(2, pat[1])
#         self.last_signal_bars = bars

#     def _signal_text(self, status):
#         if not status.get("sim_ok"):
#             return "NO SIM ".ljust(7)

#         self._update_signal_chars(status.get("signal_strength", 0))
#         return (chr(0) + chr(1) + chr(2)).ljust(7)

#         # ---------- Line builders ----------

#     def _build_line1(self, status):
#         return f"{self._signal_text(status)}PWR:{'ON' if status.get('power') else 'OFF'}"

#     def _build_line2(self, ctx):
#         if ctx["state"] == "running":
#             if ctx["pump_on"] and ctx["manual_remaining_min"] is not None:
#                 return f"PUMP:ON Rem:{ctx['manual_remaining_min']}m"
#             if ctx["pump_on"]:
#                 return "PUMP:ON IN AUTO"
#             return "PUMP:RUNNING"
#         if ctx["state"] == "waiting_for_power":
#             return "PUMP:OFF WAIT PWR"
#         if ctx["state"] == "queued":
#             return "PUMP:OFF CMD QUEUED"
#         return "PUMP:OFF"

#     def _build_line4(self, ctx):
#         if ctx["waiting_cmd"]:
#             return f"WAIT CMD #{ctx['waiting_cmd'].get('id')}"
#         if ctx["queued_cmds"]:
#             cmd = ctx["queued_cmds"][0]
#             extra = len(ctx["queued_cmds"]) - 1
#             return f"NEXT #{cmd.get('id')}" if extra <= 0 else f"NEXT #{cmd.get('id')} +{extra}"
#         return time.strftime("%d-%m %I:%M %p")

#     def _line3_text(self):
#         with self.temp_lock:
#             if self.temp_line3_message and time.time() < self.temp_line3_expiry:
#                 return self.temp_line3_message
#         self.temp_line3_message = None

#         if time.time() - self.startup_time < 20:
#             return f"IP: {get_ip_address()}".ljust(20)
#         return f"CPU: {get_cpu_temp()}".ljust(20)

#         # ---------- Context ----------

#     def _context(self, status):
#         active = status.get("active_command")
#         queued = status.get("queued_commands") or []
#         waiting = status.get("waiting_for_power_command")

#         manual_min = None
#         if active and active.get("mode") == "manual":
#             rem = max(0, active.get("remaining_sec", 0) - active.get("duration_sec", 0))
#             manual_min = round(rem / 60)

#         return {
#         "pump_on": status.get("pump_on"),
#         "state": "running" if active else
#         "waiting_for_power" if waiting else
#         "queued" if queued else "idle",
#         "manual_remaining_min": manual_min,
#         "waiting_cmd": waiting,
#         "queued_cmds": queued,
#         }

#         # ---------- Refresh ----------

#     def refresh(self, force=False):
#         status = self.main_controller.get_system_status()
#         ctx = self._context(status)

#         lines = [
#         self._build_line1(status),
#         self._build_line2(ctx),
#         self._line3_text(),
#         self._build_line4(ctx),
#         ]

#         for i in range(4):
#             if force or lines[i] != self.last_lines[i]:
#                 self.lcd.write_line(i, lines[i])

#         self.last_lines = lines

#         # ---------- Thread ----------

#     def _display_loop(self):
#         while not self._stop_event.is_set():
#             try:
#                 self.refresh()
#             except Exception:
#                 self.logger.exception("LCD refresh failed")
#             self._stop_event.wait(self.poll_interval)

#     def close(self):
#         self._stop_event.set()
#         self.lcd.clear()

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
        time.sleep(2)
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

        if cmd.ctype == "AUTO_ON":
            return "PUMP: AUTO RUN".ljust(20)

        # manual
        elapsed = time.time() - cmd.start_time.timestamp()
        remaining = max(0, (cmd.remaining_sec or 0) - elapsed)

        mins = int(remaining // 60)
        secs = int(remaining % 60)

        return f"ON {mins:02}:{secs:02}".ljust(20)

    def _build_line3(self):
        cmd = self._get_next_command()

        if not cmd:
            return ""
            # return "Queue: Empty".ljust(20)

        minutes = (cmd.remaining_sec or 0) // 60
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


