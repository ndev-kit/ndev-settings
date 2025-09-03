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
def test_settings_file(tmp_path, test_data_dir):
    """Create a temporary copy of test_settings.yaml for testing."""
    source = test_data_dir / "test_settings.yaml"
    target = tmp_path / "test_settings.yaml"
    shutil.copy(source, target)
    return target


@pytest.fixture
def external_contribution_file(tmp_path, test_data_dir):
    """Create a temporary copy of external_contribution.yaml for testing."""
    source = test_data_dir / "external_contribution.yaml"
    target = tmp_path / "external_contribution.yaml"
    shutil.copy(source, target)
    return target


@pytest.fixture
def empty_settings_file(tmp_path):
    """Create an empty settings file path (file doesn't exist)."""
    return tmp_path / "nonexistent.yaml"


@pytest.fixture
def minimal_settings_file(tmp_path):
    """Create a minimal settings file for basic testing."""
    data = {
        "TestGroup": {
            "simple_setting": {
                "value": "test_value",
                "default": "default_value",
                "tooltip": "A simple test setting",
            },
            "numeric_setting": {
                "value": 42,
                "default": 0,
                "tooltip": "A numeric test setting",
            },
            "boolean_setting": {
                "value": True,
                "default": False,
                "tooltip": "A boolean test setting",
            },
        },
    }
    file_path = tmp_path / "minimal_settings.yaml"
    file_path.write_text(yaml.dump(data, default_flow_style=False))
    return file_path


@pytest.fixture
def test_group_file(tmp_path):
    """Create a test settings file with TestGroup for widget testing."""
    data = {
        "TestGroup": {
            "test_setting": {
                "value": "test_value",
                "default": "default_value",
                "tooltip": "A test setting",
            },
            "numeric_setting": {
                "value": 42.0,
                "default": 0.0,
                "tooltip": "A numeric test setting",
            },
            "boolean_setting": {
                "value": True,
                "default": False,
                "tooltip": "A boolean test setting",
            },
        },
    }
    file_path = tmp_path / "test_group.yaml"
    file_path.write_text(yaml.dump(data, default_flow_style=False))
    return file_path


@pytest.fixture
def mock_external_contributions(tmp_path, test_data_dir, monkeypatch):
    """Mock entry points that provide external YAML contributions."""

    # Copy external contribution file to temp directory
    external_file = tmp_path / "external_contribution.yaml"
    shutil.copy(test_data_dir / "external_contribution.yaml", external_file)

    def external_yaml_provider():
        return str(external_file)

    class MockEntryPoint:
        def __init__(self, name, load_func):
            self.name = name
            self._load_func = load_func

        def load(self):
            return self._load_func

    def mock_entry_points(group=None):
        if group == "ndev_settings.yaml_providers":
            return [MockEntryPoint("test_external", external_yaml_provider)]
        return []

    # Patch the entry_points function
    monkeypatch.setattr(
        "ndev_settings._settings.entry_points", mock_entry_points
    )

    return external_file
