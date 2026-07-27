bl_info = {
    "name": "UE5 USD Importer",
    "author": "PLUGSY_DO_3D",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "File > Import",
    "description": "Import UE5 exported USD scenes into Blender and apply MetaHuman merge metadata.",
    "category": "Import-Export",
}

import bpy

from .operators import SCENEUE5_OT_import
from . import ui

classes = [SCENEUE5_OT_import]


def menu_func(self, context):
    self.layout.operator(SCENEUE5_OT_import.bl_idname, text="Import UE5 Scene")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    ui.register()
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)
    ui.unregister()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
