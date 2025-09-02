try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._settings import Settings
from .registration import (
    SettingDefinition,
    create_dynamic_choice_setting,
    register_settings,
)

# Singleton instance
_settings_instance = None

def get_settings() -> Settings:
    """Get the singleton instance of the settings manager."""
    global _settings_instance
    if _settings_instance is None:
        from pathlib import Path
        _settings_instance = Settings(
            str(Path(__file__).parent / "ndev_settings.yaml")
        )
    return _settings_instance

__all__ = (
    "get_settings",
    "SettingDefinition",
    "register_settings",
    "create_dynamic_choice_setting",
)
