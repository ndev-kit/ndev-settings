from pathlib import Path

import yaml


class Settings:
    """A class to manage settings for the nDev plugin."""

    def __init__(self, settings_file: str):
        """Initialize the settings manager with a file path."""
        self._settings_path = settings_file
        self._loading = True  # Flag to prevent auto-save during initialization
        self.load_settings()
        self._loading = False  # Enable auto-save after initialization

    def register_setting(
        self,
        name: str,
        default_value,
        description: str = "",
        group: str = "Other",
        **metadata,
    ):
        """Register a new setting (for use by other libraries)."""
        # Create the setting definition in the rich format with value first
        setting_definition = {
            "value": default_value,
            "default": default_value,
            "description": description,
            "group": group,
            **metadata,
        }

        # Load current settings to preserve existing values
        try:
            with open(self._settings_path) as file:
                current_settings = yaml.safe_load(file) or {}
        except FileNotFoundError:
            current_settings = {}

        # If setting doesn't exist in file, add it with default value
        if name not in current_settings:
            current_settings[name] = setting_definition
        else:
            # Setting exists, preserve the current value but update metadata
            existing_value = current_settings[name].get("value", default_value)
            current_settings[name] = {
                **setting_definition,
                "value": existing_value,
            }

        # Set the attribute value (either from file or default)
        if name in current_settings and "value" in current_settings[name]:
            value = current_settings[name]["value"]
            # Handle type conversion for tuples
            if isinstance(default_value, tuple) and isinstance(value, list):
                value = tuple(value)
            setattr(self, name, value)
        else:
            setattr(
                self, name, default_value
            )  # Save the updated settings file
        if not self._loading:
            self._save_settings_file(current_settings)

    def reset_to_default(self, setting_name: str | None = None):
        """Reset a setting (or all settings) to their default values.

        If setting_name is None, reset all settings.

        Parameters
        ----------
        setting_name : str | None
            The name of the setting to reset, or None to reset all settings.
        """
        try:
            with open(self._settings_path) as file:
                settings_data = yaml.safe_load(file) or {}
        except FileNotFoundError:
            return

        if setting_name:
            # Reset single setting
            if (
                setting_name in settings_data
                and "default" in settings_data[setting_name]
            ):
                default_value = settings_data[setting_name]["default"]
                # Handle tuple conversion for CANVAS_SIZE
                if setting_name == "CANVAS_SIZE" and isinstance(
                    default_value, list
                ):
                    default_value = tuple(default_value)
                setattr(self, setting_name, default_value)
                settings_data[setting_name]["value"] = settings_data[
                    setting_name
                ]["default"]
                self._save_settings_file(settings_data)
        else:
            # Reset all settings
            for name, setting_data in settings_data.items():
                if (
                    isinstance(setting_data, dict)
                    and "default" in setting_data
                ):
                    default_value = setting_data["default"]
                    # Handle tuple conversion for CANVAS_SIZE
                    if name == "CANVAS_SIZE" and isinstance(
                        default_value, list
                    ):
                        default_value = tuple(default_value)
                    setattr(self, name, default_value)
                    setting_data["value"] = setting_data["default"]
            self._save_settings_file(settings_data)

    def get_default_value(self, setting_name: str):
        """Get the default value for a setting."""
        try:
            with open(self._settings_path) as file:
                settings_data = yaml.safe_load(file) or {}
                if (
                    setting_name in settings_data
                    and "default" in settings_data[setting_name]
                ):
                    default = settings_data[setting_name]["default"]
                    # Handle tuple conversion for CANVAS_SIZE
                    if setting_name == "CANVAS_SIZE" and isinstance(
                        default, list
                    ):
                        return tuple(default)
                    return default
                return None
        except FileNotFoundError:
            return None

    def get_setting_info(self, name: str) -> dict:
        """Get metadata about a setting from the settings file."""
        try:
            with open(self._settings_path) as file:
                settings = yaml.safe_load(file) or {}
                if name in settings:
                    # Return all metadata except 'value'
                    return {
                        k: v for k, v in settings[name].items() if k != "value"
                    }
                return {}
        except FileNotFoundError:
            return {}

    def get_all_settings(self) -> dict:
        """Get all current setting values."""
        try:
            with open(self._settings_path) as file:
                settings = yaml.safe_load(file) or {}
                return {
                    name: setting["value"]
                    for name, setting in settings.items()
                    if "value" in setting
                }
        except FileNotFoundError:
            return {}

    def get_settings_by_group(self) -> dict:
        """Get all settings organized by their groups."""
        try:
            with open(self._settings_path) as file:
                settings = yaml.safe_load(file) or {}
                groups = {}

                for name, setting_data in settings.items():
                    if isinstance(setting_data, dict):
                        group = setting_data.get("group", "Other")
                        if group not in groups:
                            groups[group] = {}
                        groups[group][name] = setting_data

                return groups
        except FileNotFoundError:
            return {}

    def get_group_for_setting(self, name: str) -> str:
        """Get the group name for a specific setting."""
        try:
            with open(self._settings_path) as file:
                settings = yaml.safe_load(file) or {}
                if name in settings and isinstance(settings[name], dict):
                    return settings[name].get("group", "Other")
                return "Other"
        except FileNotFoundError:
            return "Other"

    def load_settings(self):
        """Load settings from the settings file."""
        try:
            with open(self._settings_path) as file:
                saved_settings = yaml.safe_load(file) or {}
        except FileNotFoundError:
            # If file doesn't exist, it will be created when settings are first saved
            saved_settings = {}

        # Load all settings from the file (rich format only)
        for name, setting_data in saved_settings.items():
            if isinstance(setting_data, dict) and "value" in setting_data:
                # Rich format
                value = setting_data["value"]
                # Handle type conversion for tuples (YAML converts tuples to lists)
                if isinstance(value, list) and name == "CANVAS_SIZE":
                    # Convert CANVAS_SIZE back to tuple for consistency
                    value = tuple(value)
                setattr(self, name, value)

    def __setattr__(self, name, value):
        """Override setattr to auto-save when settings are changed."""
        super().__setattr__(name, value)

        # Auto-save if we're changing a setting (not internal attributes) and not during loading
        if (
            not name.startswith("_")
            and name not in ("settings_file",)
            and hasattr(self, "_loading")
            and not self._loading
        ):
            self.save_settings()

    def save_settings(self):
        """Save the current settings to the settings file."""
        try:
            with open(self._settings_path) as file:
                current_settings = yaml.safe_load(file) or {}
        except FileNotFoundError:
            current_settings = {}

        # Update values while preserving metadata (rich format only)
        for attr_name in dir(self):
            if not attr_name.startswith("_") and not callable(
                getattr(self, attr_name)
            ):
                value = getattr(self, attr_name)

                if attr_name in current_settings:
                    # Update existing rich setting value
                    current_settings[attr_name]["value"] = value
                else:
                    # Create new setting entry with value first
                    current_settings[attr_name] = {
                        "value": value,
                        "default": value,
                        "description": f"Setting {attr_name}",
                        "group": "Other",
                    }

        self._save_settings_file(current_settings)

    def _save_settings_file(self, settings_data):
        """Helper to save settings data to file."""
        with open(self._settings_path, "w") as file:
            yaml.safe_dump(settings_data, file, default_flow_style=False)


_settings_instance = None


def get_settings() -> Settings:
    """Get the singleton instance of the settings manager."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(
            str(Path(__file__).parent / "ndev_settings.yaml")
        )
    return _settings_instance


def register_setting(
    name: str,
    default_value,
    description: str = "",
    group: str = "Other",
    **metadata,
):
    """
    Convenience function for other libraries to register settings.

    Example usage:
    from ndev_settings import register_setting
    register_setting("MY_PLUGIN_ENABLED", True, "Enable my plugin features", group="My Plugin")
    """
    settings = get_settings()
    settings.register_setting(
        name, default_value, description, group, **metadata
    )
