from pathlib import Path

import yaml

from ._default_settings import DEFAULT_SETTINGS


class Settings:
    """A class to manage settings for the nDev plugin."""

    def __init__(self, settings_file: str):
        """Initialize the settings manager with a file path."""
        self._settings_path = settings_file
        self._loading = True  # Flag to prevent auto-save during initialization
        self._default_settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        self._loading = False  # Enable auto-save after initialization

    def register_setting(self, name: str, default_value, description: str = "", **metadata):
        """Register a new setting (for use by other libraries)."""
        self._default_settings[name] = {
            "default": default_value,
            "description": description,
            **metadata
        }
        # Only set the attribute if it doesn't already exist (e.g., from loaded settings)
        if not hasattr(self, name):
            setattr(self, name, default_value)

    def get_setting_info(self, name: str) -> dict:
        """Get metadata about a setting."""
        return self._default_settings.get(name, {})

    def get_all_settings(self) -> dict:
        """Get all current setting values."""
        return {name: getattr(self, name) for name in self._default_settings}

    def load_settings(self):
        """Load settings from the settings file."""
        try:
            with open(self._settings_path) as file:
                saved_settings = yaml.safe_load(file) or {}
        except FileNotFoundError:
            saved_settings = {}

        # TODO: Simplify to be just one loop, because all settings should be contributed in the same way, 
        # Set all registered settings, using saved values or defaults
        for name, definition in self._default_settings.items():
            saved_value = saved_settings.get(name, definition["default"])
            default_value = definition["default"]

            # Handle type conversion for values that YAML might have changed
            # (e.g., tuples become lists when loaded from YAML)
            if isinstance(default_value, tuple) and isinstance(saved_value, list):
                value = tuple(saved_value)
            else:
                value = saved_value

            setattr(self, name, value)

        # Also load any extra settings from file that aren't pre-registered
        # This allows settings registered by other libraries to persist
        for name, value in saved_settings.items():
            if name not in self._default_settings and not hasattr(self, name):
                # Store as unregistered setting - we don't have type info for it
                setattr(self, name, value)

    def __setattr__(self, name, value):
        """Override setattr to auto-save when settings are changed."""
        super().__setattr__(name, value)

        # Auto-save if we're changing a setting (not internal attributes) and not during loading
        if (not name.startswith('_') and
            name not in ('settings_file',) and
            hasattr(self, '_loading') and
            not self._loading):
            self.save_settings()

    def save_settings(self):
        """Save the current settings to the settings file."""
        settings_to_save = {}
        for name in self._default_settings:
            if hasattr(self, name):
                settings_to_save[name] = getattr(self, name)

        with open(self._settings_path, "w") as file:
            yaml.safe_dump(settings_to_save, file)


_settings_instance = None


def get_settings() -> Settings:
    """Get the singleton instance of the settings manager."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings(
            str(Path(__file__).parent / "ndev_settings.yaml")
        )
    return _settings_instance


def register_setting(name: str, default_value, description: str = "", **metadata):
    """
    Convenience function for other libraries to register settings.

    Example usage:
    from ndev_settings import register_setting
    register_setting("MY_PLUGIN_ENABLED", True, "Enable my plugin features")
    """
    settings = get_settings()
    settings.register_setting(name, default_value, description, **metadata)
