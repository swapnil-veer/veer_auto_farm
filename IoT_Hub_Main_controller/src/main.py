# main.py

import time
from logging_config import logger
from app import create_app, db
from infrastructure.sms_repository import SMSRepository
from database.models.sms_log import SmsLog, SmsStatus
from datetime import datetime




from infrastructure.gpio_seed import (
    seed_gpio_config,
    seed_pumps_from_gpio,
    cleanup_gpio,
    )

from composition import compose_application

def main():
    app = create_app()
 # -----------------------------
 # Infrastructure bootstrap
 # -----------------------------
    with app.app_context():
        db.create_all()

    seed_gpio_config(app)
    seed_pumps_from_gpio(app)

 # -----------------------------
 # Compose + start application
 # -----------------------------
    ctx = compose_application(app)

    # app.ctx = ctx
    app.extensions["ctx"] = ctx

    
    logger.info("System started successfully")

    app.run(debug=True, host='0.0.0.0', port=5000)

    try:
        while True:
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        # cleanup_gpio()

if __name__ == "__main__":
    main()
