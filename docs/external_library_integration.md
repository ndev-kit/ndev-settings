# Registering Settings with ndev-settings

External libraries can register their settings with `ndev-settings` using entry points. This provides a clean, discoverable way to extend the settings system without tight coupling.

## Setup

### 1. Add Entry Point to pyproject.toml

In your library's `pyproject.toml`, add an entry point:

```toml
[project.entry-points."ndev_settings.providers"]
your_library = "your_library.ndev_settings:register_settings"
```

### 2. Create Settings Registration Function

Create a module in your library (e.g., `your_library/ndev_settings.py`) with a registration function:

```python
from ndev_settings import SettingDefinition, register_settings, create_dynamic_choice_setting

def register_settings(settings_manager):
    """Register all settings for your library."""
    register_settings(
        settings_manager,

        # Simple boolean setting
        SettingDefinition(
            name="enable_feature",
            default_value=True,
            description="Enable the awesome feature",
            group="Features"
        ),

        # Numeric setting with bounds
        SettingDefinition(
            name="timeout_seconds",
            default_value=30.0,
            description="Timeout for operations (seconds)",
            group="Performance",
            min_value=1.0,
            max_value=300.0,
            step=1.0
        ),

        # Choice setting with static options
        SettingDefinition(
            name="log_level",
            default_value="INFO",
            description="Logging level",
            group="Debug",
            choices=["DEBUG", "INFO", "WARNING", "ERROR"]
        ),

        # Dynamic choice setting from entry points
        create_dynamic_choice_setting(
            name="preferred_backend",
            default_value="default",
            entry_point_group="your_library.backends",
            description="Preferred backend to use",
            group="Performance",
            fallback_message="No backends available"
        ),

        # Tuple setting for coordinates/sizes
        SettingDefinition(
            name="default_size",
            default_value=(1024, 1024),
            description="Default size (width, height)",
            group="Display"
        ),
    )
```

## Setting Types and Metadata

### Boolean Settings
```python
SettingDefinition(
    name="my_boolean",
    default_value=True,
    description="A boolean setting",
    group="MyGroup"
)
```

### Numeric Settings (int/float)
```python
SettingDefinition(
    name="my_number",
    default_value=10.0,
    description="A numeric setting",
    group="MyGroup",
    min_value=0.0,      # Optional minimum
    max_value=100.0,    # Optional maximum
    step=1.0            # Optional step size
)
```

### Choice Settings (Static)
```python
SettingDefinition(
    name="my_choice",
    default_value="option1",
    description="A choice setting",
    group="MyGroup",
    choices=["option1", "option2", "option3"]
)
```

### Dynamic Choice Settings
```python
# Method 1: Using helper function
create_dynamic_choice_setting(
    name="my_dynamic_choice",
    default_value="default",
    entry_point_group="my_library.plugins",
    description="Choose from available plugins",
    group="MyGroup",
    fallback_message="No plugins available"
)

# Method 2: Manual configuration
SettingDefinition(
    name="my_dynamic_choice",
    default_value="default",
    description="Choose from available plugins",
    group="MyGroup",
    dynamic_choices={
        "provider": "my_library.plugins",
        "fallback_message": "No plugins available"
    }
)
```

### Tuple/List Settings
```python
SettingDefinition(
    name="my_tuple",
    default_value=(512, 512),
    description="A tuple setting for dimensions",
    group="MyGroup"
)
```

## Examples

### bioio Integration
```python
# In bioio/ndev_settings.py
def register_bioio_settings(settings_manager):
    register_settings(
        settings_manager,
        create_dynamic_choice_setting(
            name="preferred_reader",
            default_value="bioio-ome-tiff",
            entry_point_group="bioio.readers",
            description="Preferred reader for image files",
            group="Reader"
        )
    )
```

### ndevio Integration
```python
# In ndevio/ndev_settings.py
def register_ndevio_settings(settings_manager):
    register_settings(
        settings_manager,
        create_dynamic_choice_setting(
            name="preferred_writer",
            default_value="ome-tiff",
            entry_point_group="ndevio.writers",
            description="Preferred writer for exports",
            group="Export"
        ),
        SettingDefinition(
            name="compression_enabled",
            default_value=True,
            description="Enable compression for exports",
            group="Export"
        )
    )
```

## Benefits

1. **Clean Discovery**: Settings are automatically discovered when libraries are installed
2. **No Dependencies**: Libraries don't need to directly depend on ndev-settings
3. **Graceful Degradation**: If ndev-settings isn't installed, libraries continue to work
4. **Multiple Settings**: Each entry point can register many related settings
5. **Grouped Organization**: Settings are automatically organized by group
6. **Type Safety**: Rich metadata supports proper UI widget generation
