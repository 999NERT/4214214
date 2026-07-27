import json
import os

import unreal


def _load_reference_data(paths):
    if not paths:
        return {}
    if isinstance(paths, str):
        paths = [paths]
    result = {}
    for path in paths:
        if not path or not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as handle:
            try:
                result.update(json.load(handle))
            except Exception:
                continue
    return result


def _flatten_blendshape_names(reference_data: dict) -> list[str]:
    if not reference_data:
        return []
    if "channels_by_group" in reference_data:
        names = []
        for group in reference_data["channels_by_group"].values():
            for entry in group:
                if isinstance(entry, dict) and "name" in entry:
                    names.append(entry["name"])
        return names
    if "channel_names" in reference_data and isinstance(reference_data["channel_names"], list):
        return [str(name) for name in reference_data["channel_names"]]
    return []


def _find_face_component(sequence):
    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        return None, None
    for actor in getattr(world, "get_actors", lambda: [])():
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
            if "face" in component.get_name().lower():
                return actor, component
    return None, None


def _make_frame_time(frame: int):
    if hasattr(unreal, "FrameNumber"):
        try:
            return unreal.FrameNumber(frame)
        except Exception:
            pass
    if hasattr(unreal, "FrameTime"):
        try:
            return unreal.FrameTime(frame)
        except Exception:
            pass
    return frame


def _set_sequence_playhead(sequence, frame):
    target = _make_frame_time(frame)
    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, "set_current_time"):
        try:
            unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(sequence, target)
            return True
        except Exception:
            pass
    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, "set_current_frame"):
        try:
            unreal.LevelSequenceEditorBlueprintLibrary.set_current_frame(sequence, target)
            return True
        except Exception:
            pass
    return False


def _read_morph_target_value(component, channel_name):
    if not component or not channel_name:
        return None
    if hasattr(component, "get_morph_target_curve_value"):
        try:
            return float(component.get_morph_target_curve_value(channel_name))
        except Exception:
            pass

    if hasattr(component, "get_editor_property"):
        for prop_name in ["morph_target_curves", "morph_targets", "morph_target_weights"]:
            try:
                prop_value = component.get_editor_property(prop_name)
            except Exception:
                continue
            if isinstance(prop_value, dict) and channel_name in prop_value:
                try:
                    return float(prop_value[channel_name])
                except Exception:
                    continue
            if isinstance(prop_value, (list, tuple)):
                for item in prop_value:
                    name = getattr(item, "name", None) or getattr(item, "channel_name", None) or str(item)
                    value = getattr(item, "value", None) or getattr(item, "weight", None)
                    if name == channel_name and value is not None:
                        try:
                            return float(value)
                        except Exception:
                            continue
    return None


def export_blendshape_curves(sequence, output_dir, frame_start, frame_end, reference_data_paths=None, output_filename="blendshape_curves.json"):
    """Export face blendshape curve fallback data to JSON."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_filename)

    reference_data = _load_reference_data(reference_data_paths)
    channel_names = _flatten_blendshape_names(reference_data)
    actor, face_component = _find_face_component(sequence)

    if face_component is None:
        result = {
            "sequence_name": sequence.get_name() if hasattr(sequence, "get_name") else None,
            "frame_start": frame_start,
            "frame_end": frame_end,
            "supported": False,
            "message": "Nie znaleziono komponentu Face na MetaHuman actorze.",
            "curve_data": {},
        }
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
        return output_path

    if not channel_names:
        channel_names = []
        if hasattr(face_component, "get_editor_property"):
            try:
                morph_names = face_component.get_editor_property("morph_targets")
                if isinstance(morph_names, (list, tuple)):
                    channel_names = [str(name) for name in morph_names]
            except Exception:
                pass

    curves = {name: [] for name in channel_names}
    missing = []
    supported = bool(channel_names)

    for frame in range(frame_start, frame_end + 1):
        _set_sequence_playhead(sequence, frame)
        for name in channel_names:
            value = _read_morph_target_value(face_component, name)
            if value is None:
                if name not in missing:
                    missing.append(name)
                value = 0.0
            curves[name].append(value)

    result = {
        "sequence_name": sequence.get_name() if hasattr(sequence, "get_name") else None,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "supported": supported,
        "message": None if supported else "Nie zdefiniowano listy kanałów blendshape w danych referencyjnych.",
        "curve_data": curves,
        "missing_channels": missing,
        "reference_data_file": reference_data_paths,
    }

    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
    return output_path
