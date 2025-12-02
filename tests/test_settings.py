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

    def test_save_syncs_values(self, test_settings_file):
        """Test that save() syncs group values to internal dict."""
        settings = Settings(str(test_settings_file))

        # Modify some settings via group objects
        settings.Group_A.setting_int = 555
        settings.Group_A.setting_string = "Saved text"

        # Before save, _grouped_settings should still have old values
        assert (
            settings._grouped_settings["Group_A"]["setting_int"]["value"]
            != 555
        )

        # Save syncs values
        settings.save()

        # Now internal dict should be updated
        assert (
            settings._grouped_settings["Group_A"]["setting_int"]["value"]
            == 555
        )
        assert (
            settings._grouped_settings["Group_A"]["setting_string"]["value"]
            == "Saved text"
        )

    def test_save_persists_across_instances(self, test_settings_file):
        """Test that saved settings are loaded by new instances."""
        settings1 = Settings(str(test_settings_file))

        # Modify and save
        settings1.Group_A.setting_int = 999
        settings1.save()

        # Create new instance - should load saved value
        settings2 = Settings(str(test_settings_file))
        assert settings2.Group_A.setting_int == 999

    def test_cached_load_is_faster(self, test_settings_file):
        """Test that second load uses cached settings."""
        import time

        # First load - discovers from files
        start = time.perf_counter()
        settings1 = Settings(str(test_settings_file))
        first_load_time = time.perf_counter() - start

        # Second load - should use cached file
        start = time.perf_counter()
        settings2 = Settings(str(test_settings_file))
        second_load_time = time.perf_counter() - start

        # Both should have same values
        assert settings1.Group_A.setting_int == settings2.Group_A.setting_int

        # Second load should be faster (or at least not slower)
        # Note: On fast systems both may be very fast, so we just check it works
        assert second_load_time <= first_load_time
        assert settings2._grouped_settings is not None


class TestCachingBehavior:
    """Test settings caching and persistence behavior."""

    def test_clear_settings_forces_rediscovery(self, test_settings_file):
        """Test that clear_settings() forces re-discovery from defaults."""
        from ndev_settings import _settings

        settings1 = Settings(str(test_settings_file))
        settings1.Group_A.setting_int = 888
        settings1.save()

        # Clear settings
        _settings.clear_settings()

        # New instance should have default values
        settings2 = Settings(str(test_settings_file))
        assert (
            settings2.Group_A.setting_int == 49
        )  # default from test_settings.yaml

    def test_package_change_preserves_user_values(
        self, test_settings_file, monkeypatch
    ):
        """Test that when packages change, user values are preserved."""
        from ndev_settings import _settings

        # First load and save custom values
        settings1 = Settings(str(test_settings_file))
        settings1.Group_A.setting_int = 777
        settings1.save()

        # Simulate a package change by modifying the hash function
        _ = _settings._get_entry_points_hash()
        monkeypatch.setattr(
            _settings, "_get_entry_points_hash", lambda: "different_hash"
        )

        # New instance should merge: new defaults + saved user values
        settings2 = Settings(str(test_settings_file))

        # User's custom value should be preserved
        assert settings2.Group_A.setting_int == 777

    def test_clear_settings_handles_missing_file(self):
        """Test that clear_settings doesn't crash if file doesn't exist."""
        from ndev_settings import _settings

        # This should not raise even if file doesn't exist
        _settings.clear_settings()


class TestDynamicChoices:
    """Test dynamic choices functionality."""

    def test_dynamic_choices_handling(self, test_settings_file):
        """Test that dynamic choices settings work correctly."""
        settings = Settings(str(test_settings_file))

        # Test the dynamic choices method
        choices = settings.get_dynamic_choices("bioio.readers")

        # Should return a list (even if empty)
        assert isinstance(choices, list)

        # Test with invalid provider
        empty_choices = settings.get_dynamic_choices("invalid.provider")
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

    def test_external_adds_new_setting_to_existing_group(
        self, test_settings_file, mock_external_contributions
    ):
        """Test that external contributions can add new settings to existing groups."""
        settings = Settings(str(test_settings_file))

        # Group_A exists in main file, but external file adds a new setting to it
        assert hasattr(settings.Group_A, "external_only_setting")
        assert settings.Group_A.external_only_setting == "added by external"

    def test_external_settings_can_be_modified(
        self, test_settings_file, mock_external_contributions
    ):
        """Test that external settings can be modified via group objects."""
        settings = Settings(str(test_settings_file))

        # Modify external setting via group object
        settings.External_Contribution.setting_int = 999

        # Save syncs the value to internal dict
        settings.save()

        # Verify the internal dict was updated
        assert (
            settings._grouped_settings["External_Contribution"]["setting_int"][
                "value"
            ]
            == 999
        )

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

        # Mock multiple entry points using napari-style resource paths
        class MockEntryPoint:
            def __init__(
                self, name, package_name, resource_name, resource_path
            ):
                self.name = name
                self.value = f"{package_name}:{resource_name}"
                self._resource_path = resource_path

        def mock_entry_points(group=None):
            if group == "ndev_settings.manifest":
                return [
                    MockEntryPoint(
                        "external1",
                        "mock_package1",
                        "settings.yaml",
                        external1_file,
                    ),
                    MockEntryPoint(
                        "external2",
                        "mock_package2",
                        "settings.yaml",
                        external2_file,
                    ),
                ]
            return []

        # Mock importlib.resources.files to return our test files
        def mock_files(package_name):
            class MockPath:
                def __truediv__(self, resource_name):
                    if (
                        package_name == "mock_package1"
                        and resource_name == "settings.yaml"
                    ):
                        return external1_file
                    elif (
                        package_name == "mock_package2"
                        and resource_name == "settings.yaml"
                    ):
                        return external2_file
                    return tmp_path / resource_name

            return MockPath()

        # Apply patches
        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )
        monkeypatch.setattr("importlib.resources.files", mock_files)

        # Load settings
        settings = Settings(str(test_settings_file))

        # Should have the shared group
        assert hasattr(settings, "Shared_Group")

        # First external contribution wins for overlapping settings (stable, predictable)
        # This prevents unpredictable behavior based on package load order
        assert settings.Shared_Group.shared_setting == "from_external1"

        # Unique settings from later externals should still be added
        assert settings.Shared_Group.unique_setting == "unique_to_external2"


class TestErrorHandling:
    """Test error handling for various edge cases."""

    def test_missing_file_handling(self, empty_settings_file, monkeypatch):
        """Test that missing files are handled gracefully."""

        # Mock entry points to return empty list (no external contributions)
        def mock_entry_points(group=None):
            return []

        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )

        settings = Settings(str(empty_settings_file))

        # Should create empty settings without crashing
        assert hasattr(settings, "_grouped_settings")
        assert settings._grouped_settings == {}

    def test_broken_external_entry_point(
        self, test_settings_file, monkeypatch
    ):
        """Test that broken external entry points don't crash the system."""

        class MockEntryPoint:
            def __init__(self, name, value):
                self.name = name
                self.value = value  # This will cause import error

        def mock_entry_points(group=None):
            if group == "ndev_settings.manifest":
                # Create an entry point with a non-existent package
                return [
                    MockEntryPoint(
                        "broken", "nonexistent_package:settings.yaml"
                    )
                ]
            return []

        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )

        # Should not crash
        settings = Settings(str(test_settings_file))

        # Should still have main settings
        assert hasattr(settings, "Group_A")
        assert settings.Group_A.setting_int == 49


def test_dynamic_choices(empty_settings_file):
    """Test that dynamic choices method exists and doesn't crash."""
    settings = Settings(
        str(empty_settings_file)
    )  # Create without calling __init__

    # Test the method exists and handles missing entry points gracefully
    choices = settings.get_dynamic_choices("nonexistent.entry.point")
    assert isinstance(choices, list)
    assert len(choices) == 0  # Should return empty list when no entries found
