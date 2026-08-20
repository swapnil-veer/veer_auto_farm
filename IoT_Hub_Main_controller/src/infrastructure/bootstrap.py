from app import db

from infrastructure.gpio_seed import (
    seed_gpio_config,
    seed_pumps_from_gpio,
)


def bootstrap_database(app):

    with app.app_context():

        db.create_all()

        seed_gpio_config(app)

        seed_pumps_from_gpio(app)