# IMP_9WORKFLOW Import Extension

This folder contains a Blender 5.0 extension for importing an EX_9WORKFLOW exported scene folder.

## Structure

- `__init__.py` - Blender add-on registration
- `operators.py` - import operator implementation
- `blender_manifest.toml` - Blender extension manifest

## Installation

1. Install Blender 5.0 or newer.
2. Compress the `BLENDER/` folder into a ZIP archive, or directly use the folder if your Blender version supports local folder install.
3. Install the extension via `Edit > Preferences > Add-ons > Install...` and select the archive or folder from local disk.
4. Enable the add-on.
5. Use `Import UE5 Scene` from the search menu or `File > Import`.

## Usage

1. Select the exported UE5 folder containing `scene.usd` and `manifest.json`.
2. Run the import operator.
3. The add-on will import `scene.usd` if present, otherwise fall back to `scene.fbx`.
4. Scene frame range and FPS are set from the manifest.
5. If camera cut metadata is available, timeline markers are created for the cuts.

## Notes

- This tool expects `scene.usd` and `manifest.json` in the selected folder.
- USD import is the recommended path for sequencer export data.
- Imported objects are placed into a new collection named after the UE sequence.
- If `scene.usd` is not found, the importer will attempt to load `scene.fbx` as fallback.
