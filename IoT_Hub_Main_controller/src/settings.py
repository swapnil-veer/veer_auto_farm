from pathlib import Path
# from modules.phase_monitor import phase_data
import socket


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEFAULT_DURATION = 0

# Folder where CSV files will be stored
CSV_LOG_DIR = BASE_DIR/"data/"


class Config:
    # Pump business logic
    DEFAULT_DURATION_MIN = 30
    MAX_QUEUE_LENGTH = 10
    
    # Features
    MAINTENANCE_MODE = False
    AUTO_MODE_ENABLED = True
    
    # SMS
    SMS_CHANNEL = 'sim800l'
    
    # Logging
    LOG_LEVEL = 'INFO'


def get_ip_address():
    """Get local IP for current hostname."""
    try:
        # Connect to an external host (Google DNS) to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip[:18]
    except:
        return "IP ERROR"

def get_cpu_temp():
    """Get Raspberry Pi CPU temp in Celsius."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_c = int(f.read().strip()) / 1000
        return f"{temp_c:.0f}C"
    except:
        return "N/A"