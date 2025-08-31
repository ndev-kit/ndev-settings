from pathlib import Path

import yaml

# Define all default settings with their metadata
DEFAULT_SETTINGS = {
    "PREFERRED_READER": {
        "default": "bioio-ome-tiff",
        "description": "Preferred reader to use when opening images",
    },
    "SCENE_HANDLING": {
        "default": "Open Scene Widget",
        "description": "How to handle files with multiple scenes",
        "choices": ["Open Scene Widget", "View All Scenes", "View First Scene Only"],
    },
    "CLEAR_LAYERS_ON_NEW_SCENE": {
        "default": False,
        "description": "Whether to clear the viewer when selecting a new scene",
    },
    "UNPACK_CHANNELS_AS_LAYERS": {
        "default": True,
        "description": "Whether to unpack channels as layers",
    },
    "CANVAS_SCALE": {
        "default": 1.0,
        "description": "Scales exported figures and screenshots by this value",
        "min": 0.1,
        "max": 100.0,
    },
    "OVERRIDE_CANVAS_SIZE": {
        "default": False,
        "description": "Whether to override the canvas size when exporting canvas screenshot",
    },
    "CANVAS_SIZE": {
        "default": (1024, 1024),
        "description": "Height x width of the canvas when exporting a screenshot",
    },
}


class Settings:
    """A class to manage settings for the nDev plugin."""

    def __init__(self, settings_file: str):
        """Initialize the settings manager with a file path."""
        self._settings_path = settings_file
        self._loading = True  # Flag to prevent auto-save during initialization
        self._registered_settings = DEFAULT_SETTINGS.copy()
        self.load_settings()
        self._loading = False  # Enable auto-save after initialization

    def register_setting(self, name: str, default_value, description: str = "", **metadata):
        """Register a new setting (for use by other libraries)."""
        self._registered_settings[name] = {
            "default": default_value,
            "description": description,
            **metadata
        }
        # Set the attribute with the default value if it doesn't exist
        if not hasattr(self, name):
            setattr(self, name, default_value)

    def get_setting_info(self, name: str) -> dict:
        """Get metadata about a setting."""
        return self._registered_settings.get(name, {})

    def get_all_settings(self) -> dict:
        """Get all current setting values."""
        return {name: getattr(self, name) for name in self._registered_settings}

    def load_settings(self):
        """Load settings from the settings file."""
        try:
            with open(self._settings_path) as file:
                saved_settings = yaml.safe_load(file) or {}
        except FileNotFoundError:
            saved_settings = {}

        # Set all registered settings, using saved values or defaults
        for name, definition in self._registered_settings.items():
            value = saved_settings.get(name, definition["default"])
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
        for name in self._registered_settings:
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
