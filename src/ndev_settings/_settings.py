from __future__ import annotations

import hashlib
import logging
from importlib.metadata import entry_points
from pathlib import Path

import appdirs
import yaml

logger = logging.getLogger(__name__)

# User settings stored in platform-appropriate config directory
# Uses same location style as napari for familiarity
_SETTINGS_DIR = Path(appdirs.user_config_dir("ndev-settings", appauthor=False))
_SETTINGS_FILE = _SETTINGS_DIR / "settings.yaml"


def _load_yaml(path: Path) -> dict:
    """Load a YAML file, returning empty dict if missing or invalid.

    Uses FullLoader to support Python-specific types like tuples
    (e.g., canvas_size: !!python/tuple [1024, 1024]) in settings files.
    """
    try:
        with open(path) as f:
            return yaml.load(f, Loader=yaml.FullLoader) or {}
    except (FileNotFoundError, yaml.YAMLError, OSError):
        return {}


def _get_entry_points_hash() -> str:
    """Generate a hash of installed ndev_settings.manifest entry points.

    Used to detect when packages are installed/removed.
    """
    eps = entry_points(group="ndev_settings.manifest")
    ep_strings = sorted(f"{ep.name}:{ep.value}" for ep in eps)
    return hashlib.sha256("|".join(ep_strings).encode()).hexdigest()


def clear_settings() -> None:
    """Clear saved settings. Next load will use fresh defaults."""
    if _SETTINGS_FILE.exists():
        _SETTINGS_FILE.unlink()


class SettingsGroup:
    """Simple container for settings in a group."""


class Settings:
    """Manages persistent settings for ndev plugins.

    Settings are discovered from YAML files in installed packages (via entry points),
    merged together, and stored in a single user settings file. User modifications
    persist across sessions.

    When packages are installed/removed, new settings are merged in while
    preserving existing user values.
    """

    def __init__(self, defaults_file: str | None = None):
        """Initialize settings.

        Parameters
        ----------
        defaults_file : str, optional
            Path to a YAML file with default settings. Usually the main
            ndev_settings.yaml file. External contributions are merged in.
        """
        self._defaults_path = Path(defaults_file) if defaults_file else None
        self._grouped_settings: dict = {}
        self._load()

    def _load(self):
        """Load settings from saved file or discover from package YAML files.

        On first load (or after package changes), discovers settings from all
        installed packages and saves them. Subsequent loads just read the saved file.
        """
        saved = self._load_saved()

        if saved is not None:
            # Fast path: use saved settings
            all_settings = saved
        else:
            # Slow path: discover from package YAML files, then save
            all_settings = self._load_defaults()
            self._save_settings(all_settings)

        # Build group objects and store
        self._build_groups(all_settings)
        self._grouped_settings = all_settings

    def _load_defaults(self) -> dict:
        """Load default settings from main file and external contributions."""
        all_settings = {}

        # Load main defaults file if provided
        if self._defaults_path:
            all_settings = _load_yaml(self._defaults_path)

        # Load external YAML files from entry points
        # Sort for deterministic merge order across environments
        eps = sorted(
            entry_points(group="ndev_settings.manifest"),
            key=lambda ep: (ep.name, ep.value),
        )
        for ep in eps:
            try:
                package_name, resource_name = ep.value.split(":", 1)

                # Use distribution() to find package location WITHOUT importing it
                # This avoids slow package imports (e.g., ndevio takes 2.5s to import)
                from importlib.metadata import distribution

                dist = distribution(package_name)
                yaml_path = None

                # For regular installs, dist.files contains the file list
                for file in dist.files or []:
                    if file.name == resource_name and package_name in str(
                        file
                    ):
                        yaml_path = Path(str(dist.locate_file(file)))
                        break

                if yaml_path is None:
                    # For editable installs, check direct_url.json (PEP 610)
                    direct_url_file = dist._path / "direct_url.json"
                    if direct_url_file.exists():
                        import json

                        with open(direct_url_file) as f:
                            direct_url = json.load(f)
                        if direct_url.get("dir_info", {}).get("editable"):
                            # Editable install - use source path
                            url = direct_url["url"]
                            if url.startswith("file:///"):
                                source_path = Path(url[8:])  # Remove file:///
                            elif url.startswith("file://"):
                                source_path = Path(url[7:])
                            else:
                                source_path = Path(url)
                            yaml_path = (
                                source_path
                                / "src"
                                / package_name
                                / resource_name
                            )

                if yaml_path is None:
                    # Final fallback: try site-packages path
                    package_location = str(dist.locate_file(package_name))
                    yaml_path = Path(package_location) / resource_name

                external = _load_yaml(yaml_path)

                # Merge external settings (first one wins for conflicts)
                for group_name, group_settings in external.items():
                    if group_name not in all_settings:
                        all_settings[group_name] = {}
                    for name, data in group_settings.items():
                        if name not in all_settings[group_name]:
                            all_settings[group_name][name] = data
            except (ModuleNotFoundError, FileNotFoundError, ValueError, PermissionError, OSError) as e:
                logger.warning(
                    "Failed to load settings from '%s': %s", ep.name, e
                )

        return all_settings

    def _load_saved(self) -> dict | None:
        """Load saved settings if valid, return None if stale or missing."""
        if not _SETTINGS_FILE.exists():
            return None

        saved = _load_yaml(_SETTINGS_FILE)
        if not saved:
            return None

        # Check if packages changed - if so, need to re-discover
        saved_hash = saved.pop("_entry_points_hash", None)
        if saved_hash != _get_entry_points_hash():
            # Packages installed/removed - merge new defaults with saved values
            defaults = self._load_defaults()
            merged = self._merge_with_saved(defaults, saved)
            self._save_settings(merged)
            return merged

        return saved

    def _merge_with_saved(self, defaults: dict, saved: dict) -> dict:
        """Merge saved user values into fresh defaults."""
        merged = {}
        for group_name, group_settings in defaults.items():
            # Skip metadata keys
            if group_name.startswith("_"):
                continue
            merged[group_name] = {}
            for name, data in group_settings.items():
                merged[group_name][name] = data.copy()
                # Override with saved value if exists
                if group_name in saved and name in saved[group_name]:
                    saved_data = saved[group_name][name]
                    if isinstance(saved_data, dict) and "value" in saved_data:
                        merged[group_name][name]["value"] = saved_data["value"]
        return merged

    def _save_settings(self, settings: dict) -> None:
        """Save settings to file in flat format with hash at top."""
        try:
            _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
            # Flat format: hash first, then all settings groups
            data = {"_entry_points_hash": _get_entry_points_hash(), **settings}
            with open(_SETTINGS_FILE, "w") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        except (OSError, PermissionError) as e:
            logger.warning(
                "Failed to save settings to %s: %s", _SETTINGS_FILE, e
            )

    def _build_groups(self, settings: dict):
        """Create SettingsGroup objects from settings dict."""
        for group_name, group_settings in settings.items():
            # Skip metadata keys (e.g., _entry_points_hash)
            if group_name.startswith("_"):
                continue
            group_obj = SettingsGroup()
            for name, setting_data in group_settings.items():
                if isinstance(setting_data, dict) and "value" in setting_data:
                    setattr(group_obj, name, setting_data["value"])
            setattr(self, group_name, group_obj)

    def _sync_groups_to_dict(self):
        """Sync current group object values back to _grouped_settings dict."""
        for group_name, group_settings in self._grouped_settings.items():
            group_obj = getattr(self, group_name, None)
            if isinstance(group_obj, SettingsGroup):
                for setting_name in group_settings:
                    if hasattr(group_obj, setting_name):
                        value = getattr(group_obj, setting_name)
                        self._grouped_settings[group_name][setting_name][
                            "value"
                        ] = value

    def save(self):
        """Save current settings to persist across sessions."""
        self._sync_groups_to_dict()
        self._save_settings(self._grouped_settings)

    def reset_to_default(
        self, setting_name: str | None = None, group: str | None = None
    ):
        """Reset a setting (or all settings) to their default values."""
        if setting_name:
            # Reset single setting
            for group_name, group_settings in self._grouped_settings.items():
                if setting_name in group_settings:
                    default = group_settings[setting_name].get("default")
                    if default is not None:
                        setattr(
                            getattr(self, group_name), setting_name, default
                        )
                        group_settings[setting_name]["value"] = default
                    self.save()
                    return
        else:
            # Reset all settings (optionally filtered by group)
            for group_name, group_settings in self._grouped_settings.items():
                if group and group_name != group:
                    continue
                for name, setting_data in group_settings.items():
                    if "default" in setting_data:
                        default = setting_data["default"]
                        setattr(getattr(self, group_name), name, default)
                        setting_data["value"] = default
            self.save()

    def get_dynamic_choices(self, provider_key: str) -> list:
        """Get dynamic choices from entry points."""
        return [ep.name for ep in entry_points(group=provider_key)]
