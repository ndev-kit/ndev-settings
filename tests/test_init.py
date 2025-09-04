from ndev_settings import get_settings


def test_get_settings_singleton():
    """Test the singleton behavior of get_settings."""
    # Get two instances of settings
    settings1 = get_settings()
    settings2 = get_settings()

    # They should be the same object
    assert settings1 is settings2
