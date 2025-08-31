from importlib.metadata import entry_points

from magicclass.widgets import GroupBoxContainer
from magicgui.widgets import (
    CheckBox,
    ComboBox,
    Container,
    FloatSpinBox,
    TupleEdit,
    Widget,
)

from ndev_settings._settings import get_settings


class SettingsContainer(Container):
    def __init__(self):
        super().__init__(labels=False)
        self.settings = get_settings()
        self._widgets = {}  # Store references to dynamically created widgets
        self._init_widgets()
        self._connect_events()

    def _get_available_readers(self):
        """Get available bioio readers."""
        readers = [reader.name for reader in entry_points(group="bioio.readers")]
        return readers if readers else ["No readers found"]

    def _create_widget_for_setting(self, name: str, info: dict) -> Widget | None:
        """Create appropriate widget for a setting based on its metadata."""
        default_value = getattr(self.settings, name)
        description = info.get("description", "")

        # Handle special cases first
        if name == "PREFERRED_READER":
            available_readers = self._get_available_readers()
            readers_available = available_readers != ["No readers found"]
            current_value = default_value if default_value in available_readers else available_readers[0]

            return ComboBox(
                label="Preferred Reader",
                value=current_value,
                choices=available_readers,
                tooltip=f"{description}\nIf the reader is not available, it will attempt to fallback to the next available working reader.",
                enabled=readers_available,
            )

        # Handle by type and metadata
        if "choices" in info:
            return ComboBox(
                label=name.replace("_", " ").title(),
                value=default_value,
                choices=info["choices"],
                tooltip=description,
            )
        elif isinstance(default_value, bool):
            return CheckBox(
                label=name.replace("_", " ").title(),
                value=default_value,
                tooltip=description,
            )
        elif isinstance(default_value, int | float):
            return FloatSpinBox(
                label=name.replace("_", " ").title(),
                value=float(default_value),
                min=info.get("min", 0.0),
                max=info.get("max", 1000.0),
                step=info.get("step", 1.0),
                tooltip=description,
            )
        elif isinstance(default_value, tuple | list):
            # Convert list to tuple if needed for consistency
            tuple_value = tuple(default_value) if isinstance(default_value, list) else default_value
            return TupleEdit(
                label=name.replace("_", " ").title(),
                value=tuple_value,
                tooltip=description,
            )

        # Fallback for other types - could be extended
        return None

    def _group_settings(self) -> dict:
        """Group settings by category for organization."""
        groups = {
            "Reader Settings": [
                "PREFERRED_READER",
                "SCENE_HANDLING",
                "CLEAR_LAYERS_ON_NEW_SCENE",
                "UNPACK_CHANNELS_AS_LAYERS"
            ],
            "Export Settings": [
                "CANVAS_SCALE",
                "OVERRIDE_CANVAS_SIZE",
                "CANVAS_SIZE"
            ],
        }

        # Handle any settings not in predefined groups
        all_settings = set(self.settings.get_all_settings().keys())
        grouped_settings = set()
        for group_settings in groups.values():
            grouped_settings.update(group_settings)

        ungrouped = all_settings - grouped_settings
        if ungrouped:
            groups["Other Settings"] = list(ungrouped)

        return groups

    def _init_widgets(self):
        """Initialize all widgets dynamically based on registered settings."""
        groups = self._group_settings()
        containers = []

        for group_name, setting_names in groups.items():
            group_widgets = []

            for setting_name in setting_names:
                if hasattr(self.settings, setting_name):
                    setting_info = self.settings.get_setting_info(setting_name)
                    widget = self._create_widget_for_setting(setting_name, setting_info)

                    if widget:
                        self._widgets[setting_name] = widget
                        group_widgets.append(widget)

            if group_widgets:
                container = GroupBoxContainer(
                    name=group_name,
                    widgets=group_widgets,
                    layout="vertical",
                )
                containers.append(container)

        self.extend(containers)
        self.native.layout().addStretch()

    def _connect_events(self):
        """Connect all widget events to the update handler."""
        for widget in self._widgets.values():
            widget.changed.connect(self._update_settings)

    def _update_settings(self):
        """Update settings when any widget value changes."""
        for setting_name, widget in self._widgets.items():
            # Handle special case for PREFERRED_READER availability
            if setting_name == "PREFERRED_READER" and not widget.enabled:
                continue

            # Auto-save happens automatically via __setattr__
            setattr(self.settings, setting_name, widget.value)
