from ndev_settings._settings import Settings
from ndev_settings import get_settings


def test_settings_loading_and_saving(settings_file):
    """Test basic settings loading and saving with grouped structure."""
    # Test that the settings are loaded correctly (init calls load)
    settings = Settings(str(settings_file))

    # Test grouped structure access
    assert settings.Reader.preferred_reader == "test-reader"
    assert settings.Reader.scene_handling == "test-scene"
    assert settings.Reader.clear_layers_on_new_scene is True
    assert settings.Reader.unpack_channels_as_layers is False

    # Test that lists stay as lists (not converted to tuples)
    assert settings.Canvas.canvas_size == [512, 512]
    assert settings.Canvas.canvas_scale == 2.5


def test_settings_modification_and_manual_save(simple_settings_file):
    """Test modifying settings and manually saving them."""
    # Load settings and modify them
    settings = Settings(str(simple_settings_file))
    assert settings.Canvas.canvas_scale == 1.0

    # Modify the setting
    settings.Canvas.canvas_scale = 3.0

    # Manually save
    settings.save()

    # Create a new instance to verify save worked
    settings2 = Settings(str(simple_settings_file))
    assert settings2.Canvas.canvas_scale == 3.0


def test_reset_to_default(reset_settings_file):
    """Test resetting settings to default values."""
    settings = Settings(str(reset_settings_file))

    # Verify initial modified values
    assert settings.Canvas.canvas_scale == 5.0
    assert settings.Reader.preferred_reader == "modified-reader"

    # Reset a single setting
    settings.reset_to_default("canvas_scale")
    assert settings.Canvas.canvas_scale == 1.0
    assert settings.Reader.preferred_reader == "modified-reader"  # Should remain unchanged

    # Reset another setting
    settings.reset_to_default("preferred_reader")
    assert settings.Reader.preferred_reader == "bioio-ome-tiff"


def test_reset_all_settings(reset_settings_file):
    """Test resetting all settings to defaults."""
    settings = Settings(str(reset_settings_file))

    # Reset all settings
    settings.reset_to_default()

    assert settings.Canvas.canvas_scale == 1.0
    assert settings.Reader.preferred_reader == "bioio-ome-tiff"


def test_reset_by_group(reset_settings_file):
    """Test resetting settings by group."""
    settings = Settings(str(reset_settings_file))

    # Reset only Canvas group
    settings.reset_to_default(group="Canvas")

    assert settings.Canvas.canvas_scale == 1.0
    assert settings.Reader.preferred_reader == "modified-reader"  # Should remain unchanged


def test_get_settings_singleton():
    """Test the singleton behavior of get_settings."""
    # Get two instances of settings
    settings1 = get_settings()
    settings2 = get_settings()

    # They should be the same object
    assert settings1 is settings2


def test_empty_settings_file(empty_settings_file):
    """Test behavior with empty or non-existent settings file."""
    # Test with non-existent file
    settings = Settings(str(empty_settings_file))

    # Should not raise error and should have no groups
    assert not hasattr(settings, 'Canvas')
    assert not hasattr(settings, 'Reader')


def test_settings_with_missing_metadata(incomplete_settings_file):
    """Test settings that might be missing some metadata."""
    settings = Settings(str(incomplete_settings_file))
    assert settings.Canvas.canvas_scale == 2.0
    assert settings.Canvas.incomplete_setting == "test"

    # Save should work and preserve/add metadata
    settings.save()

    # Reload and verify it still works
    settings2 = Settings(str(incomplete_settings_file))
    assert settings2.Canvas.canvas_scale == 2.0
    assert settings2.Canvas.incomplete_setting == "test"


def test_programmatic_settings_creation(tmp_path):
    """Test creating settings programmatically and saving them."""
    settings_file = tmp_path / "test_settings.yaml"

    # Create settings with empty file
    settings = Settings(str(settings_file))

    # This should create the groups as needed when we save
    # For now, we need to manually create the group structure
    from ndev_settings._settings import SettingsGroup

    # Create Canvas group programmatically
    canvas_group = SettingsGroup()
    canvas_group.canvas_scale = 2.0
    canvas_group.canvas_size = [800, 600]
    settings.Canvas = canvas_group

    # Save the programmatically created settings
    settings.save()

    # Load again and verify
    settings2 = Settings(str(settings_file))
    assert settings2.Canvas.canvas_scale == 2.0
    assert settings2.Canvas.canvas_size == [800, 600]


def test_dynamic_choices():
    """Test that dynamic choices method exists and doesn't crash."""
    settings = Settings.__new__(Settings)  # Create without calling __init__

    # Test the method exists and handles missing entry points gracefully
    choices = settings._get_dynamic_choices("nonexistent.entry.point")
    assert isinstance(choices, list)
    assert len(choices) == 0  # Should return empty list when no entries found
