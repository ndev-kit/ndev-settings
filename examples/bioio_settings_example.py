"""
Example settings provider for bioio library.

This would be in the bioio library, in something like bioio/ndev_settings.py
"""

from ndev_settings import (
    SettingDefinition,
    create_dynamic_choice_setting,
    register_settings,
)


def register_bioio_settings(settings_manager):
    """
    Register all bioio-related settings.

    This function would be called by ndev-settings via entry points.
    Entry point configuration in bioio's pyproject.toml:

    [project.entry-points."ndev_settings.providers"]
    bioio = "bioio.ndev_settings:register_bioio_settings"
    """

    # Register multiple settings at once
    register_settings(
        settings_manager,
        # Dynamic choice setting for readers
        create_dynamic_choice_setting(
            name="preferred_reader",
            default_value="bioio-ome-tiff",
            entry_point_group="bioio.readers",
            description="Preferred reader to use when opening images",
            group="Reader",
            fallback_message="No bioio readers available",
        ),
        # Boolean setting for auto-detection
        SettingDefinition(
            name="auto_detect_reader",
            default_value=True,
            description="Automatically detect the best reader for each file type",
            group="Reader",
        ),
        # Numeric setting with bounds
        SettingDefinition(
            name="max_memory_usage_gb",
            default_value=4.0,
            description="Maximum memory usage for image loading (GB)",
            group="Performance",
            min_value=0.1,
            max_value=64.0,
            step=0.1,
        ),
        # Choice setting with static options
        SettingDefinition(
            name="compression_level",
            default_value="medium",
            description="Default compression level for saved images",
            group="Export",
            choices=["none", "low", "medium", "high", "maximum"],
        ),
    )


def register_ndevio_settings(settings_manager):
    """
    Register all ndevio-related settings.

    Entry point in ndevio's pyproject.toml:

    [project.entry-points."ndev_settings.providers"]
    ndevio = "ndevio.ndev_settings:register_ndevio_settings"
    """

    register_settings(
        settings_manager,
        # Dynamic choice for available formats
        create_dynamic_choice_setting(
            name="preferred_export_format",
            default_value="ome-tiff",
            entry_point_group="ndevio.writers",
            description="Preferred format for exporting images",
            group="Export",
            fallback_message="No export formats available",
        ),
        # Tuple setting for default tile size
        SettingDefinition(
            name="default_tile_size",
            default_value=(512, 512),
            description="Default tile size for tiled images (height, width)",
            group="Performance",
        ),
        # Boolean for metadata preservation
        SettingDefinition(
            name="preserve_original_metadata",
            default_value=True,
            description="Preserve original image metadata when possible",
            group="Export",
        ),
    )
