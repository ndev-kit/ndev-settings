from importlib.metadata import entry_points
from pathlib import Path
from types import SimpleNamespace

import yaml


class SettingsGroup(SimpleNamespace):
    pass

class Settings:
    """A class to manage settings for the nDev plugin, with nested group objects."""
    def __init__(self, settings_file: str):
        self._settings_path = settings_file
        self._loading = True
        self._load_settings()
        self._loading = False

    def register_setting(
        self,
        name: str,
        default_value,
        description: str = "",
        group: str = "Unknown",
        **metadata,
    ):
        """Register a new setting (for use by other libraries)."""
        with open(self._settings_path) as file:
            current_settings = yaml.load(file, Loader=yaml.FullLoader) or {}
        if group not in current_settings:
            current_settings[group] = {}
        setting_definition = {
            "value": default_value,
            "default": default_value,
            "description": description,
            **metadata,
        }
        if name not in current_settings[group]:
            current_settings[group][name] = setting_definition
        else:
            existing_value = current_settings[group][name].get("value", default_value)
            current_settings[group][name] = {
                **setting_definition,
                "value": existing_value,
            }
        # Set the attribute value in the nested group object
        if not hasattr(self, group):
            setattr(self, group, SettingsGroup())
        setattr(getattr(self, group), name, current_settings[group][name]["value"])
        if not self._loading:
            self._save_settings_file(current_settings)

    def reset_to_default(self, setting_name: str | None = None, group: str | None = None):
        """Reset a setting (or all settings) to their default values.
        If setting_name is None, reset all settings.

        Parameters
        ----------
        setting_name : str | None
            The name of the setting to reset, or None to reset all settings.
        """
        with open(self._settings_path) as file:
            settings_data = yaml.load(file, Loader=yaml.FullLoader) or {}

        if setting_name:
            # Reset single setting - find it in any group
            for group_name, group_settings in settings_data.items():
                if (
                    isinstance(group_settings, dict)
                    and setting_name in group_settings
                ):
                    setting_data = group_settings[setting_name]
                    if "default" in setting_data:
                        default_value = setting_data["default"]
                        if hasattr(self, group_name):
                            setattr(getattr(self, group_name), setting_name, default_value)
                        setting_data["value"] = default_value
                        self._save_settings_file(settings_data)
                        return
        else:
            # Reset all settings (optionally by group)
            for group_name, group_settings in settings_data.items():
                if group and group_name != group:
                    continue
                if isinstance(group_settings, dict):
                    for name, setting_data in group_settings.items():
                        if (
                            isinstance(setting_data, dict)
                            and "default" in setting_data
                        ):
                            default_value = setting_data["default"]
                            if hasattr(self, group_name):
                                setattr(getattr(self, group_name), name, default_value)
                            setting_data["value"] = default_value
            self._save_settings_file(settings_data)

    def _get_dynamic_choices(self, provider_key: str) -> list:
        """Get dynamic choices from entry points."""
        try:
            entries = entry_points(group=provider_key)
            return [entry.name for entry in entries]
        except (ImportError, AttributeError, ValueError):
            return []

    def _load_settings(self):
        """Load settings from the settings file and discover external settings."""
        with open(self._settings_path) as file:
            saved_settings = yaml.load(file, Loader=yaml.FullLoader) or {}
        for group_name, group_settings in saved_settings.items():
            group_obj = SettingsGroup()
            if isinstance(group_settings, dict):
                for name, setting_data in group_settings.items():
                    if (
                        isinstance(setting_data, dict)
                        and "value" in setting_data
                    ):
                        value = setting_data["value"]
                        setattr(group_obj, name, value)
            setattr(self, group_name, group_obj)
        self._settings_by_group = saved_settings
        self._load_external_settings()

    def _load_external_settings(self):
        """Load settings registered by external libraries via entry points."""
        try:
            for entry_point in entry_points(group="ndev_settings.providers"):
                try:
                    provider_func = entry_point.load()
                    provider_func(self)
                except (
                    ImportError,
                    AttributeError,
                    TypeError,
                    ValueError,
                ) as e:
                    print(f"Warning: Failed to load settings from {entry_point.name}: {e}")
        except (ImportError, AttributeError):
            pass

    def __setattr__(self, name, value):
        """Override setattr to auto-save when settings are changed."""
        super().__setattr__(name, value)
        # Only auto-save if changing a group object or a setting inside a group
        if not name.startswith("_") and hasattr(self, "_loading") and not self._loading:
            self._save_settings()

    def _save_settings(self):
        # Save the current state of all settings to the YAML file
        settings_data = {}
        for attr_name in dir(self):
            if attr_name.startswith("_") or callable(getattr(self, attr_name)):
                continue
            group_obj = getattr(self, attr_name)
            if isinstance(group_obj, SettingsGroup):
                group_dict = {}
                for setting_name in dir(group_obj):
                    if setting_name.startswith("_") or callable(getattr(group_obj, setting_name)):
                        continue
                    value = getattr(group_obj, setting_name)
                    # Try to preserve metadata if possible
                    if (
                        hasattr(self, "_settings_by_group")
                        and attr_name in self._settings_by_group
                        and setting_name in self._settings_by_group[attr_name]
                    ):
                        meta = self._settings_by_group[attr_name][setting_name].copy()
                        meta["value"] = value
                        group_dict[setting_name] = meta
                    else:
                        group_dict[setting_name] = {"value": value, "default": value, "description": f"Setting {setting_name}"}
                settings_data[attr_name] = group_dict
        self._save_settings_file(settings_data)

    def _save_settings_file(self, settings_data):
        """Helper to save settings data to file."""
        with open(self._settings_path, "w") as file:
            yaml.dump(settings_data, file, default_flow_style=False)


_settings_instance = None


def get_settings() -> Settings:
    """Get the singleton instance of the settings manager."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(
            str(Path(__file__).parent / "ndev_settings.yaml")
        )
    print(_settings_instance._settings_by_group)
    return _settings_instance
