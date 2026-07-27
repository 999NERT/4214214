import bpy

from .operators import SCENEUE5_OT_import

classes = [SCENEUE5_OT_import]


def menu_func(self, context):
    self.layout.operator(SCENEUE5_OT_import.bl_idname, text="Import UE5 Scene")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
