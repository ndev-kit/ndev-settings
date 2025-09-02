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
        self._load_all_settings()  # Load both local and external settings
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
        # Load current settings
        with open(self._settings_path) as file:
            current_settings = yaml.load(file, Loader=yaml.FullLoader) or {}

        # Create group if it doesn't exist
        if group not in current_settings:
            current_settings[group] = {}

        setting_definition = {
            "value": default_value,
            "default": default_value,
            "description": description,
            **metadata,
        }

        # Create the new setting if it doesn't already exist
        if name not in current_settings[group]:
            current_settings[group][name] = setting_definition
        else:
            # Preserve existing setting value but update metadata
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
        """Reset a setting (or all settings) to their default values."""
        with open(self._settings_path) as file:
            settings_data = yaml.load(file, Loader=yaml.FullLoader) or {}

        if setting_name:
            # Reset single setting - find it in any group
            for group_name, group_settings in settings_data.items():
                if setting_name in group_settings:
                    setting_data = group_settings[setting_name]

                    default_value = setting_data["default"]
                    setattr(getattr(self, group_name), setting_name, default_value)
                    setting_data["value"] = default_value
                    self._save_settings_file(settings_data)
                    return
        else:
            # Reset all settings (optionally by group)
            for group_name, group_settings in settings_data.items():
                if group and group_name != group:
                    # Skip non-specified groups, unless None then continue
                    continue
                for name, setting_data in group_settings.items():
                    if "default" in setting_data:
                        default_value = setting_data["default"]
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

    def _load_all_settings(self):
        """Load settings from main file, external YAML files, and entry points."""
        # Start with main settings file
        all_settings = self._load_yaml_file(self._settings_path)

        # Load external YAML files from entry points
        external_yaml_settings = self._load_external_yaml_files()

        # Merge external YAML settings
        for group_name, group_settings in external_yaml_settings.items():
            if group_name not in all_settings:
                all_settings[group_name] = {}
            # Only add settings that don't already exist (main file takes precedence)
            for setting_name, setting_data in group_settings.items():
                if setting_name not in all_settings[group_name]:
                    all_settings[group_name][setting_name] = setting_data

        # Create group objects from merged settings
        for group_name, group_settings in all_settings.items():
            group_obj = SettingsGroup()
            for name, setting_data in group_settings.items():
                if isinstance(setting_data, dict) and "value" in setting_data:
                    value = setting_data["value"]
                    setattr(group_obj, name, value)
            setattr(self, group_name, group_obj)

        self._grouped_settings = all_settings

    def _load_yaml_file(self, yaml_path: str) -> dict:
        """Load a single YAML settings file."""
        try:
            with open(yaml_path) as file:
                return yaml.load(file, Loader=yaml.FullLoader) or {}
        except FileNotFoundError:
            return {}

    def _load_external_yaml_files(self) -> dict:
        """Load external YAML files from other packages via entry points."""
        all_external_settings = {}
        try:
            # Look for entry points that provide YAML file paths
            for entry_point in entry_points(group="ndev_settings.yaml_providers"):
                try:
                    yaml_path_func = entry_point.load()
                    yaml_path = yaml_path_func()  # Function should return path to YAML file
                    if Path(yaml_path).exists():
                        external_settings = self._load_yaml_file(yaml_path)
                        # Merge with all external settings
                        for group_name, group_settings in external_settings.items():
                            if group_name not in all_external_settings:
                                all_external_settings[group_name] = {}
                            all_external_settings[group_name].update(group_settings)
                except (ImportError, AttributeError, TypeError, ValueError) as e:
                    print(f"Warning: Failed to load YAML settings from {entry_point.name}: {e}")
        except (ImportError, AttributeError):
            pass

        return all_external_settings


    def __setattr__(self, name, value):
        """Override setattr to auto-save when settings are changed."""
        super().__setattr__(name, value)
        # Only auto-save if changing a group object or a setting inside a group
        if not name.startswith("_") and hasattr(self, "_loading") and not self._loading:
            self._save_settings()

    def _save_settings(self):
        """Save the current state of all settings to the YAML file."""
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
                        and attr_name in self._grouped_settings
                        and setting_name in self._grouped_settings[attr_name]
                    ):
                        meta = self._grouped_settings[attr_name][setting_name].copy()
                        meta["value"] = value
                        group_dict[setting_name] = meta
                    else:
                        group_dict[setting_name] = {
                            "value": value,
                            "default": value,
                            "description": f"Setting {setting_name}"
                        }
                settings_data[attr_name] = group_dict
        self._save_settings_file(settings_data)

    def _save_settings_file(self, settings_data):
        """Helper to save settings data to file."""
        with open(self._settings_path, "w") as file:
            yaml.dump(settings_data, file, default_flow_style=False)
