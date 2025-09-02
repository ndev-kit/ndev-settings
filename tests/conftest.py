"""Pytest fixtures for ndev-settings tests."""
import shutil
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def settings_file(tmp_path, test_data_dir):
    """Create a temporary copy of sample_settings.yaml for testing."""
    source = test_data_dir / "sample_settings.yaml"
    target = tmp_path / "test_settings.yaml"
    shutil.copy(source, target)
    return target


@pytest.fixture
def simple_settings_file(tmp_path, test_data_dir):
    """Create a temporary copy of simple_canvas.yaml for testing."""
    source = test_data_dir / "simple_canvas.yaml"
    target = tmp_path / "test_settings.yaml"
    shutil.copy(source, target)
    return target


@pytest.fixture
def reset_settings_file(tmp_path, test_data_dir):
    """Create a temporary copy of reset_test.yaml for testing."""
    source = test_data_dir / "reset_test.yaml"
    target = tmp_path / "test_settings.yaml"
    shutil.copy(source, target)
    return target


@pytest.fixture
def empty_settings_file(tmp_path):
    """Create an empty settings file path (file doesn't exist)."""
    return tmp_path / "nonexistent.yaml"


@pytest.fixture
def incomplete_settings_file(tmp_path):
    """Create a settings file with incomplete metadata."""
    data = {
        "Canvas": {
            "canvas_scale": {
                "value": 2.0,
                "default": 1.0,
                # Missing description - should handle gracefully
            },
            "incomplete_setting": {
                "value": "test",
                # Missing default and description
            },
        },
    }
    file_path = tmp_path / "incomplete_settings.yaml"
    file_path.write_text(yaml.dump(data))
    return file_path


@pytest.fixture
def test_group_file(tmp_path):
    """Create a settings file with test group data."""
    data = {
        "TestGroup": {
            "test_setting": {
                "value": "test_value",
                "default": "default_value",
                "description": "A test setting",
            },
            "numeric_setting": {
                "value": 42.0,
                "default": 0.0,
                "description": "A numeric test setting",
            },
            "boolean_setting": {
                "value": True,
                "default": False,
                "description": "A boolean test setting",
            },
        },
    }
    file_path = tmp_path / "test_group.yaml"
    file_path.write_text(yaml.dump(data))
    return file_path


# External library testing fixtures
@pytest.fixture
def external_yaml_files(test_data_dir):
    """Return paths to external YAML files for testing."""
    return {
        "bioio_zarr": test_data_dir / "external_bioio_zarr.yaml",
        "microscopy": test_data_dir / "external_microscopy.yaml",
    }


@pytest.fixture
def mock_entry_point_yaml(tmp_path, test_data_dir, monkeypatch):
    """Mock entry points that return YAML file paths."""

    # Copy external YAML files to temp directory
    external_files = {}
    for name in ["external_bioio_zarr.yaml", "external_microscopy.yaml"]:
        source = test_data_dir / name
        target = tmp_path / name
        shutil.copy(source, target)
        external_files[name] = target

    # Mock entry point functions
    def bioio_zarr_yaml_provider():
        return str(external_files["external_bioio_zarr.yaml"])

    def microscopy_yaml_provider():
        return str(external_files["external_microscopy.yaml"])

    # Create mock entry points
    class MockEntryPoint:
        def __init__(self, name, load_func):
            self.name = name
            self._load_func = load_func

        def load(self):
            return self._load_func

    def mock_entry_points(group=None):
        if group == "ndev_settings.yaml_providers":
            return [
                MockEntryPoint("bioio_zarr", bioio_zarr_yaml_provider),
                MockEntryPoint("microscopy", microscopy_yaml_provider),
            ]
        return []

    # Patch the entry_points function
    monkeypatch.setattr("ndev_settings._settings.entry_points", mock_entry_points)

    return external_files


@pytest.fixture
def main_with_external_settings(tmp_path, test_data_dir, mock_entry_point_yaml):
    """Create a main settings file that will be merged with external settings."""
    # Copy the main settings file
    source = test_data_dir / "sample_settings.yaml"
    target = tmp_path / "main_settings.yaml"
    shutil.copy(source, target)
    return target
