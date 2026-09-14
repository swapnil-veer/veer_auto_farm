from datetime import datetime

from app import db
from database.models.modules import Module
from database.models.module_setting import (
    ModuleSetting,
    SettingValueType,
)


class ModuleConfigurationRepository:

    def __init__(self, app):
        self.app = app

    # --------------------------------------------------
    # Modules
    # --------------------------------------------------

    def create_module(
        self,
        module_type,
        is_installed=False,
        is_enabled=False,
    ):
        with self.app.app_context():

            existing = Module.query.filter_by(
                module_type=module_type,
            ).first()

            if existing:
                return existing._to_dict(
                    include_settings=True
                )

            module = Module(
                module_type=module_type,
                is_installed=is_installed,
                is_enabled=is_enabled,
            )

            db.session.add(module)
            db.session.commit()

            return module._to_dict(
                include_settings=True
            )

    def get_module(
        self,
        module_type,
        include_settings=True,
    ):
        with self.app.app_context():

            module = Module.query.filter_by(
                module_type=module_type,
            ).first()

            if not module:
                return None

            return module._to_dict(
                include_settings=include_settings
            )

    def get_all_modules(
        self,
        include_settings=True,
    ):
        with self.app.app_context():

            modules = (
                Module.query
                .order_by(Module.module_type)
                .all()
            )

            return [
                module._to_dict(
                    include_settings=include_settings
                )
                for module in modules
            ]

    def update_module(
        self,
        module_type,
        is_installed=None,
        is_enabled=None,
    ):
        with self.app.app_context():

            module = Module.query.filter_by(
                module_type=module_type,
            ).first()

            if not module:
                return None

            if is_installed is not None:
                module.is_installed = bool(
                    is_installed
                )

                if not module.is_installed:
                    module.is_enabled = False

            if is_enabled is not None:
                if is_enabled and not module.is_installed:
                    raise ValueError(
                        "A module cannot be enabled "
                        "when it is not installed."
                    )

                module.is_enabled = bool(
                    is_enabled
                )

            module.configured_at = datetime.utcnow()

            db.session.commit()

            return module._to_dict(
                include_settings=True
            )

    def is_module_enabled(self, module_type):
        with self.app.app_context():

            module = Module.query.filter_by(
                module_type=module_type,
            ).first()

            return bool(
                module
                and module.is_installed
                and module.is_enabled
            )

    # --------------------------------------------------
    # Settings
    # --------------------------------------------------

    def create_setting(
        self,
        module_type,
        setting_key,
        default_value,
        value_type=SettingValueType.STRING.value,
        display_name=None,
        description=None,
    ):
        with self.app.app_context():

            module = Module.query.filter_by(
                module_type=module_type,
            ).first()

            if not module:
                raise ValueError(
                    f"Module not found: {module_type}"
                )

            existing = ModuleSetting.query.filter_by(
                module_id=module.id,
                setting_key=setting_key,
            ).first()

            if existing:
                return existing._to_dict()

            value_as_text = self._serialize_value(
                default_value,
                value_type,
            )

            setting = ModuleSetting(
                module_id=module.id,
                setting_key=setting_key,
                config_value=value_as_text,
                default_value=value_as_text,
                value_type=value_type,
                display_name=display_name,
                description=description,
            )

            db.session.add(setting)
            db.session.commit()

            return setting._to_dict()

    def get_setting(
        self,
        module_type,
        setting_key,
    ):
        with self.app.app_context():

            setting = (
                ModuleSetting.query
                .join(Module)
                .filter(
                    Module.module_type == module_type,
                    ModuleSetting.setting_key == setting_key,
                )
                .first()
            )

            if not setting:
                return None

            return setting._to_dict()

    def get_setting_value(
        self,
        module_type,
        setting_key,
        fallback=None,
    ):
        setting = self.get_setting(
            module_type,
            setting_key,
        )

        if not setting:
            return fallback

        return setting["config_value"]

    def get_module_settings(self, module_type):
        with self.app.app_context():

            settings = (
                ModuleSetting.query
                .join(Module)
                .filter(
                    Module.module_type == module_type
                )
                .order_by(
                    ModuleSetting.setting_key
                )
                .all()
            )

            return [
                setting._to_dict()
                for setting in settings
            ]

    def update_setting(
        self,
        module_type,
        setting_key,
        config_value,
    ):
        with self.app.app_context():

            setting = (
                ModuleSetting.query
                .join(Module)
                .filter(
                    Module.module_type == module_type,
                    ModuleSetting.setting_key == setting_key,
                )
                .first()
            )

            if not setting:
                return None

            setting.config_value = (
                self._serialize_value(
                    config_value,
                    setting.value_type,
                )
            )

            db.session.commit()

            return setting._to_dict()

    # --------------------------------------------------
    # Restore defaults
    # --------------------------------------------------

    def restore_module_defaults(
        self,
        module_type,
    ):
        with self.app.app_context():

            settings = (
                ModuleSetting.query
                .join(Module)
                .filter(
                    Module.module_type == module_type
                )
                .all()
            )

            for setting in settings:
                setting.restore_default()

            db.session.commit()

            return [
                setting._to_dict()
                for setting in settings
            ]

    def restore_all_defaults(self):
        with self.app.app_context():

            settings = ModuleSetting.query.all()

            for setting in settings:
                setting.restore_default()

            db.session.commit()

            return len(settings)

    # --------------------------------------------------
    # Internal conversion
    # --------------------------------------------------

    def _serialize_value(
        self,
        value,
        value_type,
    ):
        if value_type == SettingValueType.BOOLEAN.value:
            return "true" if bool(value) else "false"

        if value_type == SettingValueType.INTEGER.value:
            return str(int(value))

        if value_type == SettingValueType.FLOAT.value:
            return str(float(value))

        return str(value)