from database.models.modules import ModuleType
from database.models.module_setting import (
    SettingValueType,
)


MODULE_DEFINITIONS = {
    ModuleType.LCD.value: {
        "is_installed": True,
        "is_enabled": True,
        "settings": [
            {
                "key": "i2c_address",
                "default": "0x27",
                "type": SettingValueType.STRING.value,
                "display_name": "I2C Address",
                "description": (
                    "I2C address of the LCD display."
                ),
            },
            {
                "key": "refresh_interval_sec",
                "default": 2,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Refresh Interval",
                "description": (
                    "LCD refresh interval in seconds."
                ),
            },
            {
                "key": "event_timeout_sec",
                "default": 15,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Event Message Timeout",
                "description": (
                    "Duration for LCD line 4 messages."
                ),
            },
        ],
    },

    ModuleType.CURRENT_MONITOR.value: {
        "is_installed": False,
        "is_enabled": False,
        "settings": [
            {
                "key": "dry_run_threshold_amp",
                "default": 5.0,
                "type": SettingValueType.FLOAT.value,
                "display_name": "Dry Run Threshold",
                "description": (
                    "Current threshold used to detect "
                    "a dry-run condition."
                ),
            },
            {
                "key": "raw_sample_count",
                "default": 3,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Raw Sample Count",
                "description": (
                    "Number of current readings used "
                    "to produce one averaged snapshot."
                ),
            },
            {
                "key": "sample_interval_sec",
                "default": 10,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Sample Interval",
                "description": (
                    "Delay between current snapshots."
                ),
            },
            {
                "key": "dry_run_window_count",
                "default": 2,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Dry Run Window Count",
                "description": (
                    "Consecutive low-current snapshots "
                    "required for dry-run detection."
                ),
            },
            {
                "key": "retry_hours",
                "default": 2,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Retry Delay",
                "description": (
                    "Hours to wait before retrying "
                    "after the first dry run."
                ),
            },
            {
                "key": "max_retries",
                "default": 1,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Maximum Retries",
                "description": (
                    "Maximum dry-run recovery attempts."
                ),
            },
            {
                "key": "motor_stop_threshold_amp",
                "default": 1.0,
                "type": SettingValueType.FLOAT.value,
                "display_name": "Motor Stop Threshold",
                "description": (
                    "Maximum current indicating that "
                    "the motor has stopped."
                ),
            },
            {
                "key": "motor_stop_delay_sec",
                "default": 2,
                "type": SettingValueType.INTEGER.value,
                "display_name": "Stop Verification Delay",
                "description": (
                    "Delay before checking whether "
                    "the motor stopped."
                ),
            },
        ],
    },
}


def seed_module_configuration(
    configuration_repo,
):
    for module_type, definition in (
        MODULE_DEFINITIONS.items()
    ):
        configuration_repo.create_module(
            module_type=module_type,
            is_installed=definition["is_installed"],
            is_enabled=definition["is_enabled"],
        )

        for setting in definition["settings"]:
            configuration_repo.create_setting(
                module_type=module_type,
                setting_key=setting["key"],
                default_value=setting["default"],
                value_type=setting["type"],
                display_name=setting["display_name"],
                description=setting["description"],
            )