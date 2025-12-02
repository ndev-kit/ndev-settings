from magicclass.widgets import GroupBoxContainer
from magicgui.widgets import Container, PushButton, Widget, create_widget

from ndev_settings import get_settings


class SettingsContainer(Container):
    def __init__(self):
        super().__init__(labels=False)
        self.settings = get_settings()
        self._widgets = {}  # Store references to dynamically created widgets
        self._init_widgets()
        self._connect_events()

    def _get_dynamic_choices(self, setting_info: dict) -> tuple[list, str]:
        """Get dynamic choices for a setting if configured."""
        dynamic_config = setting_info["dynamic_choices"]

        provider = dynamic_config.get("provider", "")
        fallback_message = dynamic_config.get(
            "fallback_message", "No choices available"
        )

        choices = self.settings.get_dynamic_choices(provider)
        return choices if choices else [fallback_message], fallback_message

    def _create_widget_for_setting(
        self, group_obj, name: str, info: dict
    ) -> Widget | None:
        """Create appropriate widget for a setting based on its metadata."""
        init_value = getattr(group_obj, name)
        label = name.replace("_", " ").title()

        # Separate create_widget args from widget options
        create_widget_args = {
            "value": init_value,
            "label": label,
            "widget_type": "ComboBox" if "dynamic_choices" in info else None,
        }

        # Widget options (things that get passed to the widget constructor)
        widget_options = {}

        # Add YAML parameters, separating create_widget args from widget options
        for key, value in info.items():
            if key in ["default", "value", "tooltip", "dynamic_choices"]:
                continue
            widget_options[key] = value

        # Handle dynamic choices
        if "dynamic_choices" in info:
            choices, fallback_message = self._get_dynamic_choices(info)
            choices_available = choices != [fallback_message]
            current_value = init_value if init_value in choices else choices[0]

            create_widget_args["value"] = current_value
            widget_options.update(
                {"choices": choices, "enabled": choices_available}
            )

        # Pass options as a single parameter if we have any
        if widget_options:
            create_widget_args["options"] = widget_options

        return create_widget(**create_widget_args)

    def _init_widgets(self):
        """Initialize all widgets dynamically based on registered settings."""
        groups = self.settings._grouped_settings
        containers = []

        for group_name, settings_dict in groups.items():
            group_widgets = []
            group_obj = getattr(
                self.settings, group_name
            )  # Assume group always exists

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

        self._reset_button = PushButton(text="Reset to Defaults")
        self.append(self._reset_button)

    def _connect_events(self):
        """Connect all widget events to the update handler."""
        for widget in self._widgets.values():
            widget.changed.connect(self._update_settings)

        self._reset_button.clicked.connect(self._reset_to_defaults)

    def _update_settings(self):
        """Update settings when any widget value changes."""
        for key, widget in self._widgets.items():
            # key is now "Group.Setting"
            group_name, setting_name = key.split(".", 1)
            group_obj = getattr(
                self.settings, group_name
            )  # Assume group always exists

            if hasattr(widget, "enabled") and not widget.enabled:
                continue
            setattr(group_obj, setting_name, widget.value)

        # Save all changes to file after updating all widgets
        self.settings.save()

    def _reset_to_defaults(self):
        """Reset all settings to their default values."""
        self.settings.reset_to_default()

        self.clear()  # clear the widgets inside the container
        self._widgets.clear()  # clear the stored widget references

        self._init_widgets()
        self._connect_events()
