"""Tests for the Settings class."""

from ndev_settings._settings import Settings


class TestSettingsBasics:
    """Test basic Settings functionality."""

    def test_settings_load_from_file(self, test_settings_file):
        """Test loading settings from a YAML file."""
        settings = Settings(str(test_settings_file))

        # Check groups exist
        assert hasattr(settings, "Group_A")
        assert hasattr(settings, "Group_B")

        # Check some specific settings
        assert settings.Group_A.setting_int == 49
        assert settings.Group_A.setting_choices == "another_option"
        assert settings.Group_A.setting_bool is True

    def test_settings_access_values(self, test_settings_file):
        """Test accessing setting values."""
        settings = Settings(str(test_settings_file))

        # Test various data types
        assert isinstance(settings.Group_A.setting_int, int)
        assert isinstance(settings.Group_A.setting_float, float)
        assert isinstance(settings.Group_A.setting_bool, bool)
        assert isinstance(settings.Group_A.setting_string, str)
        assert isinstance(settings.Group_A.setting_list, list)
        assert isinstance(settings.Group_A.setting_tuple, tuple)

    def test_settings_modify_values(self, test_settings_file):
        """Test modifying setting values."""
        settings = Settings(str(test_settings_file))

        # Modify various settings
        settings.Group_A.setting_int = 100
        settings.Group_A.setting_bool = False
        settings.Group_A.setting_string = "Modified text"

        # Verify changes
        assert settings.Group_A.setting_int == 100
        assert settings.Group_A.setting_bool is False
        assert settings.Group_A.setting_string == "Modified text"


class TestSettingsReset:
    """Test Settings reset functionality."""

    def test_reset_single_setting(self, test_settings_file):
        """Test resetting a single setting to default."""
        settings = Settings(str(test_settings_file))

        # Modify a setting
        settings.Group_A.setting_int = 999
        assert settings.Group_A.setting_int == 999

        # Reset it
        settings.reset_to_default("setting_int")

        # Should be back to default (0, from the YAML)
        assert settings.Group_A.setting_int == 0  # default value from YAML

    def test_reset_all_settings(self, test_settings_file):
        """Test resetting all settings to defaults."""
        settings = Settings(str(test_settings_file))

        # Modify several settings
        settings.Group_A.setting_int = 999
        settings.Group_A.setting_bool = not settings.Group_A.setting_bool
        settings.Group_B.setting_int = 777

        # Reset all
        settings.reset_to_default()

        # Check they're back to defaults
        assert settings.Group_A.setting_int == 0  # default
        assert settings.Group_A.setting_bool is False  # default
        assert settings.Group_B.setting_int == 50  # default

    def test_reset_by_group(self, test_settings_file):
        """Test resetting settings by group."""
        settings = Settings(str(test_settings_file))

        # Modify settings in both groups
        settings.Group_A.setting_int = 999
        settings.Group_B.setting_int = 777

        # Reset only Group_A
        settings.reset_to_default(group="Group_A")

        # Group_A should be reset, Group_B should remain changed
        assert settings.Group_A.setting_int == 0  # reset to default
        assert settings.Group_B.setting_int == 777  # still modified


class TestSettingsSaveLoad:
    """Test Settings save and load functionality."""

    def test_save_and_reload(self, test_settings_file):
        """Test saving changes and reloading them."""
        settings = Settings(str(test_settings_file))

        # Modify some settings
        settings.Group_A.setting_int = 555
        settings.Group_A.setting_string = "Saved text"

        # Save
        settings.save()

        # Create new Settings instance from same file
        settings2 = Settings(str(test_settings_file))

        # Should have saved changes
        assert settings2.Group_A.setting_int == 555
        assert settings2.Group_A.setting_string == "Saved text"


class TestDynamicChoices:
    """Test dynamic choices functionality."""

    def test_dynamic_choices_handling(self, test_settings_file):
        """Test that dynamic choices settings work correctly."""
        settings = Settings(str(test_settings_file))

        # Test the dynamic choices method
        choices = settings._get_dynamic_choices("bioio.readers")

        # Should return a list (even if empty)
        assert isinstance(choices, list)

        # Test with invalid provider
        empty_choices = settings._get_dynamic_choices("invalid.provider")
        assert empty_choices == []


class TestExternalContributions:
    """Test external library contributions via entry points."""

    def test_external_yaml_loading(
        self, test_settings_file, mock_external_contributions
    ):
        """Test that external YAML files are loaded and merged."""
        settings = Settings(str(test_settings_file))

        # Should have main settings
        assert hasattr(settings, "Group_A")
        assert hasattr(settings, "Group_B")

        # Should also have external contributions
        assert hasattr(settings, "External_Contribution")

        # Check external settings values
        assert settings.External_Contribution.setting_int == 10
        assert settings.External_Contribution.setting_choices == "option1"

    def test_main_settings_override_external(
        self, test_settings_file, mock_external_contributions
    ):
        """Test that main settings take precedence over external ones."""
        settings = Settings(str(test_settings_file))

        # Group_A exists in both main and external files
        # Main file should take precedence
        assert (
            settings.Group_A.setting_int == 49
        )  # from main file, not 35 from external
        assert (
            settings.Group_A.setting_choices == "another_option"
        )  # from main file

        # But external-only settings should still be loaded
        assert hasattr(settings, "External_Contribution")
        assert settings.External_Contribution.setting_int == 10

    def test_external_settings_can_be_modified(
        self, test_settings_file, mock_external_contributions
    ):
        """Test that external settings can be modified and saved."""
        settings = Settings(str(test_settings_file))

        # Modify external setting
        settings.External_Contribution.setting_int = 999

        # Save and reload
        settings.save()
        settings2 = Settings(str(test_settings_file))

        # Should preserve the change
        assert settings2.External_Contribution.setting_int == 999

    def test_duplicate_external_contributions_handling(
        self, test_settings_file, tmp_path, monkeypatch
    ):
        """Test what happens when multiple external libraries contribute the same settings."""

        # Create two external files with overlapping settings
        external1_data = {
            "Shared_Group": {
                "shared_setting": {
                    "value": "from_external1",
                    "default": "default1",
                    "tooltip": "From external library 1",
                }
            }
        }

        external2_data = {
            "Shared_Group": {
                "shared_setting": {
                    "value": "from_external2",
                    "default": "default2",
                    "tooltip": "From external library 2",
                },
                "unique_setting": {
                    "value": "unique_to_external2",
                    "default": "unique_default",
                    "tooltip": "Only in external 2",
                },
            }
        }

        # Write external files
        import yaml

        external1_file = tmp_path / "external1.yaml"
        external2_file = tmp_path / "external2.yaml"

        external1_file.write_text(
            yaml.dump(external1_data, default_flow_style=False)
        )
        external2_file.write_text(
            yaml.dump(external2_data, default_flow_style=False)
        )

        # Mock multiple entry points
        def external1_provider():
            return str(external1_file)

        def external2_provider():
            return str(external2_file)

        class MockEntryPoint:
            def __init__(self, name, load_func):
                self.name = name
                self._load_func = load_func

            def load(self):
                return self._load_func

        def mock_entry_points(group=None):
            if group == "ndev_settings.yaml_providers":
                return [
                    MockEntryPoint("external1", external1_provider),
                    MockEntryPoint("external2", external2_provider),
                ]
            return []

        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )

        # Load settings
        settings = Settings(str(test_settings_file))

        # Should have the shared group
        assert hasattr(settings, "Shared_Group")

        # Last external contribution should win (external2)
        # because _load_external_yaml_files uses dict.update() which overwrites existing keys
        assert settings.Shared_Group.shared_setting == "from_external2"

        # But unique settings from later externals should still be added
        assert settings.Shared_Group.unique_setting == "unique_to_external2"


class TestErrorHandling:
    """Test error handling for various edge cases."""

    def test_missing_file_handling(self, empty_settings_file):
        """Test that missing files are handled gracefully."""
        settings = Settings(str(empty_settings_file))

        # Should create empty settings without crashing
        assert hasattr(settings, "_grouped_settings")
        assert settings._grouped_settings == {}

    def test_broken_external_entry_point(
        self, test_settings_file, monkeypatch
    ):
        """Test that broken external entry points don't crash the system."""

        def broken_provider():
            raise ImportError("Broken external library")

        class MockEntryPoint:
            def __init__(self, name, load_func):
                self.name = name
                self._load_func = load_func

            def load(self):
                return self._load_func

        def mock_entry_points(group=None):
            if group == "ndev_settings.yaml_providers":
                return [MockEntryPoint("broken", broken_provider)]
            return []

        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )

        # Should not crash
        settings = Settings(str(test_settings_file))

        # Should still have main settings
        assert hasattr(settings, "Group_A")
        assert settings.Group_A.setting_int == 49


def test_dynamic_choices():
    """Test that dynamic choices method exists and doesn't crash."""
    settings = Settings.__new__(Settings)  # Create without calling __init__

    # Test the method exists and handles missing entry points gracefully
    choices = settings._get_dynamic_choices("nonexistent.entry.point")
    assert isinstance(choices, list)
    assert len(choices) == 0  # Should return empty list when no entries found
