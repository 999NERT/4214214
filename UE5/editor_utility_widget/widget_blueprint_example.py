import os
import unreal

from ..editor_utility_widget.exporter_ui import (
    get_all_level_sequences,
    get_all_maps,
    get_sequence_bindings,
    get_sequence_summary,
    run_export,
)


def widget_get_level_sequences():
    return get_all_level_sequences()


def widget_get_maps():
    return get_all_maps()


def widget_get_sequence_summary(sequence_path: str):
    return get_sequence_summary(sequence_path)


def widget_get_sequence_bindings(sequence_path: str):
    return get_sequence_bindings(sequence_path)


def widget_run_export(sequence_path: str,
                      output_dir: str,
                      selected_binding_ids: list[str] | None = None,
                      level_map_path: str | None = None,
                      reference_data_paths=None,
                      export_level=True,
                      export_subsequences_as_layers=True):
    os.makedirs(os.path.abspath(output_dir), exist_ok=True)
    result = run_export(
        sequence_path,
        output_dir,
        selected_binding_ids=selected_binding_ids,
        level_map_path=level_map_path,
        reference_data_paths=reference_data_paths,
        export_level=export_level,
        export_subsequences_as_layers=export_subsequences_as_layers,
    )
    if result is None:
        unreal.log_error(f"Widget export failed for sequence: {sequence_path}")
    return result
