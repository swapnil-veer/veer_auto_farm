from config.app_config import AppConfig, config


def _module_enabled(modules, module_type):
    module = modules.get(module_type)
    return bool(
        module
        and module.get("is_installed")
        and module.get("is_enabled")
    )


def _module_settings(modules, module_type):
    module = modules.get(module_type, {})
    return {
        setting["setting_key"]: setting["config_value"]
        for setting in module.get("settings", [])
    }


def _setting(settings, key, default):
    return settings.get(key, default)


def _parse_i2c_address(value):
    address = int(value, 0) if isinstance(value, str) else int(value)
    if not 0x03 <= address <= 0x77:
        raise ValueError("LCD I2C address must be a valid 7-bit address")
    return address


def _validate(config):
    if config.raw_sample_count < 1:
        raise ValueError("raw_sample_count must be at least 1")
    if config.sample_interval_sec < 1:
        raise ValueError("sample_interval_sec must be at least 1")
    if config.dry_run_window_count < 1:
        raise ValueError("dry_run_window_count must be at least 1")
    if config.retry_hours <= 0:
        raise ValueError("retry_hours must be greater than 0")
    if config.max_retries < 0:
        raise ValueError("max_retries cannot be negative")
    if config.dry_run_threshold_amp < 0:
        raise ValueError("dry_run_threshold_amp cannot be negative")
    if config.motor_stop_threshold_amp < 0:
        raise ValueError("motor_stop_threshold_amp cannot be negative")
    if config.motor_stop_delay_sec < 0:
        raise ValueError("motor_stop_delay_sec cannot be negative")
    if config.lcd_refresh_interval_sec < 1:
        raise ValueError("lcd_refresh_interval_sec must be at least 1")
    if config.lcd_event_timeout_sec < 1:
        raise ValueError("lcd_event_timeout_sec must be at least 1")


def load_config(module_configuration_service):
    """Load all module settings once and retain the resulting snapshot in memory."""
    modules = {
        module["module_type"]: module
        for module in module_configuration_service.list_modules()
    }
    lcd_settings = _module_settings(modules, "LCD")
    current_settings = _module_settings(modules, "CURRENT_MONITOR")

    loaded = AppConfig(
        lcd_enabled=_module_enabled(modules, "LCD"),
        current_monitor_enabled=_module_enabled(
            modules, "CURRENT_MONITOR"
        ),
        lcd_i2c_address=_parse_i2c_address(
            _setting(lcd_settings, "i2c_address", "0x27")
        ),
        lcd_refresh_interval_sec=int(
            _setting(lcd_settings, "refresh_interval_sec", 2)
        ),
        lcd_event_timeout_sec=int(
            _setting(lcd_settings, "event_timeout_sec", 15)
        ),
        dry_run_threshold_amp=float(
            _setting(current_settings, "dry_run_threshold_amp", 5.0)
        ),
        raw_sample_count=int(
            _setting(current_settings, "raw_sample_count", 3)
        ),
        sample_interval_sec=int(
            _setting(current_settings, "sample_interval_sec", 10)
        ),
        dry_run_window_count=int(
            _setting(current_settings, "dry_run_window_count", 2)
        ),
        retry_hours=float(
            _setting(current_settings, "retry_hours", 2)
        ),
        max_retries=int(
            _setting(current_settings, "max_retries", 1)
        ),
        motor_stop_threshold_amp=float(
            _setting(current_settings, "motor_stop_threshold_amp", 1.0)
        ),
        motor_stop_delay_sec=int(
            _setting(current_settings, "motor_stop_delay_sec", 2)
        ),
    )
    _validate(loaded)

    # Keep the shared object stable for services that imported it at startup.
    config.__dict__.update(loaded.__dict__)
    return config
