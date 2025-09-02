"""
Helper utilities for external libraries to register settings with ndev-settings.

This module provides templates and utilities to make it easy for external libraries
to register their settings via entry points.
"""

from typing import Any


class SettingDefinition:
    """Helper class to define a setting with all its metadata."""

    def __init__(
        self,
        name: str,
        default_value: Any,
        description: str = "",
        group: str = "External",
        choices: list[str] | None = None,
        dynamic_choices: dict[str, str] | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
        step: float | None = None,
        **kwargs,
    ):
        self.name = name
        self.default_value = default_value
        self.description = description
        self.group = group
        self.metadata = {}

        if choices is not None:
            self.metadata["choices"] = choices
        if dynamic_choices is not None:
            self.metadata["dynamic_choices"] = dynamic_choices
        if min_value is not None:
            self.metadata["min"] = min_value
        if max_value is not None:
            self.metadata["max"] = max_value
        if step is not None:
            self.metadata["step"] = step

        # Add any additional metadata
        self.metadata.update(kwargs)

    def register(self, settings_manager):
        """Register this setting with a settings manager."""
        settings_manager.register_setting(
            self.name,
            self.default_value,
            self.description,
            self.group,
            **self.metadata,
        )


def register_settings(
    settings_manager, *setting_definitions: SettingDefinition
):
    """
    Convenience function to register multiple settings at once.

    Usage:
        def register_my_settings(settings_manager):
            register_settings(
                settings_manager,
                SettingDefinition("setting1", "default1", "Description 1", "MyGroup"),
                SettingDefinition("setting2", True, "Description 2", "MyGroup"),
                SettingDefinition("setting3", 1.0, "Description 3", "MyGroup", min_value=0, max_value=10),
            )
    """
    for setting_def in setting_definitions:
        setting_def.register(settings_manager)


def create_dynamic_choice_setting(
    name: str,
    default_value: str,
    entry_point_group: str,
    description: str = "",
    group: str = "External",
    fallback_message: str = "No options available",
) -> SettingDefinition:
    """
    Helper to create a setting with dynamic choices from an entry point group.

    Args:
        name: Setting name
        default_value: Default value for the setting
        entry_point_group: Entry point group to get choices from (e.g., "bioio.readers")
        description: Setting description
        group: Settings group name
        fallback_message: Message when no choices are available
    """
    return SettingDefinition(
        name=name,
        default_value=default_value,
        description=description,
        group=group,
        dynamic_choices={
            "provider": entry_point_group,
            "fallback_message": fallback_message,
        },
    )
