from app import db

from infrastructure.gpio_seed import (
    seed_gpio_config,
    seed_pumps_from_gpio,
)

from infrastructure.module_configuration_repository import (
    ModuleConfigurationRepository,
)

from infrastructure.module_configuration_seed import (
    seed_module_configuration,
)


def bootstrap_database(app):

    with app.app_context():

        db.create_all()

        seed_gpio_config(app)

        seed_pumps_from_gpio(app)

        configuration_repo = ModuleConfigurationRepository(app)

        seed_module_configuration(configuration_repo)