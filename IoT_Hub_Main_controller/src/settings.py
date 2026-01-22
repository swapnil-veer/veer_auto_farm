from pathlib import Path
from modules.phase_monitor import phase_data
import socket


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DEFAULT_DURATION = 0

# Folder where CSV files will be stored
CSV_LOG_DIR = BASE_DIR/"data/"

# Define which sensors are available and enabled
SENSORS = {
    "leds": {
        "enabled": True,
        "file": "phase_data.csv",
        "fields": phase_data.keys(),
        "data" : phase_data
    },
    "temperature": {
        "enabled": False,   # disabled for now
        "file": "temperature.csv",
        "fields": ["temperature"]
    },
    "moisture": {
        "enabled": False,   # disabled for now
        "file": "moisture.csv",
        "fields": ["soil_moisture"]
    }
}
# TEMPLATES = [
#     {
#         'BACKEND': '',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [

#             ],
#         },
#     },
# ]


#  Database for future 

# DATABASES =  {
#     'default': {
#         'ENGINE': 'django.db.backends.mysql', 
#         'NAME': 'book_library',
#         'USER': 'root',
#         'PASSWORD': 'root',
#         'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
#         'PORT': '3306',
#     }
# }

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
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return ip[:18]  # Truncate for LCD
    except:
        return "Lookup failed"

def get_cpu_temp():
    """Get Raspberry Pi CPU temp in Celsius."""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp_c = int(f.read().strip()) / 1000
        return f"{temp_c:.0f}C"
    except:
        return "N/A"