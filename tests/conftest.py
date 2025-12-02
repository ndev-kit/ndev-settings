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
    3. Entry points (to prevent external packages from contributing settings)

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

    # Mock entry_points to return empty list (isolate from external packages)
    from importlib.metadata import EntryPoints

    monkeypatch.setattr(
        _settings,
        "entry_points",
        lambda group: EntryPoints([]),
    )

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
            self._package_name = package_name
            self._resource_name = resource_name

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

    # Mock distribution() to return our test file path
    class MockPackagePath:
        def __init__(self, package_name, resource_name, actual_path):
            self._path = actual_path
            self.name = resource_name  # This is what file.name returns
            self._package_name = package_name

        def __str__(self):
            # Return something like "mock_package/settings.yaml"
            # so package_name is in str(file)
            return f"{self._package_name}/{self.name}"

    class MockDistribution:
        def __init__(self, package_name, resource_name, resource_path):
            self._package_name = package_name
            self._resource_path = resource_path
            # Create a mock files list with proper name and str representation
            self.files = [
                MockPackagePath(package_name, resource_name, resource_path)
            ]

        def locate_file(self, file):
            if hasattr(file, "_path"):
                return file._path
            # For editable install fallback
            return self._resource_path.parent

    from importlib.metadata import distribution as orig_dist

    def mock_distribution(package_name):
        if package_name == "mock_package":
            return MockDistribution(
                package_name, "settings.yaml", external_file
            )
        return orig_dist(package_name)

    # Apply the patches
    monkeypatch.setattr(
        "ndev_settings._settings.entry_points", mock_entry_points
    )
    monkeypatch.setattr("importlib.metadata.distribution", mock_distribution)

    return external_file
