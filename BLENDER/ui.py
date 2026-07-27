import bpy

from .operators import SCENEUE5_OT_import
from .metahuman_merge import import_usd_actor_metadata, apply_metahuman_merge


class UE5_IMPORT_PT_metahuman(bpy.types.Panel):
    bl_label = "UE5 USD Import"
    bl_idname = "UE5_IMPORT_PT_metahuman"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "USD Import"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "ue5_usd_import_path")
        layout.prop(scene, "ue5_usd_fallback_to_fbx")
        layout.prop(scene, "ue5_usd_create_collection")
        layout.prop(scene, "ue5_usd_apply_metahuman_merge")
        layout.operator(SCENEUE5_OT_import.bl_idname, text="Import UE5 USD")


def register():
    bpy.utils.register_class(UE5_IMPORT_PT_metahuman)
    bpy.types.Scene.ue5_usd_import_path = bpy.props.StringProperty(
        name="USD or Manifest Path",
        description="Path to exported USD or manifest JSON file from UE5.",
        subtype="FILE_PATH",
    )
    bpy.types.Scene.ue5_usd_fallback_to_fbx = bpy.props.BoolProperty(
        name="Fallback to FBX",
        description="Use FBX import when USD import is unavailable or fails.",
        default=True,
    )
    bpy.types.Scene.ue5_usd_create_collection = bpy.props.BoolProperty(
        name="Create New Collection",
        description="Create a dedicated collection for imported UE5 objects.",
        default=True,
    )
    bpy.types.Scene.ue5_usd_apply_metahuman_merge = bpy.props.BoolProperty(
        name="Apply MetaHuman Merge",
        description="Create merge collections for MetaHuman body/face metadata after import.",
        default=True,
    )


def unregister():
    bpy.utils.unregister_class(UE5_IMPORT_PT_metahuman)
    del bpy.types.Scene.ue5_usd_import_path
    del bpy.types.Scene.ue5_usd_fallback_to_fbx
    del bpy.types.Scene.ue5_usd_create_collection
    del bpy.types.Scene.ue5_usd_apply_metahuman_merge
