from database.models.modules import ModuleType


class ModuleConfigurationService:

    def __init__(
        self,
        configuration_repo,
    ):
        self.repo = configuration_repo

    # --------------------------------------------------
    # Module API
    # --------------------------------------------------

    def list_modules(self):
        return self.repo.get_all_modules(
            include_settings=True
        )

    def get_module(self, module_type):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.get_module(
            module_type,
            include_settings=True,
        )

    def configure_module(
        self,
        module_type,
        is_installed,
        is_enabled,
    ):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.update_module(
            module_type=module_type,
            is_installed=is_installed,
            is_enabled=is_enabled,
        )

    def is_enabled(self, module_type):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.is_module_enabled(
            module_type
        )

    # --------------------------------------------------
    # Setting API
    # --------------------------------------------------

    def get_settings(self, module_type):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.get_module_settings(
            module_type
        )

    def get_value(
        self,
        module_type,
        setting_key,
        fallback=None,
    ):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.get_setting_value(
            module_type=module_type,
            setting_key=setting_key,
            fallback=fallback,
        )

    def update_setting(
        self,
        module_type,
        setting_key,
        value,
    ):
        module_type = self._normalize_module_type(
            module_type
        )

        updated = self.repo.update_setting(
            module_type=module_type,
            setting_key=setting_key,
            config_value=value,
        )

        if not updated:
            raise ValueError(
                f"Unknown setting: "
                f"{module_type}.{setting_key}"
            )

        return updated

    # --------------------------------------------------
    # Restore defaults
    # --------------------------------------------------

    def restore_module_defaults(
        self,
        module_type,
    ):
        module_type = self._normalize_module_type(
            module_type
        )

        return self.repo.restore_module_defaults(
            module_type
        )

    def restore_all_defaults(self):
        return self.repo.restore_all_defaults()

    # --------------------------------------------------
    # Normalization
    # --------------------------------------------------

    def _normalize_module_type(self, module_type):
        if isinstance(module_type, ModuleType):
            return module_type.value

        return str(module_type).strip().upper()