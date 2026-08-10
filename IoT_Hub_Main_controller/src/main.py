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
    logger.info("System started successfully")

    # from database.models import User
    # user = User (phone = "+917038835527", name = "Swapnil", email = "veerswapnil00@gmail.com", is_owner = True, is_superuser = True)
    # with app.app_context():
    #     db.session.add(user)
    #     db.session.commit()

    sms_repo = SMSRepository(app)

    def fake_sms(phone, message):
        sms_log = sms_repo.log_incoming(phone, message)
        user_id = sms_repo.get_user(phone)

        if user_id:
            logger.info(f"Fake SMS received From {phone} AUTHORIZED")
            fields = {
                "status": SmsStatus.AUTHORIZED,
                "is_authorized": True,
                "processed_at" : datetime.utcnow(),
            }

            if user_id is not None:
                fields["user_id"] = user_id

            sms_repo.update_sms(
                sms_id=sms_log["id"],
                **fields
            )
        else:
            print("Not authorized")

    i = 0
    if i == 0:
        fake_sms(phone = "+917038835527", message = "ON 2")
        i = 1


    try:
        while True:
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        # cleanup_gpio()

if __name__ == "__main__":
    import threading
    import time

    def monitor_threads():
        while True:
            print(f"\nAlive Threads: {len(threading.enumerate())}")
            for t in threading.enumerate():
                # print(f"""
                # Name      : {t.name}
                # Ident     : {t.ident}
                # Native ID : {t.native_id}
                # Daemon    : {t.daemon}
                # Alive     : {t.is_alive()}
                # Class     : {type(t).__name__}
                # Target    : {getattr(t, "_target", None)}
                # Args      : {getattr(t, "_args", None)}
                # """)
                # print("=" * 60)
                print("Thread:", t)
                # print("Type:", type(t))
                # print("Module:", type(t).__module__)
                # print("Class:", type(t).__name__)
                
            time.sleep(60)

    threading.Thread(
        target=monitor_threads,
        name="ThreadMonitor",
        daemon=True,
    ).start()
    main()
