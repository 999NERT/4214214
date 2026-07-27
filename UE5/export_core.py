import json
import os
import unreal

from .metahuman_export import describe_metahuman, is_metahuman_actor


def load_reference_data(path: str) -> dict:
    """Load JSON reference data used for MetaHuman manifest entries."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_bindings_to_export(sequence: unreal.LevelSequence) -> list:
    """Return selected bindings or all bindings if none are selected."""
    selected = unreal.LevelSequenceEditorBlueprintLibrary.get_selected_bindings(sequence)
    if selected:
        return selected
    return sequence.get_bindings()


def get_sequence_frame_range(sequence: unreal.LevelSequence) -> tuple[int, int]:
    """Return the playback frame range for the sequence."""
    frame_start = getattr(sequence, "get_playback_start", lambda: 0)()
    frame_end = getattr(sequence, "get_playback_end", lambda: 0)()
    return int(frame_start), int(frame_end)


def get_sequence_frame_rate_components(sequence: unreal.LevelSequence) -> tuple[int, int]:
    """Return the numerator and denominator for the sequence display rate."""
    rate = getattr(sequence, "get_display_rate", lambda: 30)()
    if hasattr(rate, "numerator") and hasattr(rate, "denominator"):
        numerator = int(rate.numerator)
        denominator = int(rate.denominator) if int(rate.denominator) != 0 else 1
        return numerator, denominator
    if isinstance(rate, float):
        return int(rate), 1
    return int(rate), 1


def get_sequence_frame_rate(sequence: unreal.LevelSequence) -> float:
    """Return the display rate as a float for convenience."""
    numerator, denominator = get_sequence_frame_rate_components(sequence)
    return float(numerator) / float(denominator)


def export_to_usd(world: unreal.World,
                  sequence: unreal.LevelSequence,
                  output_dir: str,
                  export_level: bool = True,
                  export_subsequences_as_layers: bool = True,
                  start_frame: int = None,
                  end_frame: int = None) -> str:
    """Export the sequence to USD and return the generated file path."""
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    usd_path = os.path.join(output_dir, "scene.usd")
    options = unreal.LevelSequenceExporterUsdOptions()
    options.export_level = export_level
    options.export_subsequences_as_layers = export_subsequences_as_layers
    if start_frame is not None and end_frame is not None:
        options.override_export_range = True
        options.start_frame = start_frame
        options.end_frame = end_frame
    export_fn = getattr(unreal.SequencerTools, "export_level_sequence_to_usd", None)
    if export_fn is None:
        raise RuntimeError("USD export API not available on this Unreal build.")
    export_fn(world, sequence, usd_path, options)
    return usd_path


def export_fallback_fbx(world: unreal.World,
                         sequence: unreal.LevelSequence,
                         output_dir: str) -> str:
    """Export the sequence to FBX as a fallback path."""
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    fbx_path = os.path.join(output_dir, "scene.fbx")
    export_fn = getattr(unreal.SequencerTools, "export_level_sequence_fbx", None)
    if export_fn is None:
        raise RuntimeError("FBX export API not available on this Unreal build.")
    export_fn(world, sequence, fbx_path)
    return fbx_path


def _build_binding_summary(binding: unreal.MovieSceneBinding) -> dict:
    """Return a small metadata summary for a Sequencer binding."""
    summary = {
        "name": binding.get_name(),
        "binding_id": str(binding.get_id()) if hasattr(binding, "get_id") else None,
    }
    if hasattr(binding, "get_display_name"):
        summary["display_name"] = binding.get_display_name()
    return summary


def _resolve_binding_name(sequence: unreal.LevelSequence, binding_id) -> str | None:
    for binding in sequence.get_bindings():
        if hasattr(binding, "get_id") and str(binding.get_id()) == str(binding_id):
            return binding.get_name()
    return None


def collect_camera_cuts(sequence: unreal.LevelSequence) -> list[dict]:
    movie_scene = sequence.get_movie_scene()
    if not movie_scene:
        return []

    cuts = []
    for track in movie_scene.get_master_tracks():
        if not isinstance(track, unreal.MovieSceneCameraCutTrack):
            continue
        for section in track.get_sections():
            frame = None
            if hasattr(section, "get_start_frame"):
                start_frame = section.get_start_frame()
                frame = int(start_frame.value) if hasattr(start_frame, "value") else int(start_frame)

            camera_name = None
            if hasattr(section, "get_camera_binding_id"):
                camera_name = _resolve_binding_name(sequence, section.get_camera_binding_id())
            cuts.append({
                "frame": frame,
                "camera_name": camera_name,
            })
    return cuts


def build_manifest(sequence: unreal.LevelSequence,
                   bindings: list,
                   level_path: str,
                   output_dir: str,
                   frame_rate: float,
                   frame_rate_numerator: int,
                   frame_rate_denominator: int,
                   frame_start: int,
                   frame_end: int,
                   reference_data_path: str = None) -> dict:
    """Build a manifest dictionary for the exported scene."""
    reference_data = load_reference_data(reference_data_path)
    bound_metadata = [_build_binding_summary(binding) for binding in bindings]
    manifest = {
        "schema_version": "1.0",
        "sequence_name": sequence.get_name(),
        "level_path": level_path,
        "output_dir": output_dir,
        "frame_rate": frame_rate,
        "frame_rate_numerator": frame_rate_numerator,
        "frame_rate_denominator": frame_rate_denominator,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "bindings": bound_metadata,
        "exporter": "UE5 Level Sequence USD Export Tool",
        "usd_file": os.path.join(output_dir, "scene.usd"),
        "camera_cuts": collect_camera_cuts(sequence),
        "meta": {
            "has_reference_data": bool(reference_data),
            "reference_data_file": os.path.basename(reference_data_path) if reference_data_path else None,
        },
    }

    actors = []
    world = unreal.EditorLevelLibrary.get_editor_world()
    for actor in world.get_actors():
        if is_metahuman_actor(actor):
            actors.append(describe_metahuman(actor, sequence, reference_data))
    if actors:
        manifest["actors"] = actors
    return manifest


def save_manifest(manifest: dict, output_dir: str) -> str:
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
    return path


def export_sequence(sequence: unreal.LevelSequence,
                    output_dir: str,
                    export_level: bool = True,
                    export_subsequences_as_layers: bool = True,
                    reference_data_path: str = None) -> dict:
    """Export a UE5 sequence and write a manifest for Blender import."""
    world = unreal.EditorLevelLibrary.get_editor_world()
    bindings = get_bindings_to_export(sequence)
    frame_start, frame_end = get_sequence_frame_range(sequence)
    frame_rate_numerator, frame_rate_denominator = get_sequence_frame_rate_components(sequence)
    frame_rate = float(frame_rate_numerator) / float(frame_rate_denominator)
    usd_path = export_to_usd(
        world,
        sequence,
        output_dir,
        export_level=export_level,
        export_subsequences_as_layers=export_subsequences_as_layers,
        start_frame=frame_start,
        end_frame=frame_end,
    )
    manifest = build_manifest(
        sequence,
        bindings,
        world.get_path_name() if world else "",
        output_dir,
        frame_rate,
        frame_rate_numerator,
        frame_rate_denominator,
        frame_start,
        frame_end,
        reference_data_path=reference_data_path,
    )
    save_manifest(manifest, output_dir)
    return {
        "usd_path": usd_path,
        "manifest": manifest,
    }
