from logging_config import logger
import time
import threading
from RPLCD.i2c import CharLCD
from settings import get_ip_address, get_cpu_temp


class LCD:
    def __init__(self, main_controller, i2c_address=0x27, poll_interval=1):
        self.main_controller = main_controller
        self.logger = logger
        self.poll_interval = poll_interval

        self.lcd_lock = threading.Lock()
        self._stop_event = threading.Event()
        self.startup_time = time.time()

        self.last_lines = ["", "", "", ""]
        self.last_signal_bars = None

        self.temp_line3_message = None
        self.temp_line3_expiry = 0
        self.temp_lock = threading.Lock()

        self.lcd = CharLCD(
            i2c_expander="PCF8574",
            address=i2c_address,
            port=1,
            cols=20,
            rows=4,
            charmap="A02",
            auto_linebreaks=False,
            # compat_mode=True
        )

        self._load_base_custom_chars()

        with self.lcd_lock:
            self.lcd.clear()
            self._write_line(0, "VEER AUTO-FARM".center(20))
        time.sleep(2)

        with self.lcd_lock:
            self.lcd.clear()

        self.refresh(force=True)

        self._thread = threading.Thread(target=self.display_thread, daemon=True)
        self._thread.start()
        self.logger.info("LCD Display started background monitoring thread.")

    def _load_base_custom_chars(self):
        network_top = [
            0b00000,
            0b00000,
            0b00000,
            0b11111,
            0b01110,
            0b00100,
            0b00100,
            0b00100,
        ]
        with self.lcd_lock:
            self.lcd.create_char(0, network_top)

    def _signal_patterns(self):
        return [
          ([0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000],  # empty
            [0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000]),
            
            ([0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b11100,
            0b11100],
            [0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000]),

            ([0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00111,
            0b00111,
            0b11111,
            0b11111],
            [0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00000]),

        ([0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00111,
            0b00111,
            0b11111,
            0b11111,],
            [0b00000,
            0b00000,
            0b11100,
            0b11100,
            0b11100,
            0b11100,
            0b11100,
            0b11100]),

            (
            [0b00000,
            0b00000,
            0b00000,
            0b00000,
            0b00111,
            0b00111,
            0b11111,
            0b11111],
            [0b00111,
            0b00111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111,
            0b11111])
            ]


    def _update_signal_chars_if_needed(self, signal_strength):
        bars = max(0, min(4, round(signal_strength / 20)))
        if bars == self.last_signal_bars:
            return

        patterns = self._signal_patterns()
        with self.lcd_lock:
            self.lcd.create_char(1, patterns[bars][0])
            self.lcd.create_char(2, patterns[bars][1])

        self.last_signal_bars = bars

    def get_signal_symbol(self, status):
        if not status.get("sim_ok", False):
            return "NO SIM "

        signal_strength = status.get("signal_strength", 0)
        self._update_signal_chars_if_needed(signal_strength)
        return (chr(0) + chr(1) + chr(2)).ljust(7)

    def _fit(self, text):
        return str(text)[:20].ljust(20)

    def _write_line(self, row, text):
        self.lcd.cursor_pos = (row, 0)
        self.lcd.write_string(self._fit(text))

    def show_event_on_line3(self, message, duration=3):
        with self.temp_lock:
            self.temp_line3_message = self._fit(message)
            self.temp_line3_expiry = time.time() + duration

    def clear_event_line3(self):
        with self.temp_lock:
            self.temp_line3_message = None
            self.temp_line3_expiry = 0

    def _get_line3_text(self):
        with self.temp_lock:
            if self.temp_line3_message and time.time() < self.temp_line3_expiry:
                return self.temp_line3_message

            self.temp_line3_message = None
            self.temp_line3_expiry = 0

        elapsed = time.time() - self.startup_time
        if elapsed < 20:
            return self._fit(f"IP: {get_ip_address()}")
        return self._fit(f"CPU: {get_cpu_temp()}")

    def _build_lines(self):
        status = self.main_controller.get_system_status()
        ctx = self._get_display_context(status)

        line1 = self._build_line1(status)
        line2 = self._build_line2(ctx)
        line3 = self._get_line3_text()
        line4 = self._build_line4(ctx)

        return [
            self._fit(line1),
            self._fit(line2),
            self._fit(line3),
            self._fit(line4),
        ]


    def _get_display_context(self, status):
        active_cmd = status.get("active_command")
        waiting_cmd = status.get("waiting_for_power_command")
        queued_cmds = status.get("queued_commands") or []
        pump_on = status.get("pump_on", False)
        power_on = status.get("power", False)

        mode = (active_cmd or {}).get("mode")
        manual_remaining_min = None
        if active_cmd and mode == "manual":
            rem_sec = active_cmd.get("remaining_sec", 0) or 0
            dur_sec = active_cmd.get("duration_sec", 0) or 0
            remaining_sec = max(0, rem_sec - dur_sec)
            manual_remaining_min = round(remaining_sec / 60)

        if active_cmd:
            state = "running"
        elif waiting_cmd:
            state = "waiting_for_power"
        elif queued_cmds:
            state = "queued"
        else:
            state = "idle"

        return {
            "power_on": power_on,
            "pump_on": pump_on,
            "active_cmd": active_cmd,
            "waiting_cmd": waiting_cmd,
            "queued_cmds": queued_cmds,
            "mode": mode,
            "manual_remaining_min": manual_remaining_min,
            "state": state,
        }


    def _build_line1(self, status):
        signal_text = self.get_signal_symbol(status)[:7]
        power_state = "ON" if status.get("power") else "OFF"
        return f"{signal_text}PWR:{power_state}"


    def _build_line2(self, ctx):
        if ctx["state"] == "running":
            if ctx["pump_on"] and ctx["manual_remaining_min"] is not None:
                return f"PUMP:ON Rem:{ctx['manual_remaining_min']}m"
            if ctx["pump_on"]:
                return "PUMP:ON IN AUTO"
            return "PUMP:RUNNING"

        if ctx["state"] == "waiting_for_power":
            return "PUMP:OFF WAIT PWR"

        if ctx["state"] == "queued":
            return "PUMP:OFF CMD QUEUED"

        return "PUMP:OFF"


    def _build_line4(self, ctx):
        if ctx["waiting_cmd"]:
            cmd = ctx["waiting_cmd"]
            cmd_id = cmd.get("id") if isinstance(cmd, dict) else cmd.id
            return f"WAIT CMD #{cmd_id}"

        if ctx["queued_cmds"]:
            cmd = ctx["queued_cmds"][0]
            cmd_id = cmd.get("id")
            extra = len(ctx["queued_cmds"]) - 1
            return f"NEXT CMD #{cmd_id}" if extra <= 0 else f"NEXT #{cmd_id} +{extra}"

        return time.strftime("%d-%m %I:%M %p")
    
    def refresh(self, force=False):
        lines = self._build_lines()

        with self.lcd_lock:
            for row in range(4):
                if force or lines[row] != self.last_lines[row]:
                    self._write_line(row, lines[row])

        self.last_lines = lines

    def clear(self):
        with self.lcd_lock:
            self.lcd.clear()
        self.last_lines = ["", "", "", ""]

    def close(self):
        self._stop_event.set()
        time.sleep(0.1)
        with self.lcd_lock:
            self.lcd.clear()

    def display_thread(self):
        while not self._stop_event.is_set():
            try:
                self.refresh()
            except Exception as e:
                self.logger.exception(f"LCD update failed: {e}")

            self._stop_event.wait(self.poll_interval)