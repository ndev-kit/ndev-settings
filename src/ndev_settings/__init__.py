try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._settings import get_settings
from .registration import (
    SettingDefinition,
    create_dynamic_choice_setting,
    register_settings,
)

__all__ = (
    "get_settings",
    "SettingDefinition",
    "register_settings",
    "create_dynamic_choice_setting",
)
