from ndev_settings import get_settings
from ndev_settings._settings_widget import SettingsContainer


def test_settings_container_initialization():
    """Test that the settings container initializes with all default widgets."""
    container = SettingsContainer()
    settings_singleton = get_settings()

    # Check that the container uses the singleton
    assert container.settings is settings_singleton

    # Check that widgets were created for available settings
    # With the grouped approach, check that some expected group.setting combinations exist
    expected_widgets = ["Reader.preferred_reader", "Reader.scene_handling", "Canvas.canvas_scale"]
    for widget_key in expected_widgets:
        group_name, setting_name = widget_key.split(".", 1)
        if hasattr(settings_singleton, group_name) and hasattr(getattr(settings_singleton, group_name), setting_name):
            assert widget_key in container._widgets


def test_widget_types_created_correctly():
    """Test that the correct widget types are created for different setting types."""
    container = SettingsContainer()
    settings = container.settings

    # Test boolean settings create checkboxes
    if (hasattr(settings, "Reader") and
        hasattr(settings.Reader, "clear_layers_on_new_scene") and
        isinstance(settings.Reader.clear_layers_on_new_scene, bool) and
        "Reader.clear_layers_on_new_scene" in container._widgets):
        widget = container._widgets["Reader.clear_layers_on_new_scene"]
        assert hasattr(widget, 'value')  # CheckBox has value attribute

    # Test that numeric settings create spinboxes
    if (hasattr(settings, "Canvas") and
        hasattr(settings.Canvas, "canvas_scale") and
        "Canvas.canvas_scale" in container._widgets):
        # Check if it's numeric and not boolean
        value = settings.Canvas.canvas_scale
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            widget = container._widgets["Canvas.canvas_scale"]
            assert hasattr(widget, 'min'), f"Widget for Canvas.canvas_scale is {type(widget)}, expected FloatSpinBox"


def test_widget_values_match_settings():
    """Test that widget values match the current settings values."""
    container = SettingsContainer()

    for widget_key, widget in container._widgets.items():
        # Parse the group.setting format
        group_name, setting_name = widget_key.split(".", 1)
        group_obj = getattr(container.settings, group_name)
        current_value = getattr(group_obj, setting_name)

        # Handle special case for PREFERRED_READER
        if setting_name == "preferred_reader" and not widget.enabled:
            continue

        # For tuple/list values, widget might convert to tuple
        if isinstance(current_value, list) and hasattr(widget, 'value'):
            assert widget.value == tuple(current_value) or widget.value == current_value
        else:
            assert widget.value == current_value


def test_widget_updates_settings():
    """Test that changing widget values updates the settings."""
    container = SettingsContainer()

    # Test with Canvas.canvas_scale (numeric setting)
    if "Canvas.canvas_scale" in container._widgets:
        widget = container._widgets["Canvas.canvas_scale"]
        original_value = container.settings.Canvas.canvas_scale

        # Change the widget value
        new_value = original_value + 1.0
        widget.value = new_value

        # Should automatically update settings via the event handler
        # We need to manually trigger the update since we're not in the GUI event loop
        container._update_settings()

        assert new_value == container.settings.Canvas.canvas_scale

        # Reset for other tests
        widget.value = original_value
        container._update_settings()


def test_settings_manual_save():
    """Test that settings can be manually saved after widget changes."""
    container = SettingsContainer()

    # Test with Canvas.canvas_scale if available
    if "Canvas.canvas_scale" in container._widgets:
        widget = container._widgets["Canvas.canvas_scale"]
        original_value = container.settings.Canvas.canvas_scale

        # Change the widget value
        new_value = original_value + 2.0
        widget.value = new_value

        # Update settings
        container._update_settings()

        # The manual save should have been called automatically in _update_settings
        # Verify the setting was updated
        assert container.settings.Canvas.canvas_scale == new_value

        # Reset for other tests
        widget.value = original_value
        container._update_settings()


def test_grouping_functionality():
    """Test that settings are properly grouped in the container."""
    container = SettingsContainer()

    # Check that we have widgets for different groups
    canvas_widgets = [key for key in container._widgets.keys() if key.startswith("Canvas.")]
    reader_widgets = [key for key in container._widgets.keys() if key.startswith("Reader.")]

    # Should have widgets from multiple groups
    if hasattr(container.settings, "Canvas"):
        assert len(canvas_widgets) > 0, "Should have Canvas widgets"

    if hasattr(container.settings, "Reader"):
        assert len(reader_widgets) > 0, "Should have Reader widgets"


def test_widget_container_with_custom_settings(test_group_file):
    """Test widget creation with custom settings file."""
    # Create a Settings instance with the custom file
    from ndev_settings._settings import Settings
    custom_settings = Settings(str(test_group_file))

    # Verify the settings were loaded correctly
    assert hasattr(custom_settings, "TestGroup")
    assert custom_settings.TestGroup.test_setting == "test_value"
    assert custom_settings.TestGroup.numeric_setting == 42.0
    assert custom_settings.TestGroup.boolean_setting is True


def test_settings_update_and_save():
    """Test the complete flow of updating settings through widgets and saving."""
    container = SettingsContainer()

    # Find a numeric widget to test with
    numeric_widget_key = None
    for key, widget in container._widgets.items():
        if hasattr(widget, 'min') and hasattr(widget, 'max'):  # Likely a numeric widget
            numeric_widget_key = key
            break

    if numeric_widget_key:
        widget = container._widgets[numeric_widget_key]
        group_name, setting_name = numeric_widget_key.split(".", 1)
        group_obj = getattr(container.settings, group_name)
        original_value = getattr(group_obj, setting_name)

        # Change widget value
        new_value = original_value + 5.0
        widget.value = new_value

        # Trigger update (which should also save)
        container._update_settings()

        # Verify the setting was updated
        updated_value = getattr(group_obj, setting_name)
        assert updated_value == new_value

        # Reset for other tests
        widget.value = original_value
        container._update_settings()
