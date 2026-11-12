from dataclasses import dataclass


@dataclass
class AppConfig:
    """Configuration snapshot loaded once during application startup."""

    lcd_enabled: bool = False
    current_monitor_enabled: bool = False

    lcd_i2c_address: int = 0x27
    lcd_refresh_interval_sec: int = 2
    lcd_event_timeout_sec: int = 15

    dry_run_threshold_amp: float = 5.0
    raw_sample_count: int = 3
    sample_interval_sec: int = 10
    dry_run_window_count: int = 2
    retry_hours: float = 2.0
    max_retries: int = 1
    motor_stop_threshold_amp: float = 1.0
    motor_stop_delay_sec: int = 2


config = AppConfig()
