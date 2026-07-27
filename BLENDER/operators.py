import bpy
import json
import os

from bpy_extras.io_utils import ImportHelper


class SCENEUE5_OT_import(bpy.types.Operator, ImportHelper):
    """Import a UE5 scene folder exported by the UE5 Export Tool."""
    bl_idname = "sceneue5.import"
    bl_label = "Import UE5 Scene"
    bl_options = {'REGISTER', 'UNDO'}

    filename_ext = ""
    filter_folder: bpy.props.BoolProperty(default=True)

    def execute(self, context):
        folder = self.filepath
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

        if os.path.exists(usd_path):
            bpy.ops.wm.usd_import(filepath=usd_path)
            imported_path = usd_path
        elif os.path.exists(fbx_path):
            bpy.ops.import_scene.fbx(filepath=fbx_path)
            imported_path = fbx_path
        else:
            self.report({'ERROR'}, "Neither scene.usd nor scene.fbx found in selected folder")
            return {'CANCELLED'}

        scene = context.scene
        if manifest.get("frame_rate") is not None:
            scene.render.fps = int(manifest["frame_rate"])
        if manifest.get("frame_start") is not None:
            scene.frame_start = int(manifest["frame_start"])
        if manifest.get("frame_end") is not None:
            scene.frame_end = int(manifest["frame_end"])

        sequence_name = manifest.get("sequence_name")
        if sequence_name:
            collection = bpy.data.collections.new(sequence_name)
            context.scene.collection.children.link(collection)
            for obj in context.selected_objects:
                if obj.name not in collection.objects:
                    collection.objects.link(obj)

        camera_cuts = manifest.get("camera_cuts", [])
        for cut in camera_cuts:
            frame = cut.get("frame")
            camera_name = cut.get("camera_name") or cut.get("name") or "CameraCut"
            if frame is None:
                continue
            marker = scene.timeline_markers.new(camera_name, frame=int(frame))
            if camera_name and camera_name in bpy.data.objects:
                marker.camera = bpy.data.objects[camera_name]

        self.report({'INFO'}, f"Imported UE5 scene from {os.path.basename(imported_path)}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
