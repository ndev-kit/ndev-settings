"""Pytest fixtures for ndev-settings tests."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def mock_settings_file_path(tmp_path, monkeypatch, test_data_dir):
    """Mock the settings file path to use test data during tests."""
    from pathlib import Path

    import ndev_settings
    from ndev_settings._settings import Settings

    # Use the existing test_settings.yaml as our mock data
    test_settings_path = tmp_path / "test_ndev_settings.yaml"
    shutil.copy(test_data_dir / "test_settings.yaml", test_settings_path)

    # Store the original Settings class constructor
    original_settings_init = Settings.__init__

    # Get the real default settings file path
    real_settings_path = str(
        Path(ndev_settings.__file__).parent / "ndev_settings.yaml"
    )

    def mock_settings_init(self, settings_file=None):
        """Mock Settings constructor to use test file only when loading the default settings."""
        # Only redirect if this is the default ndev_settings.yaml path
        if settings_file == real_settings_path:
            settings_file = str(test_settings_path)

        # Ensure settings_file is never None
        if settings_file is None:
            settings_file = str(test_settings_path)

        return original_settings_init(self, settings_file)

    # Mock the Settings class constructor
    monkeypatch.setattr(Settings, "__init__", mock_settings_init)

    # Reset singleton before test
    ndev_settings._settings_instance = None

    yield test_settings_path

    # Clean up
    ndev_settings._settings_instance = None


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
def mock_external_contributions(tmp_path, test_data_dir, monkeypatch):
    """Mock entry points that provide external YAML contributions using napari-style resource paths."""

    # Copy external contribution file to temp directory
    external_file = tmp_path / "external_contribution.yaml"
    shutil.copy(test_data_dir / "external_contribution.yaml", external_file)

    class MockEntryPoint:
        def __init__(self, name, package_name, resource_name, resource_path):
            self.name = name
            self.value = f"{package_name}:{resource_name}"
            self._resource_path = resource_path

    def mock_entry_points(group=None):
        if group == "ndev_settings.manifest":
            return [
                MockEntryPoint(
                    "test_external",
                    "mock_package",
                    "settings.yaml",
                    external_file,
                )
            ]
        return []

    # Mock importlib.resources.files to return our test file
    def mock_files(package_name):
        if package_name == "mock_package":

            class MockPath:
                def __truediv__(self, resource_name):
                    if resource_name == "settings.yaml":
                        return external_file
                    return tmp_path / resource_name

            return MockPath()
        raise ImportError(f"No module named '{package_name}'")

    # Apply the patches
    monkeypatch.setattr(
        "ndev_settings._settings.entry_points", mock_entry_points
    )
    monkeypatch.setattr("importlib.resources.files", mock_files)

    return external_file
