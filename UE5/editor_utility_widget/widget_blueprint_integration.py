import os
import unreal

from ..export_core import export_sequence


# UI helper functions for Editor Utility Widget blueprint integration.
# Use these from a UMG/Editor Utility Widget blueprint to populate pickers and run export.

def list_level_sequences() -> list[dict]:
    """Return Level Sequence assets available in the project."""
    return get_all_level_sequences()


def list_maps() -> list[dict]:
    """Return World/Level assets available in the project."""
    return get_all_maps()


def get_all_level_sequences() -> list[dict]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class("LevelSequence", True)
    sequences = []
    for asset in assets:
        sequences.append({
            "name": asset.asset_name,
            "path": str(asset.object_path),
            "package_name": asset.package_name,
        })
    return sequences


def get_all_maps() -> list[dict]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_class("World", True)
    maps = []
    for asset in assets:
        maps.append({
            "name": asset.asset_name,
            "path": str(asset.object_path),
            "package_name": asset.package_name,
        })
    return maps


def get_sequence_summary(sequence_path: str) -> dict | None:
    """Return frame range, FPS and bindings metadata for the selected sequence."""
    sequence = unreal.load_asset(sequence_path)
    if not sequence or not isinstance(sequence, unreal.LevelSequence):
        return None
    frame_start, frame_end = sequence.get_playback_start(), sequence.get_playback_end()
    numerator, denominator = (0, 1)
    display_rate = getattr(sequence, "get_display_rate", lambda: 30)()
    if hasattr(display_rate, "numerator") and hasattr(display_rate, "denominator"):
        numerator = int(display_rate.numerator)
        denominator = int(display_rate.denominator) if int(display_rate.denominator) else 1
    elif isinstance(display_rate, float):
        numerator, denominator = int(display_rate), 1
    return {
        "name": sequence.get_name(),
        "path": sequence_path,
        "frame_start": int(frame_start),
        "frame_end": int(frame_end),
        "frame_rate_numerator": numerator,
        "frame_rate_denominator": denominator,
        "bindings": get_sequence_bindings(sequence_path),
    }


def get_sequence_bindings(sequence_path: str) -> list[dict]:
    sequence = unreal.load_asset(sequence_path)
    if not sequence or not isinstance(sequence, unreal.LevelSequence):
        return []
    bindings = []
    for binding in sequence.get_bindings():
        binding_id = str(binding.get_id()) if hasattr(binding, "get_id") else None
        display_name = binding.get_display_name() if hasattr(binding, "get_display_name") else None
        track_count = len(binding.get_tracks()) if hasattr(binding, "get_tracks") else None
        bindings.append({
            "id": binding_id,
            "name": binding.get_name() if hasattr(binding, "get_name") else None,
            "display_name": display_name,
            "track_count": track_count,
        })
    return bindings


def run_export_widget(sequence_path: str,
                      output_dir: str,
                      selected_binding_ids: list[str] | None = None,
                      level_map_path: str | None = None,
                      reference_data_paths=None,
                      export_level=True,
                      export_subsequences_as_layers=True) -> dict | None:
    os.makedirs(os.path.abspath(output_dir), exist_ok=True)
    return export_sequence(
        unreal.load_asset(sequence_path),
        output_dir,
        export_level=export_level,
        export_subsequences_as_layers=export_subsequences_as_layers,
        reference_data_paths=reference_data_paths,
        selected_binding_ids=selected_binding_ids,
        level_map_path=level_map_path,
        blendshape_curve_output_path=output_dir,
    )
