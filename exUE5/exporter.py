import os
import json
import unreal


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_current_sequence():
    try:
        return unreal.LevelSequenceEditorBlueprintLibrary.get_current_level_sequence()
    except Exception:
        return None


def get_world():
    try:
        return unreal.EditorLevelLibrary.get_editor_world()
    except Exception:
        return None


def collect_all_bindings(sequence):
    if not sequence:
        return []
    try:
        return list(sequence.get_bindings())
    except Exception:
        return []


def collect_all_tracks(sequence):
    if not sequence:
        return []
    try:
        return list(sequence.get_all_tracks())
    except Exception:
        return []


def build_export_params(sequence, output_path, config=None):
    if config is None:
        config = {}

    params = unreal.SequencerExportFBXParams()
    params.sequence = sequence
    params.root_sequence = sequence
    params.world = get_world()
    params.fbx_file_name = output_path

    bindings = collect_all_bindings(sequence)
    tracks = collect_all_tracks(sequence)

    params.bindings = bindings
    params.tracks = tracks

    return params


def export_current_sequence(output_path=None, config=None):
    if config is None:
        config = load_config()

    if not output_path:
        output_dir = config.get("default_output_folder", "D:/Exports")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "exported_sequence.fbx")

    sequence = get_current_sequence()
    if not sequence:
        raise RuntimeError("Brak aktualnie otwartego Level Sequence.")

    world = get_world()
    if not world:
        raise RuntimeError("Brak aktywnego World/Level.")

    params = build_export_params(sequence, output_path, config)

    try:
        success = unreal.SequencerTools.export_level_sequence_fbx(params)
    except Exception as exc:
        raise RuntimeError(f"Błąd wywołania eksportu: {exc}") from exc

    if not success:
        raise RuntimeError("Eksport FBX zakończył się niepowodzeniem.")

    return {
        "success": True,
        "sequence": sequence.get_name(),
        "output_path": output_path,
        "world": world.get_name() if hasattr(world, "get_name") else None,
    }
