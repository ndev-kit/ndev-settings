"""Tests for external library integration via entry points."""
from ndev_settings._settings import Settings


def test_external_yaml_loading(main_with_external_settings):
    """Test that external YAML files are loaded via entry points."""
    settings = Settings(str(main_with_external_settings))

    # Test main settings are loaded
    assert hasattr(settings, "Reader")
    assert hasattr(settings, "Canvas")
    assert settings.Reader.preferred_reader == "test-reader"

    # Test external settings are loaded
    assert hasattr(settings, "BioioOmeZarr")
    assert hasattr(settings, "Microscopy")

    # Test bioio-ome-zarr settings
    assert settings.BioioOmeZarr.chunk_size == [1024, 1024]
    assert settings.BioioOmeZarr.compression == "lz4"
    assert settings.BioioOmeZarr.parallel_read is True

    # Test microscopy settings
    assert settings.Microscopy.objective_correction is True
    assert settings.Microscopy.pixel_size_um == 0.1
    assert settings.Microscopy.illumination_correction == "flatfield"


def test_main_settings_take_precedence(tmp_path, test_data_dir, mock_entry_point_yaml):
    """Test that main settings file takes precedence over external settings."""
    # Create a main settings file that conflicts with external settings
    import yaml
    main_data = {
        "Canvas": {
            "canvas_scale": {
                "value": 3.0,  # Different from default
                "default": 1.0,
                "description": "Main file canvas scale",
            }
        },
        # Add a setting that also exists in external (hypothetical)
        "BioioOmeZarr": {
            "compression": {
                "value": "gzip",  # Different from external
                "default": "blosc",
                "description": "Main file compression override",
            }
        }
    }

    main_file = tmp_path / "main_with_conflicts.yaml"
    main_file.write_text(yaml.dump(main_data))

    settings = Settings(str(main_file))

    # Main file should take precedence
    assert settings.Canvas.canvas_scale == 3.0
    assert settings.BioioOmeZarr.compression == "gzip"  # Main file wins

    # But other external settings should still be loaded
    assert settings.BioioOmeZarr.chunk_size == [1024, 1024]  # From external
    assert settings.Microscopy.objective_correction is True  # From external


def test_external_settings_save_behavior(main_with_external_settings):
    """Test that external settings can be modified and saved."""
    settings = Settings(str(main_with_external_settings))

    # Modify an external setting
    settings.BioioOmeZarr.chunk_size = [2048, 2048]

    # Save and reload
    settings.save()
    settings2 = Settings(str(main_with_external_settings))

    # Should preserve the change
    assert settings2.BioioOmeZarr.chunk_size == [2048, 2048]

    # But other external settings should remain unchanged
    assert settings2.BioioOmeZarr.compression == "lz4"
    assert settings2.Microscopy.objective_correction is True


def test_external_settings_reset(main_with_external_settings):
    """Test that external settings can be reset to defaults."""
    settings = Settings(str(main_with_external_settings))

    # Modify some external settings
    settings.BioioOmeZarr.compression = "gzip"
    settings.Microscopy.pixel_size_um = 0.5

    # Reset external group
    settings.reset_to_default(group="BioioOmeZarr")

    # BioioOmeZarr should be reset
    assert settings.BioioOmeZarr.compression == "blosc"  # Back to default
    assert settings.BioioOmeZarr.chunk_size == [512, 512]  # Back to default

    # But Microscopy should remain modified
    assert settings.Microscopy.pixel_size_um == 0.5

    # Reset specific external setting
    settings.reset_to_default("pixel_size_um")
    assert settings.Microscopy.pixel_size_um == 1.0  # Back to default


def test_missing_external_yaml_graceful_handling(tmp_path, monkeypatch):
    """Test that missing external YAML files are handled gracefully."""
    # Mock entry points that return non-existent files
    def broken_yaml_provider():
        return "/path/to/nonexistent.yaml"

    class MockEntryPoint:
        def __init__(self, name, load_func):
            self.name = name
            self._load_func = load_func

        def load(self):
            return self._load_func

    def mock_entry_points(group=None):
        if group == "ndev_settings.yaml_providers":
            return [MockEntryPoint("broken", broken_yaml_provider)]
        return []

    monkeypatch.setattr("ndev_settings._settings.entry_points", mock_entry_points)

    # Create main settings file
    main_file = tmp_path / "main_settings.yaml"
    main_file.write_text("Canvas:\n  canvas_scale:\n    value: 1.0\n    default: 1.0\n    description: 'Test'")

    # Should not crash with missing external files
    settings = Settings(str(main_file))
    assert hasattr(settings, "Canvas")
    assert settings.Canvas.canvas_scale == 1.0


def test_broken_entry_point_graceful_handling(tmp_path, monkeypatch):
    """Test that broken entry points are handled gracefully."""
    # Mock entry points that raise exceptions
    def broken_entry_point():
        raise ImportError("Broken entry point")

    class MockEntryPoint:
        def __init__(self, name, load_func):
            self.name = name
            self._load_func = load_func

        def load(self):
            return self._load_func

    def mock_entry_points(group=None):
        if group == "ndev_settings.yaml_providers":
            return [MockEntryPoint("broken", broken_entry_point)]
        return []

    monkeypatch.setattr("ndev_settings._settings.entry_points", mock_entry_points)

    # Create main settings file
    main_file = tmp_path / "main_settings.yaml"
    main_file.write_text("Canvas:\n  canvas_scale:\n    value: 1.0\n    default: 1.0\n    description: 'Test'")

    # Should not crash with broken entry points
    settings = Settings(str(main_file))
    assert hasattr(settings, "Canvas")
    assert settings.Canvas.canvas_scale == 1.0
