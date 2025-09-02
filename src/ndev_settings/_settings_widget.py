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

    def _get_dynamic_choices(self, setting_info: dict) -> tuple[list, str]:
        """Get dynamic choices for a setting if configured."""
        dynamic_config = setting_info.get("dynamic_choices")
        if not dynamic_config:
            return [], ""

        provider = dynamic_config.get("provider", "")
        fallback_message = dynamic_config.get(
            "fallback_message", "No choices available"
        )

        choices = self.settings._get_dynamic_choices(provider)
        return choices if choices else [fallback_message], fallback_message


    def _create_widget_for_setting(self, group_obj, name: str, info: dict) -> Widget | None:
        """Create appropriate widget for a setting based on its metadata."""
        default_value = getattr(group_obj, name)
        description = info.get("description", "")

        # Handle dynamic choices first
        if "dynamic_choices" in info:
            choices, fallback_message = self._get_dynamic_choices(info)
            choices_available = choices != [fallback_message]
            current_value = (
                default_value if default_value in choices else choices[0]
            )

            tooltip = description
            if not choices_available:
                tooltip += f"\n{fallback_message}"
            elif "dynamic_choices" in info:
                tooltip += "\nIf the selection is not available, it will attempt to fallback to the next available working option."

            return ComboBox(
                label=name.replace("_", " ").title(),
                value=current_value,
                choices=choices,
                tooltip=tooltip,
                enabled=choices_available,
            )

        # Handle static choices
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
        elif isinstance(default_value, tuple):
            return TupleEdit(
                label=name.replace("_", " ").title(),
                value=default_value,
                tooltip=description,
            )

        return None

    def _group_settings(self) -> dict:
        """Group settings by their defined groups from the YAML file."""
        return self.settings._settings_by_group


    def _init_widgets(self):
        """Initialize all widgets dynamically based on registered settings."""
        groups = self._group_settings()
        containers = []

        for group_name, settings_dict in groups.items():
            group_widgets = []
            group_obj = getattr(self.settings, group_name)  # Assume group always exists

            for setting_name, setting_data in settings_dict.items():
                widget = self._create_widget_for_setting(
                    group_obj, setting_name, setting_data
                )
                if widget:
                    self._widgets[f"{group_name}.{setting_name}"] = widget
                    group_widgets.append(widget)

            if group_widgets:
                container = GroupBoxContainer(
                    name=f"{group_name} Settings",
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
        for key, widget in self._widgets.items():
            # key is now "Group.Setting"
            group_name, setting_name = key.split(".", 1)
            group_obj = getattr(self.settings, group_name)  # Assume group always exists

            if hasattr(widget, "enabled") and not widget.enabled:
                continue
            setattr(group_obj, setting_name, widget.value)
