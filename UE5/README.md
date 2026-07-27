# UE5 Export Tool

This folder contains the UE5 plugin-side exporter for Level Sequence scene data.

## Structure

- `export_core.py` - core USD/FBX export helper functions
- `metahuman_export.py` - MetaHuman detection and metadata helpers
- `editor_utility_widget/` - placeholder for the Editor Utility Widget asset and configuration
- `manifest_schema.json` - manifest schema for exported scenes

## Installation

1. Copy the `UE5/` folder into your Unreal project.
2. Ensure the folder is treated as a Python package by keeping `UE5/__init__.py` in place.
3. Create an Editor Utility Widget that runs Python from the Unreal editor and imports the package as `from UE5.export_core import export_sequence`.
4. Call `export_sequence(sequence, output_dir, export_level=True, export_subsequences_as_layers=True, reference_data_path=...)`.
5. The exporter writes `scene.usd` and `manifest.json` into the target output folder.

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
result = export_sequence(sequence, output_dir, reference_data_path=r'C:\Path\To\reference_data\metahuman_face_blendshapes.json')
print('USD:', result['usd_path'])
print('Manifest:', result['manifest'])
```

## Notes

- This tool is designed to live separately from the Blender addon.
- USD export is the recommended path for full Sequencer + MetaHuman support.
- The manifest includes sequence playback range, display FPS, exported bindings, and MetaHuman actor metadata.
- Use `reference_data_path` to attach MetaHuman bone/blendshape reference JSON into the manifest for downstream Blender validation.
