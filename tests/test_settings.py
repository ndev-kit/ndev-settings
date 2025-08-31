import os
import tempfile

import yaml

from ndev_settings import register_setting
from ndev_settings._settings import Settings, get_settings


def test_settings(tmp_path):
    """Test basic settings loading and saving."""
    # Write a temporary settings file in rich format
    settings_file = tmp_path / "test_settings.yaml"
    settings_file.write_text(
        yaml.dump(
            {
                "PREFERRED_READER": {
                    "value": "test-reader",
                    "default": "bioio-ome-tiff",
                    "description": "Preferred reader to use when opening images"
                },
                "SCENE_HANDLING": {
                    "value": "test-scene",
                    "default": "Open Scene Widget",
                    "description": "How to handle files with multiple scenes"
                },
                "CLEAR_LAYERS_ON_NEW_SCENE": {
                    "value": True,
                    "default": False,
                    "description": "Whether to clear the viewer when selecting a new scene"
                },
                "UNPACK_CHANNELS_AS_LAYERS": {
                    "value": False,
                    "default": True,
                    "description": "Whether to unpack channels as layers"
                },
                "CANVAS_SIZE": {
                    "value": [512, 512],
                    "default": [1024, 1024],
                    "description": "Height x width of the canvas when exporting a screenshot"
                }
            }
        )
    )

    # Test that the settings are loaded correctly (init calls load_settings)
    settings = Settings(str(settings_file))
    assert settings.PREFERRED_READER == "test-reader"
    assert settings.SCENE_HANDLING == "test-scene"
    assert settings.CLEAR_LAYERS_ON_NEW_SCENE
    assert not settings.UNPACK_CHANNELS_AS_LAYERS
    # Test that list from YAML is converted back to tuple
    assert settings.CANVAS_SIZE == (512, 512)
    assert isinstance(settings.CANVAS_SIZE, tuple)

    # Update settings, and then test that save works
    settings.PREFERRED_READER = "new-reader"
    settings.SCENE_HANDLING = "new-scene"
    settings.CLEAR_LAYERS_ON_NEW_SCENE = False
    settings.UNPACK_CHANNELS_AS_LAYERS = True
    settings.CANVAS_SIZE = (256, 256)

    settings.save_settings()

    with open(settings_file) as file:
        saved_settings = yaml.safe_load(file)

    # With rich format, we need to check the 'value' key
    assert saved_settings["PREFERRED_READER"]["value"] == "new-reader"
    assert saved_settings["SCENE_HANDLING"]["value"] == "new-scene"
    assert not saved_settings["CLEAR_LAYERS_ON_NEW_SCENE"]["value"]
    assert saved_settings["UNPACK_CHANNELS_AS_LAYERS"]["value"]
    # Note: YAML will save tuple as list, but that's expected
    assert saved_settings["CANVAS_SIZE"]["value"] == [256, 256]


def test_default_settings_structure():
    """Test that default settings are properly loaded from YAML."""
    settings = get_settings()

    # Check that all expected settings are present
    expected_settings = {
        "PREFERRED_READER", "SCENE_HANDLING", "CLEAR_LAYERS_ON_NEW_SCENE",
        "UNPACK_CHANNELS_AS_LAYERS", "CANVAS_SCALE", "OVERRIDE_CANVAS_SIZE", "CANVAS_SIZE"
    }

    # Get all loaded settings
    loaded_settings = set()
    for attr_name in dir(settings):
        if not attr_name.startswith('_') and not callable(getattr(settings, attr_name)):
            loaded_settings.add(attr_name)

    # Check that expected settings are a subset of loaded settings
    assert expected_settings.issubset(loaded_settings)

    # Check that each setting has proper metadata in YAML
    for setting_name in expected_settings:
        info = settings.get_setting_info(setting_name)
        assert "description" in info


def test_settings_registration():
    """Test that external libraries can register new settings."""
    # Create a temporary settings file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({}, f)
        settings_file = f.name

    try:
        # Create settings instance
        settings = Settings(settings_file)

        # Register a new setting
        settings.register_setting("TEST_SETTING", "default_value", "Test description")
        settings.register_setting("TEST_NUMERIC", 42, "Test numeric", min=0, max=100)
        settings.register_setting("TEST_BOOLEAN", True, "Test boolean")
        settings.register_setting("TEST_CHOICES", "option1", "Test choices",
                                choices=["option1", "option2", "option3"])

        # Check that settings were registered
        assert hasattr(settings, "TEST_SETTING")
        assert settings.TEST_SETTING == "default_value"
        assert settings.TEST_NUMERIC == 42
        assert settings.TEST_BOOLEAN is True
        assert settings.TEST_CHOICES == "option1"

        # Check that metadata is stored correctly
        test_info = settings.get_setting_info("TEST_NUMERIC")
        assert test_info["default"] == 42
        assert test_info["description"] == "Test numeric"
        assert test_info["min"] == 0
        assert test_info["max"] == 100

        choices_info = settings.get_setting_info("TEST_CHOICES")
        assert choices_info["choices"] == ["option1", "option2", "option3"]

        # Test that changing registered settings triggers save
        settings.TEST_SETTING = "new_value"

        # To properly test save/load of dynamically registered settings,
        # we create a new instance and register the setting again
        settings2 = Settings(settings_file)
        settings2.register_setting("TEST_SETTING", "default_value", "Test description")
        # The setting should have been loaded from the saved file, not use the default
        assert settings2.TEST_SETTING == "new_value"

    finally:
        os.unlink(settings_file)


def test_get_all_settings():
    """Test getting all settings at once."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "CANVAS_SCALE": {
                "value": 2.0,
                "default": 1.0,
                "description": "Scales exported figures and screenshots by this value"
            }
        }, f)
        settings_file = f.name

    try:
        settings = Settings(settings_file)
        settings.register_setting("CUSTOM_SETTING", "custom_value", "Custom setting")

        all_settings = settings.get_all_settings()

        # Should include all default settings plus custom ones
        assert "CANVAS_SCALE" in all_settings
        assert "CUSTOM_SETTING" in all_settings
        assert all_settings["CANVAS_SCALE"] == 2.0
        assert all_settings["CUSTOM_SETTING"] == "custom_value"

    finally:
        os.unlink(settings_file)


def test_register_setting_convenience_function():
    """Test the module-level register_setting function."""
    # This uses the singleton, so we need to be careful not to pollute other tests
    try:
        # Register a setting using the convenience function
        register_setting("TEMP_TEST_SETTING", "temp_value", "Temporary test setting")

        settings = get_settings()
        assert hasattr(settings, "TEMP_TEST_SETTING")
        assert settings.TEMP_TEST_SETTING == "temp_value"

        info = settings.get_setting_info("TEMP_TEST_SETTING")
        assert info["description"] == "Temporary test setting"

    finally:
        # Clean up - remove the temporary setting from the singleton
        settings = get_settings()
        # Since we're using YAML-based settings, we need to remove from YAML and object
        if hasattr(settings, "TEMP_TEST_SETTING"):
            delattr(settings, "TEMP_TEST_SETTING")
        # Also remove from YAML file
        try:
            with open(settings._settings_path) as file:
                current_settings = yaml.safe_load(file) or {}
            if "TEMP_TEST_SETTING" in current_settings:
                del current_settings["TEMP_TEST_SETTING"]
                settings._save_settings_file(current_settings)
        except FileNotFoundError:
            pass


def test_get_settings():
    """Test the singleton behavior of get_settings."""
    # this test will look at the real settings file
    # so if there are updates, this may need changed
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1.PREFERRED_READER == "bioio-ome-tiff"
    assert settings1 is settings2  # ensure is singleton

    original_reader = settings1.PREFERRED_READER
    settings1.PREFERRED_READER = "test-reader"

    assert settings2.PREFERRED_READER == "test-reader"

    settings1.PREFERRED_READER = original_reader  # reset for other tests

    assert settings1.SCENE_HANDLING == "Open Scene Widget"
    assert settings1.CLEAR_LAYERS_ON_NEW_SCENE is False
    assert settings1.UNPACK_CHANNELS_AS_LAYERS is True
    assert settings1.CANVAS_SCALE == 1.0
    assert settings1.OVERRIDE_CANVAS_SIZE is False
    # After our fixes, CANVAS_SIZE should be a tuple even when loaded from YAML
    assert settings1.CANVAS_SIZE == (1024, 1024)
    assert isinstance(settings1.CANVAS_SIZE, tuple)


def test_auto_save_behavior():
    """Test that settings are automatically saved when changed."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({
            "CANVAS_SCALE": {
                "value": 1.0,
                "default": 1.0,
                "description": "Scales exported figures and screenshots by this value"
            }
        }, f)
        settings_file = f.name

    try:
        settings = Settings(settings_file)

        # Change a setting - should auto-save
        settings.CANVAS_SCALE = 5.0

        # Create a new instance to verify the save happened
        settings2 = Settings(settings_file)
        assert settings2.CANVAS_SCALE == 5.0

    finally:
        os.unlink(settings_file)
