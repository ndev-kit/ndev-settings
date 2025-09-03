from importlib.metadata import entry_points

import yaml


class SettingsGroup:
    """Simple container for settings in a group."""


class Settings:
    """A class to manage settings for the nDev plugin, with nested group objects."""

    def __init__(self, settings_file: str):
        self._settings_path = settings_file
        self.load()

    def reset_to_default(
        self, setting_name: str | None = None, group: str | None = None
    ):
        """Reset a setting (or all settings) to their default values."""
        # Use the merged settings data that includes external settings
        if hasattr(self, "_grouped_settings"):
            all_settings = self._grouped_settings
        else:
            # Fallback to main file if _grouped_settings not available
            with open(self._settings_path) as file:
                all_settings = yaml.load(file, Loader=yaml.FullLoader) or {}

        if setting_name:
            # Reset single setting - find it in any group
            for group_name, group_settings in all_settings.items():
                if setting_name in group_settings:
                    setting_data = group_settings[setting_name]

                    default_value = setting_data["default"]
                    setattr(
                        getattr(self, group_name), setting_name, default_value
                    )
                    # Update the in-memory settings data
                    setting_data["value"] = default_value
                    # Save changes (this will save everything including external changes)
                    self.save()
                    return
        else:
            # Reset all settings (optionally by group)
            for group_name, group_settings in all_settings.items():
                if group and group_name != group:
                    # Skip non-specified groups, unless None then continue
                    continue
                for name, setting_data in group_settings.items():
                    if "default" in setting_data:
                        default_value = setting_data["default"]
                        setattr(getattr(self, group_name), name, default_value)
                        # Update the in-memory settings data
                        setting_data["value"] = default_value
            # Save changes (this will save everything including external changes)
            self.save()

    def _get_dynamic_choices(self, provider_key: str) -> list:
        """Get dynamic choices from entry points."""
        try:
            entries = entry_points(group=provider_key)
            return [entry.name for entry in entries]
        except (ImportError, AttributeError, ValueError):
            return []

    def load(self):
        """Load settings from main file, external YAML files, and entry points."""
        # Start with main settings file
        all_settings = self._load_yaml_file(self._settings_path)

        # Load external YAML files from entry points
        external_yaml_settings = self._load_external_yaml_files()

        # Merge external YAML settings - append new groups at the end to preserve order
        # First, add settings to existing groups
        for group_name, group_settings in external_yaml_settings.items():
            if group_name in all_settings:
                # Add to existing group (main file settings take precedence)
                for setting_name, setting_data in group_settings.items():
                    if setting_name not in all_settings[group_name]:
                        all_settings[group_name][setting_name] = setting_data

        # Then, add completely new groups at the end
        for group_name, group_settings in external_yaml_settings.items():
            if group_name not in all_settings:
                all_settings[group_name] = group_settings

        # Create group objects from merged settings
        for group_name, group_settings in all_settings.items():
            group_obj = SettingsGroup()
            for name, setting_data in group_settings.items():
                if isinstance(setting_data, dict) and "value" in setting_data:
                    value = setting_data["value"]
                    setattr(group_obj, name, value)
            setattr(self, group_name, group_obj)

        self._grouped_settings = all_settings
        # Don't auto-save during load - only save when explicitly requested
        # This prevents modifying files during testing and keeps loading fast

    def _load_yaml_file(self, yaml_path: str) -> dict:
        """Load a single YAML settings file."""
        try:
            with open(yaml_path) as file:
                # Use FullLoader to support Python-specific tags like !!python/tuple
                return yaml.load(file, Loader=yaml.FullLoader) or {}
        except FileNotFoundError:
            return {}

    def _load_external_yaml_files(self) -> dict:
        """Load external YAML files from other packages via entry points."""
        all_external_settings = {}
        try:
            # Look for entry points that provide YAML file paths
            for entry_point in entry_points(group="ndev_settings.manifest"):
                try:
                    # Support napari-style resource paths (e.g., "package:file.yaml")
                    entry_value = getattr(entry_point, "value", None)
                    if not entry_value or ":" not in entry_value:
                        print(
                            f"Warning: Entry point {entry_point.name} has invalid format: {entry_value}"
                        )
                        continue

                    package_name, resource_name = entry_value.split(":", 1)

                    from importlib.resources import files

                    yaml_path = str(files(package_name) / resource_name)
                    external_settings = self._load_yaml_file(yaml_path)
                    # Merge with all external settings
                    for (
                        group_name,
                        group_settings,
                    ) in external_settings.items():
                        if group_name not in all_external_settings:
                            all_external_settings[group_name] = {}
                        all_external_settings[group_name].update(
                            group_settings
                        )
                except (
                    ImportError,
                    AttributeError,
                    TypeError,
                    ValueError,
                ) as e:
                    print(
                        f"Warning: Failed to load YAML settings from {entry_point.name}: {e}"
                    )
        except (ImportError, AttributeError):
            pass

        return all_external_settings

    def save(self):
        """Save the current state of all settings to the YAML file, preserving original order."""
        # Update the _grouped_settings values from the current group objects
        for group_name, group_settings in self._grouped_settings.items():
            if hasattr(self, group_name):
                group_obj = getattr(self, group_name)
                if isinstance(group_obj, SettingsGroup):
                    for setting_name in group_settings:
                        if hasattr(group_obj, setting_name):
                            current_value = getattr(group_obj, setting_name)
                            # Update the value in place
                            self._grouped_settings[group_name][setting_name][
                                "value"
                            ] = current_value

        # Save the updated _grouped_settings directly
        self._save_settings_file(self._grouped_settings)

    def _save_settings_file(self, settings_data):
        """Helper to save settings data to file."""
        with open(self._settings_path, "w") as file:
            yaml.dump(
                settings_data,
                file,
                default_flow_style=False,
                sort_keys=False,
            )
