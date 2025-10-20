from pathlib import Path
from modules.phase_monitor import phase_data

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
