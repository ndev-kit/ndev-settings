from ndev_settings._settings import get_settings
from ndev_settings._settings_widget import SettingsContainer


def test_settings_container():
    container = SettingsContainer()
    settings_singleton = get_settings()
    original_reader = settings_singleton.PREFERRED_READER

    assert container.settings is settings_singleton
    # TODO: mock entry points to test actual readers
    assert "No readers found" in container._available_readers
    assert container._preferred_reader in container._available_readers
    assert (
        container._scene_handling_combo.value
        == settings_singleton.SCENE_HANDLING
    )
    assert (
        container._clear_on_scene_select_checkbox.value
        == settings_singleton.CLEAR_LAYERS_ON_NEW_SCENE
    )
    assert (
        container._unpack_channels_as_layers_checkbox.value
        == settings_singleton.UNPACK_CHANNELS_AS_LAYERS
    )

    # then, change a value and check that the settings singleton is updated
    # container._preferred_reader_combo.value = (
    #     "bioio-imageio"  # should also be in defaults
    # )
    # assert settings_singleton.PREFERRED_READER == "bioio-imageio"

    # now switch back to the original value, so to not mess up the users settings
    if original_reader in container._preferred_reader_combo.choices:
        container._preferred_reader_combo.value = original_reader
    else:
        # If no readers are found, ComboBox only contains 'No readers found'
        assert container._preferred_reader_combo.value == "No readers found"
