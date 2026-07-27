# Blender Import Extension

This folder contains a Blender 5.0 extension for importing a UE5 exported scene folder.

## Structure

- `__init__.py` - Blender add-on registration
- `operators.py` - import operator implementation
- `blender_manifest.toml` - Blender extension manifest

## Installation

1. Install Blender 5.0 or newer.
2. Copy the `BLENDER/` folder into Blender's add-ons directory or install it via `Edit > Preferences > Add-ons > Install...`.
3. Enable the add-on.
4. Use `Import UE5 Scene` from the search menu or `File > Import`.

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
