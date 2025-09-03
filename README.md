# ndev-settings

[![License BSD-3](https://img.shields.io/pypi/l/ndev-settings.svg?color=green)](https://github.com/ndev-kit/ndev-settings/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/ndev-settings.svg?color=green)](https://pypi.org/project/ndev-settings)
[![Python Version](https://img.shields.io/pypi/pyversions/ndev-settings.svg?color=green)](https://python.org)
[![tests](https://github.com/ndev-kit/ndev-settings/workflows/tests/badge.svg)](https://github.com/ndev-kit/ndev-settings/actions)
[![codecov](https://codecov.io/gh/ndev-kit/ndev-settings/branch/main/graph/badge.svg)](https://codecov.io/gh/ndev-kit/ndev-settings)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/ndev-settings)](https://napari-hub.org/plugins/ndev-settings)
[![npe2](https://img.shields.io/badge/plugin-npe2-blue?link=https://napari.org/stable/plugins/index.html)](https://napari.org/stable/plugins/index.html)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)

Reusable settings and customization widget for the ndev-kit

----------------------------------

This [napari] plugin was generated with [copier] using the [napari-plugin-template] (None).

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

You can install `ndev-settings` via [pip]:

```
pip install ndev-settings
```

If napari is not already installed, you can install `ndev-settings` with napari and Qt via:

```
pip install "ndev-settings[all]"
```


To install latest development version :

```
pip install git+https://github.com/ndev-kit/ndev-settings.git
```

## Use with external libraries

External libraries can provide their settings in YAML format with the same structure as your main `ndev_settings.yaml`.

**Step 1**: Create a YAML file in the external library (e.g., `ndevio_settings.yaml`):

```yaml
ndevio_Reader:
  preferred_reader:
    default: bioio-ome-tiff
    dynamic_choices:
      fallback_message: No readers found
      provider: bioio.readers
    tooltip: Preferred reader to use when opening images
    value: bioio-ome-tiff
  scene_handling:
    choices:
    - Open Scene Widget
    - View All Scenes
    - View First Scene Only
    default: Open Scene Widget
    tooltip: How to handle files with multiple scenes
    value: View First Scene Only
  clear_layers_on_new_scene:
    default: false
    tooltip: Whether to clear the viewer when selecting a new scene
    value: false

ndevio_Export:
  canvas_scale:
    default: 1.0
    max: 100.0
    min: 0.1
    tooltip: Scales exported figures and screenshots by this value
    value: 1.0
  override_canvas_size:
    default: false
    tooltip: Whether to override the canvas size when exporting canvas screenshot
    value: false
  canvas_size:
    default: !!python/tuple
    - 1024
    - 1024
    tooltip: Height x width of the canvas when exporting a screenshot
    value: !!python/tuple
    - 1024
    - 1024
```

**Step 2**: Register the entry point in `pyproject.toml`:

```toml
[project.entry-points."ndev_settings.manifest"]
ndevio = "ndevio:ndev_settings.yaml"
```

## Usage Example

```python
from ndev_settings import get_settings

settings = get_settings()

# Access settings from main file
print(settings.Canvas.canvas_scale)

# Access settings from external libraries (if installed)
print(settings.Reader.preferred_reader)  # From ndevio
print(settings.Export.compression_level)  # From ndevio
```

## Contributing

Contributions are very welcome. Tests can be run with [tox], please ensure
the coverage at least stays the same before you submit a pull request.

## License

Distributed under the terms of the [BSD-3] license,
"ndev-settings" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[copier]: https://copier.readthedocs.io/en/stable/
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[napari-plugin-template]: https://github.com/napari/napari-plugin-template

[file an issue]: https://github.com/ndev-kit/ndev-settings/issues

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
