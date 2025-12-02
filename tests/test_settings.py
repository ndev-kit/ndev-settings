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

    def test_cached_load_uses_saved_file(
        self, test_settings_file, monkeypatch
    ):
        """Test that second load uses cached settings file, not _load_defaults."""
        # First load - discovers from files and saves
        settings1 = Settings(str(test_settings_file))

        # Track if _load_defaults is called on second load
        load_defaults_called = False
        original_load_defaults = Settings._load_defaults

        def tracking_load_defaults(self):
            nonlocal load_defaults_called
            load_defaults_called = True
            return original_load_defaults(self)

        monkeypatch.setattr(Settings, "_load_defaults", tracking_load_defaults)

        # Second load - should use cached file, not call _load_defaults
        settings2 = Settings(str(test_settings_file))

        # Both should have same values
        assert settings1.Group_A.setting_int == settings2.Group_A.setting_int
        assert settings2._grouped_settings is not None

        # _load_defaults should NOT have been called (cache was used)
        assert (
            not load_defaults_called
        ), "Expected cached path, but _load_defaults was called"


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

        # Mock multiple entry points
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

        # Mock distribution() to return our test files
        class MockPackagePath:
            def __init__(self, package_name, resource_name, actual_path):
                self._path = actual_path
                self.name = resource_name
                self._package_name = package_name

            def __str__(self):
                return f"{self._package_name}/{self.name}"

        class MockDistribution:
            def __init__(self, package_name, resource_name, resource_path):
                self._package_name = package_name
                self._resource_path = resource_path
                self.files = [
                    MockPackagePath(package_name, resource_name, resource_path)
                ]

            def locate_file(self, file):
                if hasattr(file, "_path"):
                    return file._path
                return self._resource_path.parent

        from importlib.metadata import distribution as orig_dist

        def mock_distribution(package_name):
            if package_name == "mock_package1":
                return MockDistribution(
                    package_name, "settings.yaml", external1_file
                )
            elif package_name == "mock_package2":
                return MockDistribution(
                    package_name, "settings.yaml", external2_file
                )
            return orig_dist(package_name)

        # Apply patches
        monkeypatch.setattr(
            "ndev_settings._settings.entry_points", mock_entry_points
        )
        monkeypatch.setattr(
            "importlib.metadata.distribution", mock_distribution
        )

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


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_build_groups_skips_metadata_keys(self, test_settings_file):
        """Test that _build_groups skips underscore-prefixed keys."""
        settings = Settings(str(test_settings_file))

        # Manually call _build_groups with settings containing metadata
        settings_with_metadata = {
            "_entry_points_hash": "abc123",
            "_other_metadata": {"some": "data"},
            "ValidGroup": {"setting1": {"value": 10, "default": 10}},
        }

        # Clear existing groups and rebuild
        settings._build_groups(settings_with_metadata)

        # Should have ValidGroup but not metadata keys as attributes
        assert hasattr(settings, "ValidGroup")
        assert not hasattr(settings, "_entry_points_hash")
        assert not hasattr(settings, "_other_metadata")

    def test_save_failure_logs_warning(
        self, test_settings_file, monkeypatch, caplog
    ):
        """Test that save failures are logged as warnings."""
        import logging

        settings = Settings(str(test_settings_file))

        # Mock yaml.dump to raise when trying to save
        def failing_dump(*args, **kwargs):
            raise OSError("Cannot write to file")

        monkeypatch.setattr("yaml.dump", failing_dump)

        # Should not raise, but should log
        with caplog.at_level(logging.WARNING):
            settings._save_settings(settings._grouped_settings)

        assert "Failed to save settings" in caplog.text

    def test_editable_install_detection(
        self, test_settings_file, tmp_path, monkeypatch
    ):
        """Test that editable installs are detected via direct_url.json."""
        import json

        from ndev_settings import _settings

        # Create a mock editable install structure
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        src_package_dir = source_dir / "src" / "mock_package"
        src_package_dir.mkdir(parents=True)
        yaml_file = src_package_dir / "settings.yaml"
        yaml_file.write_text(
            "Editable_Group:\n  setting1:\n    value: 42\n    default: 42\n"
        )

        # Create a mock dist_info with direct_url.json
        dist_info_path = tmp_path / "mock_package-1.0.0.dist-info"
        dist_info_path.mkdir()
        direct_url_file = dist_info_path / "direct_url.json"
        direct_url_file.write_text(
            json.dumps(
                {
                    "url": f"file:///{source_dir.as_posix()}",
                    "dir_info": {"editable": True},
                }
            )
        )

        class MockEntryPoint:
            def __init__(self):
                self.name = "mock_editable"
                self.value = "mock_package:settings.yaml"

        class MockDistribution:
            def __init__(self):
                self._path = dist_info_path
                self.files = []  # Empty files list to trigger fallback

            def locate_file(self, file):
                return tmp_path / "nonexistent"  # Force fallback

        def mock_entry_points(group=None):
            if group == "ndev_settings.manifest":
                return [MockEntryPoint()]
            return []

        def mock_distribution(name):
            if name == "mock_package":
                return MockDistribution()
            from importlib.metadata import distribution

            return distribution(name)

        monkeypatch.setattr(_settings, "entry_points", mock_entry_points)
        monkeypatch.setattr(
            "importlib.metadata.distribution", mock_distribution
        )

        settings = Settings(str(test_settings_file))

        # Should have loaded the editable package's settings
        assert hasattr(settings, "Editable_Group")
        assert settings.Editable_Group.setting1 == 42
