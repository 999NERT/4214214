import os
import json
import threading
import traceback

try:
    import unreal
except ModuleNotFoundError:
    unreal = None


def _log(message):
    thread_name = threading.current_thread().name
    formatted = f"[exUE5][{thread_name}] {message}"
    if unreal is not None:
        try:
            unreal.log(formatted)
            return
        except Exception:
            pass
    print(formatted)


def load_config(config_path=None):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _try_call(obj, method_names, *args, **kwargs):
    for method_name in method_names:
        method = getattr(obj, method_name, None)
        if not callable(method):
            continue
        try:
            result = method(*args, **kwargs)
            _log(f"_try_call {obj.__class__.__name__}.{method_name} -> {result}")
            return result
        except Exception as exc:
            _log(f"_try_call {obj.__class__.__name__}.{method_name} failed: {exc}")
    return None


def _is_level_sequence_object(obj):
    if not obj:
        return False

    try:
        if hasattr(unreal, 'LevelSequence') and isinstance(obj, unreal.LevelSequence):
            return True
    except Exception:
        pass

    try:
        if hasattr(unreal, 'MovieSceneSequence') and isinstance(obj, unreal.MovieSceneSequence):
            return True
    except Exception:
        pass

    try:
        if hasattr(obj, 'get_class') and callable(getattr(obj, 'get_class')):
            class_name = obj.get_class().get_name()
            if class_name and 'Sequence' in class_name:
                return True
    except Exception:
        pass

    try:
        if hasattr(obj, 'asset_class'):
            return 'LevelSequence' in str(obj.asset_class) or 'MovieSceneSequence' in str(obj.asset_class)
    except Exception:
        pass

    try:
        if hasattr(obj, 'get_tag_value'):
            tag_value = obj.get_tag_value('AssetClass')
            if tag_value and ('LevelSequence' in str(tag_value) or 'MovieSceneSequence' in str(tag_value)):
                return True
    except Exception:
        pass

    try:
        if hasattr(obj, 'get_path_name') and callable(obj.get_path_name):
            path_name = obj.get_path_name()
            if path_name and ('LevelSequence' in str(path_name) or 'MovieSceneSequence' in str(path_name)):
                return True
    except Exception:
        pass

    try:
        if hasattr(obj, 'get_editor_property'):
            asset_class = obj.get_editor_property('asset_class')
            if asset_class and ('LevelSequence' in str(asset_class) or 'MovieSceneSequence' in str(asset_class)):
                return True
    except Exception:
        pass

    return False


def _find_sequence_in_container(container):
    if not container:
        return None

    if _is_level_sequence_object(container):
        return container

    if isinstance(container, dict):
        for value in container.values():
            sequence = _find_sequence_in_container(value)
            if sequence:
                return sequence
        return None

    if isinstance(container, (list, tuple, set)):
        for item in container:
            sequence = _find_sequence_in_container(item)
            if sequence:
                return sequence
        return None

    try:
        for attribute_name in ('asset', 'asset_data', 'sequence', 'root_sequence', 'parent_sequence', 'movie_scene_sequence'):
            if hasattr(container, 'get_editor_property'):
                try:
                    value = container.get_editor_property(attribute_name)
                    sequence = _find_sequence_in_container(value)
                    if sequence:
                        return sequence
                except Exception:
                    continue
    except Exception:
        pass

    return None


def _get_current_sequence_from_open_assets():
    try:
        if hasattr(unreal, 'AssetEditorSubsystem'):
            asset_subsystem = unreal.AssetEditorSubsystem()
            assets = _try_call(asset_subsystem, [
                'get_all_editor_assets',
                'get_open_editor_assets',
                'get_editor_assets',
                'get_all_editor_asset',
            ])
            sequence = _find_sequence_in_container(assets)
            if sequence:
                _log(f"get_current_sequence fallback open asset -> {sequence}")
                return sequence
    except Exception as exc:
        _log(f"get_current_sequence open asset fallback ERROR: {exc}")
    _log("get_current_sequence fallback open assets -> no LevelSequence found")
    return None


def _get_current_sequence_from_selected_assets():
    try:
        if hasattr(unreal, 'EditorUtilitySubsystem'):
            utility_subsystem = unreal.EditorUtilitySubsystem()
            assets = _try_call(utility_subsystem, [
                'get_selected_assets',
                'get_selected_asset',
                'get_selected_assets_from_content_browser',
            ])
            sequence = _find_sequence_in_container(assets)
            if sequence:
                _log(f"get_current_sequence fallback selected asset -> {sequence}")
                return sequence

        if hasattr(unreal, 'AssetEditorSubsystem'):
            asset_subsystem = unreal.AssetEditorSubsystem()
            assets = _try_call(asset_subsystem, [
                'get_selected_assets',
                'get_selected_asset',
            ])
            sequence = _find_sequence_in_container(assets)
            if sequence:
                _log(f"get_current_sequence fallback selected asset (AssetEditorSubsystem) -> {sequence}")
                return sequence

        if hasattr(unreal, 'EditorAssetLibrary'):
            assets = _try_call(unreal.EditorAssetLibrary, [
                'get_selected_assets',
                'get_selected_asset',
            ])
            sequence = _find_sequence_in_container(assets)
            if sequence:
                _log(f"get_current_sequence fallback selected asset (EditorAssetLibrary) -> {sequence}")
                return sequence
    except Exception as exc:
        _log(f"get_current_sequence selected asset fallback ERROR: {exc}")
    _log("get_current_sequence fallback selected assets -> no LevelSequence found")
    return None


def _get_current_sequence_from_actors():
    try:
        if hasattr(unreal, 'LevelSequenceActor') and hasattr(unreal, 'GameplayStatics'):
            world = get_world()
            if world:
                actors = _try_call(unreal.GameplayStatics, ['get_all_actors_of_class', 'get_all_actors_of_class'], world, unreal.LevelSequenceActor)
                if actors:
                    for actor in actors:
                        sequence = None
                        if hasattr(actor, 'get_sequence'):
                            sequence = actor.get_sequence()
                        elif hasattr(actor, 'sequence'):
                            try:
                                sequence = actor.sequence
                            except Exception:
                                sequence = None
                        if _is_level_sequence_object(sequence):
                            _log(f"get_current_sequence fallback actor -> {sequence}")
                            return sequence
    except Exception as exc:
        _log(f"get_current_sequence actor fallback ERROR: {exc}")
    _log("get_current_sequence fallback actors -> no sequence found")
    return None


def _get_current_sequence_from_sequence_editor():
    try:
        if hasattr(unreal, 'LevelSequenceEditorBlueprintLibrary'):
            sequence = _try_call(unreal.LevelSequenceEditorBlueprintLibrary, [
                'get_current_level_sequence',
                'get_current_sequence',
                'get_current_sequence_asset',
                'get_active_sequence',
            ])
            if sequence and _is_level_sequence_object(sequence):
                _log(f"get_current_sequence via LevelSequenceEditorBlueprintLibrary active -> {sequence}")
                return sequence
    except Exception as exc:
        _log(f"get_current_sequence sequence editor fallback ERROR: {exc}")
    return None


def _get_current_sequence_from_sequencer_subsystems():
    try:
        candidates = [
            ('SequencerTools.get_current_level_sequence', unreal.SequencerTools if hasattr(unreal, 'SequencerTools') else None, ['get_current_level_sequence', 'get_current_sequence', 'get_active_sequence']),
        ]
        for label, module, methods in candidates:
            if module is None:
                continue
            sequence = _try_call(module, methods)
            if sequence and _is_level_sequence_object(sequence):
                _log(f"get_current_sequence via {label} -> {sequence}")
                return sequence
    except Exception as exc:
        _log(f"get_current_sequence sequencer subsystem fallback ERROR: {exc}")
    return None


def get_current_sequence():
    try:
        sequence = _get_current_sequence_from_sequence_editor()
        if sequence:
            _log(f"get_current_sequence -> {sequence}")
            return sequence

        sequence = _get_current_sequence_from_sequencer_subsystems()
        if sequence:
            _log(f"get_current_sequence -> {sequence}")
            return sequence
    except Exception as exc:
        _log(f"get_current_sequence ERROR: {exc}")

    sequence = _get_current_sequence_from_open_assets()
    if sequence:
        _log("get_current_sequence -> found sequence via open assets")
        return sequence

    sequence = _get_current_sequence_from_selected_assets()
    if sequence:
        _log("get_current_sequence -> found sequence via selected assets")
        return sequence

    sequence = _get_current_sequence_from_actors()
    if sequence:
        _log("get_current_sequence -> found sequence via LevelSequenceActor")
        return sequence

    _log("get_current_sequence -> no current sequence found")
    return None


def get_world():
    try:
        subsystem = unreal.UnrealEditorSubsystem()
        if subsystem and hasattr(subsystem, "get_editor_world"):
            world = subsystem.get_editor_world()
            if world:
                _log(f"get_world -> {world}")
                return world
    except Exception as exc:
        _log(f"get_world via UnrealEditorSubsystem ERROR: {exc}")

    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        _log(f"get_world -> {world}")
        return world
    except Exception as exc:
        _log(f"get_world ERROR: {exc}")
        return None


def collect_all_bindings(sequence):
    if not sequence:
        _log("collect_all_bindings -> no sequence")
        return []
    try:
        bindings = list(sequence.get_bindings())
        _log(f"collect_all_bindings -> count={len(bindings)}")
        return bindings
    except Exception as exc:
        _log(f"collect_all_bindings ERROR: {exc}")
        return []


def collect_all_tracks(sequence):
    """Collect tracks for export.

    get_all_tracks() maps to the deprecated GetMasterTracks, which only
    returns master/top-level tracks (Camera Cut, Audio, Subscenes) -- NOT
    the Skeletal Animation / Control Rig tracks attached to individual
    bindings (e.g. a MetaHuman's body/face animation). Those come back via
    collect_all_bindings() + each binding's own tracks instead, so
    get_all_tracks()/get_tracks() being small/empty for a character-heavy
    sequence is expected, not necessarily a bug.

    Verified against Epic's official Python API docs: get_tracks() is the
    current, non-deprecated method. Real-world testing on UE 5.8.1 showed
    get_all_tracks() has been fully REMOVED on this engine version (not
    just deprecated) -- calling it raises AttributeError. Rather than
    trusting a single hasattr() check (which should be reliable, but this
    project has already been burned once by an engine-version assumption
    that didn't hold), this tries each candidate name defensively and never
    raises -- it logs exactly which one worked, or that none did.
    """
    if not sequence:
        _log("collect_all_tracks -> no sequence")
        return []

    for method_name in ("get_tracks", "get_master_tracks", "get_all_tracks"):
        method = getattr(sequence, method_name, None)
        if not callable(method):
            continue
        try:
            tracks = list(method())
            _log(f"collect_all_tracks -> using {method_name}(), count={len(tracks)}")
            return tracks
        except Exception as exc:
            _log(f"collect_all_tracks -> {method_name}() failed: {exc}")

    _log(
        "collect_all_tracks -> no working get_tracks()/get_master_tracks()/"
        "get_all_tracks() method found on this sequence/engine build -- "
        "master tracks (e.g. Camera Cut Track) will NOT be included in the "
        "export. This does not affect bindings/body/camera animation "
        "themselves, but may affect anything that depends on the Camera "
        "Cut track specifically."
    )
    return []


def _get_display_name(item):
    for attr_name in ("get_name", "get_display_name", "get_object_name", "get_path_name"):
        method = getattr(item, attr_name, None)
        if callable(method):
            try:
                value = method()
            except Exception:
                continue
            if value:
                return str(value)
    return str(item)


def _filter_sequence_items(items, config):
    items = list(items)
    total = len(items)

    if config.get("include_all_bindings", True):
        _log(f"_filter_sequence_items -> include_all_bindings=True, keeping all {total} item(s)")
        return items

    keywords = []
    if config.get("include_body", False):
        keywords.extend(["body", "bone", "skeleton", "metahuman"])
    if config.get("include_face", False):
        keywords.extend(["face", "blendshape", "morph"])
    if config.get("include_cameras", False):
        keywords.extend(["camera", "cam"])
    if config.get("include_control_rigs", False):
        keywords.extend(["controlrig", "control rig", "rig"])
    if config.get("include_subsequences", False):
        keywords.extend(["sequence", "subsequence"])

    if not keywords:
        _log(f"_filter_sequence_items -> no include_* flags set, keeping all {total} item(s)")
        return items

    filtered = []
    for item in items:
        name = _get_display_name(item).lower()
        if any(keyword in name for keyword in keywords):
            filtered.append(item)

    _log(f"_filter_sequence_items -> keywords={keywords} before={total} after={len(filtered)}")

    if total and not filtered:
        # KNOWN LIMITATION: real MetaHuman bone/blendshape names (e.g.
        # 'pelvis', 'clavicle_l', 'head_lod0_mesh__brow_down_L') don't
        # contain the keywords above, which are tuned for generic/BP
        # component names (e.g. a 'Body'/'Face' component on a MetaHuman
        # Blueprint actor). If this fires, the filter almost certainly
        # zeroed out real content -- verify by name against your actual
        # sequence and extend `keywords` above rather than shipping an
        # incomplete FBX silently.
        _log(
            "WARNING: filter matched 0 of {} item(s) for keywords {} -- this "
            "config combination would export an EMPTY/INCOMPLETE FBX. Check "
            "whether the real binding/track names actually contain these "
            "keywords, or set include_all_bindings=true.".format(total, keywords)
        )

    return filtered


def _get_spawnable_binding_ids(sequence):
    """Return the set of binding IDs (as strings) that are Spawnables in this sequence.

    Uses unreal.MovieSceneSequence.get_spawnables(), verified against
    Epic's official Python API docs. Always logs its outcome -- including
    when it finds zero spawnables or when the method isn't available on
    this engine build -- so a silent "no warning fired" result in the log
    can be told apart from "the check for spawnables never actually ran."
    """
    spawnable_ids = set()
    if not sequence:
        return spawnable_ids
    if not hasattr(sequence, "get_spawnables"):
        _log(
            "_get_spawnable_binding_ids -> sequence has no get_spawnables() "
            "on this engine build; cannot check for the known Spawnable "
            "camera/mesh export bug on this run."
        )
        return spawnable_ids
    try:
        spawnables = list(sequence.get_spawnables())
        for spawnable in spawnables:
            binding_id = getattr(spawnable, "binding_id", None)
            if binding_id is not None:
                spawnable_ids.add(str(binding_id))
        _log(
            f"_get_spawnable_binding_ids -> found {len(spawnables)} "
            f"spawnable(s) in sequence, {len(spawnable_ids)} with a usable binding_id"
        )
    except Exception as exc:
        _log(f"_get_spawnable_binding_ids ERROR: {exc}")
    return spawnable_ids


def _warn_about_spawnable_export_bug(sequence, bindings):
    """Known engine bug (UE 5.8 / 5.8.1, regression from 5.7):

    unreal.SequencerTools.export_level_sequence_fbx() run from Python writes
    every Spawnable binding as a bare/empty transform node (no mesh, no camera
    data) when the binding's Spawn track has no toggling keys. Possessables are
    unaffected. Confirmed NOT fixed in the 5.8.1 hotfix notes (checked
    28.07.2026 - no matching entry under Sequencer/Cinematics fixes).

    We can't reliably patch the Spawn track's keyframes from Python without
    guessing undocumented low-level Sequencer scripting calls, so instead we
    detect and warn loudly, and recommend converting the binding to a
    Possessable in the Sequencer (RMB on the track -> "Convert to
    Possessable"), which is the reliable fix.
    """
    spawnable_ids = _get_spawnable_binding_ids(sequence)
    if not spawnable_ids:
        return []

    flagged = []
    for binding in bindings:
        binding_id = getattr(binding, "binding_id", None)
        if binding_id is not None and str(binding_id) in spawnable_ids:
            name = _get_display_name(binding)
            flagged.append(name)
            _log(
                f"WARNING: binding '{name}' is a Spawnable. Known UE5.8/5.8.1 bug: "
                "SequencerTools.export_level_sequence_fbx() may export it as an "
                "empty transform with no mesh/camera data. Fix: RMB on the track "
                "in Sequencer -> 'Convert to Possessable', then re-export."
            )
    if flagged:
        _log(
            f"EXPORT WARNING: {len(flagged)} spawnable binding(s) detected "
            f"({', '.join(flagged)}) - verify the exported FBX contains their "
            "mesh/camera data, not just an empty transform."
        )
    else:
        _log(
            f"_warn_about_spawnable_export_bug -> sequence has {len(spawnable_ids)} "
            "spawnable(s), but none of them matched a binding in this export "
            "(they may be filtered out, or binding_id comparison didn't match)."
        )
    return flagged


def build_output_path(config=None, filename=None, folder=None):
    if config is None:
        config = {}

    output_dir = folder or config.get("default_output_folder") or os.path.join(os.path.expanduser("~"), "Exports")
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        filename = config.get("default_output_filename", "exported_sequence.fbx")

    if not filename.lower().endswith(".fbx"):
        filename = f"{filename}.fbx"

    return os.path.join(output_dir, filename)


def _prompt_for_output_path(default_dir):
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.asksaveasfilename(
            title="Wybierz miejsce zapisu FBX",
            initialdir=default_dir,
            initialfile="exported_sequence.fbx",
            defaultextension=".fbx",
            filetypes=[("FBX files", "*.fbx")],
        )
        root.destroy()
        return path or None
    except Exception as exc:
        _log(f"save dialog ERROR: {exc}")
        return None


def _resolve_output_path(output_path, config=None):
    if output_path:
        return output_path

    if config is None:
        config = {}

    output_dir = config.get("default_output_folder") or os.path.join(os.path.expanduser("~"), "Exports")
    os.makedirs(output_dir, exist_ok=True)

    if config.get("show_save_dialog", True):
        dialog_path = _prompt_for_output_path(output_dir)
        if dialog_path:
            return dialog_path

    filename = config.get("default_output_filename", "exported_sequence.fbx")
    return build_output_path(config=config, filename=filename, folder=output_dir)


def _make_frame_time(frame: int):
    if hasattr(unreal, 'FrameNumber'):
        try:
            return unreal.FrameNumber(frame)
        except Exception:
            pass
    if hasattr(unreal, 'FrameTime'):
        try:
            return unreal.FrameTime(frame)
        except Exception:
            pass
    return frame


def _save_sequence_playhead(sequence):
    if not sequence:
        return None

    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, 'get_current_time'):
        try:
            current = unreal.LevelSequenceEditorBlueprintLibrary.get_current_time(sequence)
            _log(f"Saved current sequence time: {current}")
            return current
        except Exception as exc:
            _log(f"get_current_time failed: {exc}")

    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, 'get_current_frame'):
        try:
            current = unreal.LevelSequenceEditorBlueprintLibrary.get_current_frame(sequence)
            _log(f"Saved current sequence frame: {current}")
            return current
        except Exception as exc:
            _log(f"get_current_frame failed: {exc}")

    return None


def _restore_sequence_playhead(sequence, saved_time):
    if not sequence or saved_time is None:
        return False

    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, 'set_current_time'):
        try:
            unreal.LevelSequenceEditorBlueprintLibrary.set_current_time(sequence, saved_time)
            _log(f"Restored sequence time: {saved_time}")
            return True
        except Exception as exc:
            _log(f"set_current_time failed: {exc}")

    if hasattr(unreal.LevelSequenceEditorBlueprintLibrary, 'set_current_frame'):
        try:
            if hasattr(saved_time, 'frame_number'):
                frame = int(saved_time.frame_number)
            else:
                frame = int(saved_time)
            unreal.LevelSequenceEditorBlueprintLibrary.set_current_frame(sequence, _make_frame_time(frame))
            _log(f"Restored sequence frame: {frame}")
            return True
        except Exception as exc:
            _log(f"set_current_frame failed: {exc}")
    return False


def build_export_params(sequence, output_path, config=None):
    if config is None:
        config = {}

    _log(f"build_export_params -> output_path={output_path}")
    _log(f"build_export_params -> config={config}")

    params = unreal.SequencerExportFBXParams()
    params.sequence = sequence
    params.root_sequence = sequence
    params.world = get_world()
    params.fbx_file_name = output_path

    bindings = _filter_sequence_items(collect_all_bindings(sequence), config)
    tracks = _filter_sequence_items(collect_all_tracks(sequence), config)

    _warn_about_spawnable_export_bug(sequence, bindings)

    _log(f"build_export_params -> bindings={len(bindings)} tracks={len(tracks)}")
    params.bindings = bindings
    params.tracks = tracks

    return params


def export_current_sequence(output_path=None, config=None):
    if config is None:
        config = load_config()

    _log("=== EXPORT START ===")

    output_path = _resolve_output_path(output_path, config)
    _log(f"output_path={output_path}")

    sequence = get_current_sequence()
    if not sequence:
        _log("EXPORT FAILED: Brak aktualnie otwartego Level Sequence.")
        raise RuntimeError("Brak aktualnie otwartego Level Sequence.")

    world = get_world()
    if not world:
        _log("EXPORT FAILED: Brak aktywnego World/Level.")
        raise RuntimeError("Brak aktywnego World/Level.")

    saved_time = _save_sequence_playhead(sequence)
    params = build_export_params(sequence, output_path, config)

    try:
        _log("Calling unreal.SequencerTools.export_level_sequence_fbx(params)...")
        success = unreal.SequencerTools.export_level_sequence_fbx(params)
        _log(f"export_level_sequence_fbx returned: {success}")
    except Exception as exc:
        _log(f"EXPORT FAILED: {exc}")
        _log(traceback.format_exc())
        raise RuntimeError(f"Błąd wywołania eksportu: {exc}") from exc
    finally:
        if saved_time is not None:
            _restore_sequence_playhead(sequence, saved_time)

    if not success:
        _log("EXPORT FAILED: Eksport FBX zakończył się niepowodzeniem.")
        raise RuntimeError("Eksport FBX zakończył się niepowodzeniem.")

    result = {
        "success": True,
        "sequence": sequence.get_name(),
        "output_path": output_path,
        "world": world.get_name() if hasattr(world, "get_name") else None,
    }
    _log(f"EXPORT SUCCESS: {result}")
    return result
