import bpy
import json
import os

from bpy_extras.io_utils import ImportHelper

from .metahuman_merge import import_usd_actor_metadata, apply_metahuman_merge
from .metahuman_blendshape_apply import apply_blendshapes_from_manifest


def write_debug_import_report(folder: str, manifest: dict, imported_path: str, imported_objects: list[str], settings: dict) -> None:
    report = {
        "manifest_path": os.path.join(folder, "manifest.json"),
        "imported_path": imported_path,
        "imported_objects": imported_objects,
        "settings": settings,
    }
    debug_path = os.path.join(folder, "debug_import.json")
    with open(debug_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)


class SCENEUE5_OT_import(bpy.types.Operator, ImportHelper):
    """Import a UE5 scene folder exported by the UE5 Export Tool."""
    bl_idname = "sceneue5.import"
    bl_label = "Import UE5 Scene"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ""
    filter_folder: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        scene = context.scene
        folder = self.filepath or getattr(scene, "ue5_usd_import_path", "")
        if not folder:
            self.report({'ERROR'}, "No import path provided.")
            return {'CANCELLED'}

        if os.path.isfile(folder):
            folder = os.path.dirname(folder)

        manifest_path = os.path.join(folder, "manifest.json")
        if not os.path.exists(manifest_path):
            self.report({'ERROR'}, "manifest.json not found in selected folder")
            return {'CANCELLED'}

        with open(manifest_path, 'r', encoding='utf-8') as handle:
            manifest = json.load(handle)

        usd_path = os.path.join(folder, "scene.usd")
        fbx_path = os.path.join(folder, "scene.fbx")
        before_objects = set(context.scene.objects)

        imported_path = None
        usd_import_available = hasattr(bpy.ops.wm, "usd_import")
        fbx_import_available = hasattr(bpy.ops.import_scene, "fbx")

        if os.path.exists(usd_path) and usd_import_available:
            try:
                bpy.ops.wm.usd_import(filepath=usd_path)
                imported_path = usd_path
            except Exception as exc:
                usd_import_available = False
                debug_import_error = str(exc)
        if imported_path is None and getattr(scene, "ue5_usd_fallback_to_fbx", True) and os.path.exists(fbx_path) and fbx_import_available:
            try:
                bpy.ops.import_scene.fbx(filepath=fbx_path)
                imported_path = fbx_path
            except Exception as exc:
                fbx_import_available = False
                debug_import_error = str(exc)

        if imported_path is None:
            if os.path.exists(usd_path) and not usd_import_available:
                self.report({'ERROR'}, "USD importer not available in this Blender build.")
            elif os.path.exists(fbx_path) and not fbx_import_available:
                self.report({'ERROR'}, "FBX importer not available in this Blender build.")
            else:
                self.report({'ERROR'}, "Neither scene.usd nor scene.fbx could be imported from selected folder.")
            return {'CANCELLED'}

        after_objects = set(context.scene.objects)
        imported_objects = [obj for obj in after_objects if obj not in before_objects]
        if not imported_objects:
            imported_objects = list(context.selected_objects)
        imported_names = [obj.name for obj in imported_objects]

        fps_numerator = manifest.get("frame_rate_numerator")
        fps_denominator = manifest.get("frame_rate_denominator")
        if fps_numerator is not None and fps_denominator is not None:
            scene.render.fps = int(fps_numerator)
            scene.render.fps_base = float(fps_denominator)
        elif manifest.get("frame_rate") is not None:
            scene.render.fps = int(round(manifest["frame_rate"]))
            scene.render.fps_base = 1.0

        if manifest.get("frame_start") is not None:
            scene.frame_start = int(manifest["frame_start"])
        if manifest.get("frame_end") is not None:
            scene.frame_end = int(manifest["frame_end"])

        collection_name = manifest.get("sequence_name", "UE5 Import")
        if getattr(scene, "ue5_usd_create_collection", True):
            collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
            if collection.name not in [c.name for c in context.scene.collection.children]:
                context.scene.collection.children.link(collection)
            for obj in imported_objects:
                for col in list(obj.users_collection):
                    col.objects.unlink(obj)
                if obj.name not in collection.objects:
                    collection.objects.link(obj)
        else:
            collection = context.scene.collection

        camera_cuts = manifest.get("camera_cuts", [])
        for cut in camera_cuts:
            frame = cut.get("frame")
            camera_name = cut.get("camera_name") or cut.get("name") or "CameraCut"
            if frame is None:
                continue
            marker_name = f"CameraCut_{frame}"
            if marker_name in scene.timeline_markers:
                continue
            marker = scene.timeline_markers.new(marker_name, frame=int(frame))
            if camera_name and camera_name in bpy.data.objects:
                marker.camera = bpy.data.objects[camera_name]

        if getattr(scene, "ue5_usd_apply_metahuman_merge", False):
            import_usd_actor_metadata(manifest, collection)
            apply_metahuman_merge(manifest, collection)
            apply_blendshapes_from_manifest(folder, collection)

        debug_settings = {
            "use_fbx_fallback": getattr(scene, "ue5_usd_fallback_to_fbx", True),
            "create_collection": getattr(scene, "ue5_usd_create_collection", True),
            "apply_metahuman_merge": getattr(scene, "ue5_usd_apply_metahuman_merge", False),
        }
        write_debug_import_report(folder, manifest, imported_path, imported_names, debug_settings)

        self.report({'INFO'}, f"Imported UE5 scene from {os.path.basename(imported_path)}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
