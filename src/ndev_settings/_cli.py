"""Command-line interface for ndev-settings utilities."""

import sys
from pathlib import Path

import yaml


def reset_values_to_defaults(settings_file: Path | str) -> bool:
    """Reset all 'value' fields to match 'default' fields in a settings YAML file.

    Parameters
    ----------
    settings_file : Path | str
        Path to the settings YAML file to reset

    Returns
    -------
    bool
        True if file was modified, False otherwise
    """
    settings_file = Path(settings_file)

    if not settings_file.exists():
        print(f"Settings file not found: {settings_file}")
        return False

    with open(settings_file) as f:
        settings = yaml.safe_load(f)

    if not settings:
        return False

    modified = False

    for group_name, group_settings in settings.items():
        for setting_name, setting_data in group_settings.items():
            if (
                isinstance(setting_data, dict)
                and "default" in setting_data
                and "value" in setting_data
                and setting_data["value"] != setting_data["default"]
            ):
                print(
                    f"Resetting {group_name}.{setting_name}: "
                    f"{setting_data['value']} -> {setting_data['default']}"
                )
                setting_data["value"] = setting_data["default"]
                modified = True

    if modified:
        with open(settings_file, "w") as f:
            yaml.dump(settings, f, default_flow_style=False, sort_keys=False)

    return modified


def main_reset_values():
    """Entry point for reset-settings-values command."""
    if len(sys.argv) < 2:
        print(
            "Usage: reset-settings-values <path-to-settings.yaml> [<path2> ...]"
        )
        print("\nResets all 'value' fields to their 'default' values.")
        print(
            "Useful as a pre-commit hook to prevent committing local preferences."
        )
        return 1

    # Process all files passed as arguments
    any_modified = False
    for settings_path in sys.argv[1:]:
        settings_file = Path(settings_path)

        if reset_values_to_defaults(settings_file):
            any_modified = True

    if any_modified:
        print(
            "\nWARNING: Settings file(s) were modified to reset values to defaults."
        )
        print("Please review and re-stage the changes.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main_reset_values())
