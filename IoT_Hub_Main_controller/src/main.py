# main.py

import time
from logging_config import logger
from app import create_app, db

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
    logger.info("System started successfully")

    # from database.models import User
    # user = User (phone = "+917038835527", name = "Swapnil", email = "veerswapnil00@gmail.com", is_owner = True, is_superuser = True)
    # with app.app_context():
    #     db.session.add(user)
    #     db.session.commit()

    try:
        while True:
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        # cleanup_gpio()

if __name__ == "__main__":
    main()
