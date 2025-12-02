"""Pytest fixtures for ndev-settings tests."""

import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_settings(tmp_path, monkeypatch, test_data_dir):
    """Isolate settings to tmp_path for each test.

    This redirects both:
    1. The settings file location (where user settings are saved)
    2. The defaults file (to use test data instead of real package defaults)

    This allows tests to run with real persistence behavior while being isolated.
    """
    import ndev_settings
    from ndev_settings import _settings
    from ndev_settings._settings import Settings

    # Redirect settings file to tmp_path
    test_settings_dir = tmp_path / "ndev-settings"
    test_settings_file = test_settings_dir / "settings.yaml"
    monkeypatch.setattr(_settings, "_SETTINGS_DIR", test_settings_dir)
    monkeypatch.setattr(_settings, "_SETTINGS_FILE", test_settings_file)

    # Copy test data to use as defaults
    test_defaults_path = tmp_path / "test_defaults.yaml"
    shutil.copy(test_data_dir / "test_settings.yaml", test_defaults_path)

    # Redirect default settings file path
    original_settings_init = Settings.__init__
    real_settings_path = str(
        Path(ndev_settings.__file__).parent / "ndev_settings.yaml"
    )

    def mock_settings_init(self, defaults_file=None):
        """Redirect default settings file to test data."""
        if defaults_file == real_settings_path or defaults_file is None:
            defaults_file = str(test_defaults_path)
        return original_settings_init(self, defaults_file)

    monkeypatch.setattr(Settings, "__init__", mock_settings_init)

    # Reset singleton before each test
    ndev_settings._settings_instance = None

    yield test_defaults_path

    # Clean up singleton after test
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
    """Mock entry points that provide external YAML contributions."""

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
