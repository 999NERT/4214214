import os
import unreal

from .exporter import export_current_sequence, load_config


def show_export_window():
    """Placeholder UI hook for future editor widget integration."""
    config = load_config()
    output_path = config.get("default_output_folder", "D:/Exports")
    if not output_path:
        output_path = "D:/Exports"
    if not os.path.exists(output_path):
        os.makedirs(output_path, exist_ok=True)

    output_file = os.path.join(output_path, "exported_sequence.fbx")
    result = export_current_sequence(output_file, config)
    unreal.log(str(result))
