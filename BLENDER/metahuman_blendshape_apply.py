import json
import os

import bpy


def _ensure_shape_key(obj: bpy.types.Object, key_name: str):
    if obj.type != 'MESH':
        return None
    mesh = obj.data
    if mesh.shape_keys is None:
        return None
    return mesh.shape_keys.key_blocks.get(key_name)


def apply_blendshape_curve_data(manifest_folder: str, imported_collection: bpy.types.Collection) -> None:
    curve_file = None
    manifest_path = os.path.join(manifest_folder, "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as handle:
            manifest = json.load(handle)
        curve_file = manifest.get("blendshape_curve_file")
        if curve_file and not os.path.isabs(curve_file):
            curve_file = os.path.join(manifest_folder, curve_file)

    if not curve_file or not os.path.exists(curve_file):
        return

    with open(curve_file, 'r', encoding='utf-8') as handle:
        curve_data = json.load(handle)

    channels = curve_data.get("curve_data", {})
    if not channels:
        return

    frame_start = int(curve_data.get("frame_start", bpy.context.scene.frame_start))
    frame_end = int(curve_data.get("frame_end", bpy.context.scene.frame_end))

    for obj in imported_collection.objects:
        if obj.type != 'MESH':
            continue
        for channel_name, keyframes in channels.items():
            shape_key = _ensure_shape_key(obj, channel_name)
            if not shape_key:
                continue
            for frame_index, value in enumerate(keyframes, start=frame_start):
                try:
                    shape_key.value = float(value)
                    shape_key.keyframe_insert(data_path=f"key_blocks[\"{channel_name}\"].value", frame=frame_index)
                except Exception:
                    continue


def apply_blendshapes_from_manifest(folder: str, imported_collection: bpy.types.Collection) -> None:
    if not os.path.exists(os.path.join(folder, "manifest.json")):
        return
    apply_blendshape_curve_data(folder, imported_collection)
