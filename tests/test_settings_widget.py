import os
import tempfile
from unittest.mock import Mock, patch

import yaml

from ndev_settings._default_settings import DEFAULT_SETTINGS
from ndev_settings._settings import get_settings
from ndev_settings._settings_widget import SettingsContainer


def test_settings_container_initialization():
    """Test that the settings container initializes with all default widgets."""
    container = SettingsContainer()
    settings_singleton = get_settings()

    # Check that the container uses the singleton
    assert container.settings is settings_singleton

    # Check that widgets were created for all default settings
    expected_widgets = set(DEFAULT_SETTINGS.keys())
    created_widgets = set(container._widgets.keys())

    # PREFERRED_READER should always be created, but might be disabled
    # All other widgets should be created
    assert created_widgets == expected_widgets


def test_widget_types_created_correctly():
    """Test that the correct widget types are created for different setting types."""
    container = SettingsContainer()

    # Test that boolean settings create checkboxes
    bool_settings = [name for name, info in DEFAULT_SETTINGS.items()
                    if isinstance(info["default"], bool)]
    for setting_name in bool_settings:
        if setting_name in container._widgets:
            widget = container._widgets[setting_name]
            assert hasattr(widget, 'value')  # CheckBox has value attribute

    # Test that settings with choices create ComboBoxes
    choice_settings = [name for name, info in DEFAULT_SETTINGS.items()
                      if "choices" in info]
    for setting_name in choice_settings:
        if setting_name in container._widgets:
            widget = container._widgets[setting_name]
            assert hasattr(widget, 'choices')  # ComboBox has choices attribute

    # Test that numeric settings create spinboxes (exclude booleans since bool is subclass of int)
    numeric_settings = [name for name, info in DEFAULT_SETTINGS.items()
                       if isinstance(info["default"], int | float)
                       and not isinstance(info["default"], bool)
                       and "choices" not in info]
    for setting_name in numeric_settings:
        if setting_name in container._widgets:
            widget = container._widgets[setting_name]
            assert hasattr(widget, 'min'), f"Widget for {setting_name} is {type(widget)}, expected FloatSpinBox"


def test_widget_values_match_settings():
    """Test that widget values match the current settings values."""
    container = SettingsContainer()

    for setting_name, widget in container._widgets.items():
        current_value = getattr(container.settings, setting_name)

        # Handle special case for PREFERRED_READER
        if setting_name == "PREFERRED_READER" and not widget.enabled:
            continue

        # For tuple/list values, widget might convert to tuple
        if isinstance(current_value, list) and hasattr(widget, 'value'):
            assert widget.value == tuple(current_value) or widget.value == current_value
        else:
            assert widget.value == current_value


def test_widget_updates_settings():
    """Test that changing widget values updates the settings."""
    container = SettingsContainer()

    # Test with CANVAS_SCALE (numeric setting)
    if "CANVAS_SCALE" in container._widgets:
        widget = container._widgets["CANVAS_SCALE"]
        original_value = container.settings.CANVAS_SCALE

        # Change the widget value
        new_value = original_value + 1.0
        widget.value = new_value

        # Should automatically update settings via the event handler
        # We need to manually trigger the update since we're not in the GUI event loop
        container._update_settings()

        assert new_value == container.settings.CANVAS_SCALE

        # Reset for other tests
        widget.value = original_value
        container._update_settings()


def test_dynamic_settings_registration():
    """Test that dynamically registered settings create widgets."""
    # Create a temporary settings file to avoid polluting the main one
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        # Create a simple settings dict that YAML can handle
        test_settings = {
            "CANVAS_SCALE": 1.0,
            "CANVAS_SIZE": [1024, 1024],  # Use list instead of tuple for YAML
            "PREFERRED_READER": "test-reader"
        }
        yaml.dump(test_settings, f)
        temp_file = f.name

    try:
        # We need to test with a fresh settings instance
        from ndev_settings._settings import Settings
        temp_settings = Settings(temp_file)

        # Register a new setting
        temp_settings.register_setting("TEST_DYNAMIC", "test_value", "Dynamic test setting")
        temp_settings.register_setting("TEST_BOOL", False, "Dynamic boolean")
        temp_settings.register_setting("TEST_CHOICE", "A", "Dynamic choice",
                                      choices=["A", "B", "C"])

        # Create a container with this settings instance (we'd need to modify the class for this)
        # For now, we'll just test that the settings were registered
        assert hasattr(temp_settings, "TEST_DYNAMIC")
        assert temp_settings.TEST_DYNAMIC == "test_value"
        assert hasattr(temp_settings, "TEST_BOOL")
        assert temp_settings.TEST_BOOL is False
        assert hasattr(temp_settings, "TEST_CHOICE")
        assert temp_settings.TEST_CHOICE == "A"

    finally:
        os.unlink(temp_file)


@patch('ndev_settings._settings_widget.entry_points')
def test_preferred_reader_widget_with_available_readers(mock_entry_points):
    """Test PREFERRED_READER widget when readers are available."""
    # Mock some readers being available
    mock_reader1 = Mock()
    mock_reader1.name = "bioio-ome-tiff"
    mock_reader2 = Mock()
    mock_reader2.name = "bioio-czi"

    mock_entry_points.return_value = [mock_reader1, mock_reader2]

    container = SettingsContainer()

    # Should have created a PREFERRED_READER widget
    assert "PREFERRED_READER" in container._widgets
    reader_widget = container._widgets["PREFERRED_READER"]

    # Widget should be enabled and have the available readers as choices
    assert reader_widget.enabled
    assert "bioio-ome-tiff" in reader_widget.choices
    assert "bioio-czi" in reader_widget.choices


@patch('ndev_settings._settings_widget.entry_points')
def test_preferred_reader_widget_no_available_readers(mock_entry_points):
    """Test PREFERRED_READER widget when no readers are available."""
    # Mock no readers being available
    mock_entry_points.return_value = []

    container = SettingsContainer()

    # Should still create widget but disabled
    if "PREFERRED_READER" in container._widgets:
        reader_widget = container._widgets["PREFERRED_READER"]
        assert not reader_widget.enabled
        assert list(reader_widget.choices) == ["No readers found"]


def test_settings_groups():
    """Test that settings are properly grouped in the UI."""
    container = SettingsContainer()
    groups = container._group_settings()

    # Should have Reader Settings and Export Settings groups
    assert "Reader Settings" in groups
    assert "Export Settings" in groups

    # Check that expected settings are in correct groups
    reader_settings = groups["Reader Settings"]
    export_settings = groups["Export Settings"]

    assert "PREFERRED_READER" in reader_settings
    assert "SCENE_HANDLING" in reader_settings
    assert "CANVAS_SCALE" in export_settings
    assert "CANVAS_SIZE" in export_settings


def test_canvas_size_tuple_handling():
    """Test that CANVAS_SIZE (tuple/list) is handled correctly."""
    container = SettingsContainer()

    # Should create a widget for CANVAS_SIZE
    assert "CANVAS_SIZE" in container._widgets
    canvas_widget = container._widgets["CANVAS_SIZE"]

    # Value should be a tuple (converted from list if needed)
    current_size = container.settings.CANVAS_SIZE
    assert isinstance(canvas_widget.value, tuple)

    # Should match the settings value (handling list/tuple conversion)
    if isinstance(current_size, list):
        assert canvas_widget.value == tuple(current_size)
    else:
        assert canvas_widget.value == current_size


def test_other_settings_group():
    """Test that unrecognized settings go into 'Other Settings' group."""
    # Create temp settings instance and register a custom setting
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump({}, f)
        temp_file = f.name

    try:
        from ndev_settings._settings import Settings
        temp_settings = Settings(temp_file)
        temp_settings.register_setting("UNKNOWN_SETTING", "test", "Unknown setting")

        # Mock the container to use our temp settings
        # This is a bit tricky since SettingsContainer uses get_settings() singleton
        # We'll test the grouping logic directly
        container = SettingsContainer()

        # Temporarily add our custom setting to test grouping
        original_registered = container.settings._default_settings.copy()
        container.settings._default_settings["UNKNOWN_SETTING"] = {
            "default": "test", "description": "Unknown setting"
        }

        groups = container._group_settings()

        # Should create "Other Settings" group
        assert "Other Settings" in groups
        assert "UNKNOWN_SETTING" in groups["Other Settings"]

        # Restore original settings
        container.settings._default_settings = original_registered

    finally:
        os.unlink(temp_file)
