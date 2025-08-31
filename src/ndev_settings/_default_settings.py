"""Default settings definitions for nDev."""

# Define all default settings with their metadata
DEFAULT_SETTINGS = {
    "PREFERRED_READER": {
        "default": "bioio-ome-tiff",
        "description": "Preferred reader to use when opening images",
    },
    "SCENE_HANDLING": {
        "default": "Open Scene Widget",
        "description": "How to handle files with multiple scenes",
        "choices": ["Open Scene Widget", "View All Scenes", "View First Scene Only"],
    },
    "CLEAR_LAYERS_ON_NEW_SCENE": {
        "default": False,
        "description": "Whether to clear the viewer when selecting a new scene",
    },
    "UNPACK_CHANNELS_AS_LAYERS": {
        "default": True,
        "description": "Whether to unpack channels as layers",
    },
    "CANVAS_SCALE": {
        "default": 1.0,
        "description": "Scales exported figures and screenshots by this value",
        "min": 0.1,
        "max": 100.0,
    },
    "OVERRIDE_CANVAS_SIZE": {
        "default": False,
        "description": "Whether to override the canvas size when exporting canvas screenshot",
    },
    "CANVAS_SIZE": {
        "default": (1024, 1024),
        "description": "Height x width of the canvas when exporting a screenshot",
    },
}
