try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from ._default_settings import DEFAULT_SETTINGS
from ._settings import get_settings, register_setting

__all__ = ("get_settings", "register_setting", "DEFAULT_SETTINGS")
