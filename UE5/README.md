# EX_9WORKFLOW Export Tool

This folder contains the UE5 plugin-side exporter for Level Sequence scene data.

## Structure

- `export_core.py` - core USD/FBX export helper functions
- `metahuman_export.py` - MetaHuman detection and metadata helpers
- `editor_utility_widget/` - placeholder for the Editor Utility Widget asset and configuration
- `manifest_schema.json` - manifest schema for exported scenes

## Installation

1. Copy the `EX_9WORKFLOW/` folder into your Unreal project.
2. Ensure the folder is treated as a Python package by keeping `UE5/__init__.py` in place.
3. Create an Editor Utility Widget that runs Python from the Unreal editor and imports the package as `from UE5.export_core import export_sequence`.
4. Call `export_sequence(sequence, output_dir, export_level=True, export_subsequences_as_layers=True, reference_data_paths=..., selected_binding_ids=[...], level_map_path=...)`.
5. The exporter writes `scene.usd`, `manifest.json` and `debug_export.json` into the target output folder.

## Editor Utility Widget UI helper

Use `UE5/editor_utility_widget/exporter_ui.py` to populate the widget:

- `get_all_level_sequences()` - returns available Level Sequence assets.
- `get_all_maps()` - returns available World/Level assets.
- `get_sequence_bindings(sequence_path)` - returns bindings inside a selected sequence.
- `get_sequence_summary(sequence_path)` - returns frame range, fps, and bindings metadata.
- `run_export(sequence_path, output_dir, selected_binding_ids=None, level_map_path=None, reference_data_paths=None, export_level=True, export_subsequences_as_layers=True)` - executes export and writes debug data into `output_dir`.

Set the export path from the widget and pass it to `run_export`; all debug files will be created in that folder.

## Notes

- `editor_utility_widget/` is a placeholder for the Editor Utility Widget asset and UI config.
- This tool is designed to live separately from the Blender addon.
- USD export is the recommended path for full Sequencer + MetaHuman support.
- The manifest includes sequence playback range, display FPS, exported bindings, camera cuts, MetaHuman actor metadata, and reference data file info.

## Usage Example

```python
import os
from UE5.export_core import export_sequence

sequence = unreal.load_asset('/Game/MySequences/MySequence')
output_dir = r'C:\Temp\ue5_export'
result = export_sequence(
    sequence,
    output_dir,
    reference_data_paths=[r'C:\Path\To\reference_data\metahuman_face_blendshapes.json'],
    selected_binding_ids=None,
    level_map_path='/Game/Maps/MyLevel',
)
print('USD:', result['usd_path'])
print('Manifest:', result['manifest'])
```

## Editor Utility Widget Example

Use `UE5/editor_utility_widget/widget_blueprint_example.py` from a UE5 Python widget or helper function:

```python
from UE5.editor_utility_widget.widget_blueprint_example import (
    widget_get_level_sequences,
    widget_get_maps,
    widget_get_sequence_summary,
    widget_get_sequence_bindings,
    widget_run_export,
)

sequences = widget_get_level_sequences()
maps = widget_get_maps()
sequence_summary = widget_get_sequence_summary('/Game/MySequences/MySequence')
bindings = widget_get_sequence_bindings('/Game/MySequences/MySequence')

result = widget_run_export(
    '/Game/MySequences/MySequence',
    r'C:\Temp\ue5_export',
    selected_binding_ids=[binding['id'] for binding in bindings if binding['name'] == 'MyActor'],
    level_map_path='/Game/Maps/MyLevel',
    reference_data_paths=[r'C:\Path\To\reference_data\metahuman_face_blendshapes.json'],
)
print(result)
```

## Installation Steps for UE5

1. Copy the `EX_9WORKFLOW/` folder into your Unreal project content root or Python script folder.
2. Make sure `UE5/__init__.py` remains in place so Python treats the folder as a package.
3. In Unreal, open `Edit > Editor Preferences > Scripting` and enable Python if needed.
4. Create a new Editor Utility Widget or Python script asset.
5. In the widget, import the helper module:
   - `from UE5.editor_utility_widget.widget_blueprint_example import widget_get_level_sequences, widget_get_maps, widget_get_sequence_summary, widget_get_sequence_bindings, widget_run_export`
6. Build UI logic so the widget can:
   - choose a Level Sequence asset
   - choose a Level/World asset if needed
   - list sequence bindings and allow selection
   - choose an output folder path
   - press export to run `widget_run_export(...)`
7. When export runs, verify that `scene.usd`, `manifest.json`, and `debug_export.json` appear in the selected output folder.

## Notes

- The widget functions are Python helpers only; the actual UI is created in Unreal Editor Utility Widget.
- All debug files are written into the chosen output folder.
- USD export is still the recommended path for full Sequencer + MetaHuman support.
