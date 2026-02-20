import pytest

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
    expected_widgets = [
        "Group_A.setting_int",
        "Group_A.setting_choices",
        "Group_A.setting_float",
    ]
    for widget_key in expected_widgets:
        group_name, setting_name = widget_key.split(".", 1)
        if hasattr(settings_singleton, group_name) and hasattr(
            getattr(settings_singleton, group_name), setting_name
        ):
            assert widget_key in container._widgets


def test_widget_types_created_correctly():
    """Test that the correct widget types are created for different setting types."""
    container = SettingsContainer()
    settings = container.settings

    # Test boolean settings create checkboxes
    if (
        hasattr(settings, "Group_A")
        and hasattr(settings.Group_A, "setting_bool")
        and isinstance(settings.Group_A.setting_bool, bool)
        and "Group_A.setting_bool" in container._widgets
    ):
        widget = container._widgets["Group_A.setting_bool"]
        assert hasattr(widget, "value")  # CheckBox has value attribute

    # Test that numeric settings create spinboxes
    if (
        hasattr(settings, "Group_A")
        and hasattr(settings.Group_A, "setting_float")
        and "Group_A.setting_float" in container._widgets
    ):
        # Check if it's numeric and not boolean
        value = settings.Group_A.setting_float
        if isinstance(value, int | float) and not isinstance(value, bool):
            widget = container._widgets["Group_A.setting_float"]
            assert hasattr(
                widget, "min"
            ), f"Widget for Group_A.setting_float is {type(widget)}, expected FloatSpinBox"


def test_widget_values_match_settings():
    """Test that widget values match the current settings values."""
    container = SettingsContainer()

    for widget_key, widget in container._widgets.items():
        # Parse the group.setting format
        group_name, setting_name = widget_key.split(".", 1)
        group_obj = getattr(container.settings, group_name)
        current_value = getattr(group_obj, setting_name)

        # Handle special case for dynamic choices widgets
        if setting_name == "setting_dynamic" and not widget.enabled:
            assert "No readers found" in str(
                widget.value
            ) or "No choices" in str(widget.value)
            assert current_value == "bioio-ome-tiff"  # from YAML
            continue

        # For tuple/list values, widget might convert to tuple
        if isinstance(current_value, list) and hasattr(widget, "value"):
            assert (
                widget.value == tuple(current_value)
                or widget.value == current_value
            )
        else:
            assert widget.value == current_value


def test_widget_updates_settings():
    """Test that changing widget values updates the settings."""
    container = SettingsContainer()

    # Test with Group_A.setting_float (numeric setting)
    if "Group_A.setting_float" in container._widgets:
        widget = container._widgets["Group_A.setting_float"]
        original_value = container.settings.Group_A.setting_float

        # Change the widget value
        new_value = original_value + 1.0
        widget.value = new_value

        # Should automatically update settings via the event handler
        # We need to manually trigger the update since we're not in the GUI event loop
        container._update_settings()

        assert new_value == pytest.approx(
            container.settings.Group_A.setting_float
        )

        # Reset for other tests
        widget.value = original_value
        container._update_settings()


def test_settings_manual_save():
    """Test that settings can be manually saved after widget changes."""
    container = SettingsContainer()

    # Test with Group_A.setting_float if available
    if "Group_A.setting_float" in container._widgets:
        widget = container._widgets["Group_A.setting_float"]
        original_value = container.settings.Group_A.setting_float

        # Change the widget value
        new_value = original_value + 2.0
        widget.value = new_value

        # Update settings
        container._update_settings()

        # The manual save should have been called automatically in _update_settings
        # Verify the setting was updated
        assert container.settings.Group_A.setting_float == pytest.approx(
            new_value
        )

        # Reset for other tests
        widget.value = original_value
        container._update_settings()


def test_grouping_functionality():
    """Test that settings are properly grouped in the container."""
    container = SettingsContainer()

    # Check that we have widgets for different groups
    canvas_widgets = [
        key for key in container._widgets if key.startswith("Canvas.")
    ]
    reader_widgets = [
        key for key in container._widgets if key.startswith("ndevio_reader.")
    ]

    # Should have widgets from multiple groups
    if hasattr(container.settings, "Canvas"):
        assert len(canvas_widgets) > 0, "Should have Canvas widgets"

    if hasattr(container.settings, "ndevio_reader"):
        assert len(reader_widgets) > 0, "Should have ndevio_reader widgets"


def test_widget_container_with_custom_settings(test_settings_file):
    """Test widget creation with custom settings file."""
    # Create a Settings instance with the custom file
    from ndev_settings._settings import Settings

    custom_settings = Settings(str(test_settings_file))

    # Verify the settings were loaded correctly
    assert hasattr(custom_settings, "Group_A")
    assert custom_settings.Group_A.setting_int == 49
    assert custom_settings.Group_A.setting_float == 3.14
    assert custom_settings.Group_A.setting_bool is True


def test_settings_update_and_save():
    """Test the complete flow of updating settings through widgets and saving."""
    container = SettingsContainer()

    # Find a numeric widget to test with
    numeric_widget_key = None
    for key, widget in container._widgets.items():
        if hasattr(widget, "min") and hasattr(
            widget, "max"
        ):  # Likely a numeric widget
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


def test_reset_to_defaults():
    """Test that the reset to defaults button resets all settings and updates widgets."""
    container = SettingsContainer()

    settings = container.settings

    # Change some settings via widgets
    if "Group_A.setting_float" in container._widgets:
        widget = container._widgets["Group_A.setting_float"]
        original_value = settings.Group_A.setting_float
        widget.value = original_value + 3.0
        container._update_settings()
        assert settings.Group_A.setting_float == pytest.approx(
            original_value + 3.0
        )

    if "Group_A.setting_bool" in container._widgets:
        widget = container._widgets["Group_A.setting_bool"]
        original_value = settings.Group_A.setting_bool
        widget.value = not original_value
        container._update_settings()
        assert settings.Group_A.setting_bool == (not original_value)

    # Now reset to defaults
    container._reset_to_defaults()
    # Verify settings are back to defaults
    assert (
        settings.Group_A.setting_float
        == settings._grouped_settings["Group_A"]["setting_float"]["default"]
    )
    assert (
        settings.Group_A.setting_bool
        == settings._grouped_settings["Group_A"]["setting_bool"]["default"]
    )


def test_nullable_dynamic_choices_includes_none():
    """Test that dynamic choices with default=null include None as a valid option."""
    container = SettingsContainer()

    widget_key = "Group_A.setting_dynamic_nullable"
    assert (
        widget_key in container._widgets
    ), f"Expected widget {widget_key} to exist"
    widget = container._widgets[widget_key]

    # None should be in the choices
    assert (
        None in widget.choices
    ), f"None should be in choices for nullable dynamic setting, got {widget.choices}"

    # The widget value should be None (matching the YAML value)
    assert widget.value is None


def test_non_nullable_dynamic_choices_excludes_none():
    """Test that dynamic choices with non-null default do NOT include None."""
    container = SettingsContainer()

    widget_key = "Group_A.setting_dynamic"
    assert (
        widget_key in container._widgets
    ), f"Expected widget {widget_key} to exist"
    widget = container._widgets[widget_key]

    # None should NOT be in the choices
    assert (
        None not in widget.choices
    ), "None should not be in choices for non-nullable dynamic setting"


def test_reset_nullable_dynamic_to_default():
    """Test that resetting a nullable dynamic setting restores None."""
    settings = get_settings()

    # Verify initial default is None
    assert settings.Group_A.setting_dynamic_nullable is None

    # Change the setting
    settings.Group_A.setting_dynamic_nullable = "some_reader"
    assert settings.Group_A.setting_dynamic_nullable == "some_reader"

    # Reset to defaults
    settings.reset_to_default("setting_dynamic_nullable")

    # Should be None again
    assert settings.Group_A.setting_dynamic_nullable is None
