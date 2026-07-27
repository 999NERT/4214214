# Editor Utility Widget helper

This folder contains helper code for an Unreal Editor Utility Widget that drives the EX_9WORKFLOW exporter.

Use `exporter_ui.py` from the widget to:

- list available Level Sequence assets
- list available World/Level assets
- show the selected sequence frame range, FPS, and binding list
- choose which sequence bindings to export
- choose a target export output folder
- run the export and write `scene.usd`, `manifest.json`, and `debug_export.json` into that folder

Example widget flow:

1. Call `get_all_level_sequences()` to populate the sequence picker.
2. Call `get_all_maps()` to populate the level/map picker.
3. When a sequence is selected, call `get_sequence_summary(sequence_path)` and/or `get_sequence_bindings(sequence_path)` to display its contents.
4. Allow the user to select individual `selected_binding_ids` from the binding list.
5. Allow the user to choose `output_dir` in the folder browser.
6. Execute `run_export(sequence_path, output_dir, selected_binding_ids=selected_binding_ids, level_map_path=selected_map_path, reference_data_paths=reference_data_paths)`.

The debug report is written into the same output folder as the exported USD and manifest.
